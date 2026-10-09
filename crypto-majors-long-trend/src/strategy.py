"""Nautilus long-only pullback replay for crypto-major USDT perps."""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Optional

from nautilus_trader.config import StrategyConfig
from nautilus_trader.model.data import Bar, BarType
from nautilus_trader.model.enums import OrderSide, TimeInForce
from nautilus_trader.model.identifiers import InstrumentId
from nautilus_trader.model.instruments import Instrument
from nautilus_trader.model.objects import Price, Quantity
from nautilus_trader.trading.strategy import Strategy

from . import spec
from .risk import HaltState, apply_day_rollover, expected_funding_r, in_funding_blackout, register_realized, size_from_risk
from .signal import evaluate_long

ROUND_TRIPS: list[dict[str, Any]] = []


class CryptoMajorsLongTrendConfig(StrategyConfig):
    instrument_id: Optional[InstrumentId] = None
    bar_type: Optional[BarType] = None
    instrument_ids: tuple[InstrumentId, ...] = ()
    bar_types: tuple[BarType, ...] = ()
    trade_size: str = "0.0001"
    symbol: str = "BTCUSDT"
    adx_period: int = 14
    atr_period: int = 14
    ema_fast_period: int = 21
    ema_slow_period: int = 55
    adx_min: float = 22.0
    atr_pct_lo: float = 25.0
    atr_pct_hi: float = 80.0
    percentile_lookback: int = 168
    stop_atr_mult: float = 1.5
    tp_r_multiple: float = 2.0
    time_stop_hours: int = 8
    limit_ttl_hours: int = 4
    risk_usdt: float = 15.0
    leverage_cap: int = 5
    margin_budget: float = 500.0
    funding_blackout_min: int = 15
    funding_cost_max_r: float = 0.1
    daily_pause_usdt: float = 30.0
    playbook_stop_usdt: float = 40.0
    consecutive_loss_halt: int = 5
    maker_fee: float = 0.0002
    taker_fee: float = 0.0006


class CryptoMajorsLongTrend(Strategy):
    def __init__(self, config: CryptoMajorsLongTrendConfig) -> None:
        super().__init__(config)
        self.cfg = config
        self._highs: list[float] = []
        self._lows: list[float] = []
        self._closes: list[float] = []
        self._instrument: Optional[Instrument] = None
        self._pending_bars = 0
        self._pending_price: Optional[float] = None
        self._pending_stop: Optional[float] = None
        self._entry: Optional[float] = None
        self._stop: Optional[float] = None
        self._tp: Optional[float] = None
        self._bars_held = 0
        self._qty: Optional[Quantity] = None
        self._halt = HaltState()
        self._feature_frames: dict[str, Any] = {}
        ROUND_TRIPS.clear()

    def set_feature_frames(self, feature_frames: dict[str, Any]) -> None:
        self._feature_frames = feature_frames or {}

    def on_start(self) -> None:
        bar_type = self.cfg.bar_type or (self.cfg.bar_types[0] if self.cfg.bar_types else None)
        instrument_id = self.cfg.instrument_id or (
            self.cfg.instrument_ids[0] if self.cfg.instrument_ids else None
        )
        if bar_type is None or instrument_id is None:
            raise RuntimeError("bar_type and instrument_id must be set")
        self._instrument = self.cache.instrument(instrument_id)
        self.subscribe_bars(bar_type)

    def _bar_time(self, bar: Bar) -> datetime:
        ts = getattr(bar.ts_event, "value", None) or getattr(bar, "ts_event", 0)
        try:
            nanos = int(ts)
            if nanos > 10**15:
                return datetime.fromtimestamp(nanos / 1_000_000_000, tz=timezone.utc)
            if nanos > 10**12:
                return datetime.fromtimestamp(nanos / 1_000, tz=timezone.utc)
            return datetime.fromtimestamp(nanos, tz=timezone.utc)
        except Exception:
            return datetime.now(timezone.utc)

    def _funding_rate_at(self, when: datetime) -> float:
        frame = None
        for value in self._feature_frames.values():
            frame = value
            break
        if frame is None:
            return 0.0
        try:
            series = frame["funding_rate"] if "funding_rate" in frame.columns else None
            if series is None:
                return 0.0
            loc = series.index.asof(when)
            value = series.loc[loc]
            return float(value) if value == value else 0.0
        except Exception:
            return 0.0

    def _submit_qty(self, qty_text: str) -> Quantity | None:
        instrument = self._instrument
        if instrument is None:
            return None
        return Quantity(Decimal(qty_text), instrument.size_precision)

    def _price(self, value: float) -> Price:
        instrument = self._instrument
        assert instrument is not None
        return Price(Decimal(str(round(value, instrument.price_precision))), instrument.price_precision)

    def _flat(self) -> bool:
        instrument = self._instrument
        if instrument is None:
            return True
        return not self.cache.positions_open(instrument_id=instrument.id)

    def _cancel_pending_entry(self) -> None:
        instrument = self._instrument
        if instrument is None:
            return
        self.cancel_all_orders(instrument.id)
        self._pending_bars = 0
        self._pending_price = None
        self._pending_stop = None

    def _close_long(self, reason: str, bar: Bar, fill_hint: float) -> None:
        instrument = self._instrument
        if instrument is None:
            return
        self.cancel_all_orders(instrument.id)
        self.close_all_positions(instrument.id)
        entry = self._entry
        stop = self._stop
        if entry is not None and stop is not None and stop != entry:
            r_dist = entry - stop
            pnl_r = (fill_hint - entry) / r_dist if r_dist else 0.0
        else:
            pnl_r = 0.0
        qty = float(self._qty) if self._qty is not None else 0.0
        pnl_usdt = (fill_hint - (entry or fill_hint)) * qty
        fees = abs((entry or 0.0) * qty) * self.cfg.maker_fee + abs(fill_hint * qty) * self.cfg.taker_fee
        funding_rate = self._funding_rate_at(self._bar_time(bar))
        funding = abs(funding_rate) * abs((entry or 0.0) * qty) * max(self._bars_held / 8.0, 0.0)
        net = pnl_usdt - fees - funding
        ROUND_TRIPS.append(
            {
                "time": self._bar_time(bar).isoformat(),
                "symbol": self.cfg.symbol,
                "side": "long",
                "entry": entry,
                "exit": fill_hint,
                "qty": qty,
                "gross_usdt": pnl_usdt,
                "fees_usdt": fees,
                "funding_usdt": funding,
                "net_usdt": net,
                "r": (net / self.cfg.risk_usdt) if self.cfg.risk_usdt else 0.0,
                "pnl_r_price": pnl_r,
                "reason": reason,
                "bars_held": self._bars_held,
            }
        )
        self._halt = register_realized(
            self._halt,
            net,
            self.cfg.daily_pause_usdt,
            self.cfg.playbook_stop_usdt,
        )
        self._entry = None
        self._stop = None
        self._tp = None
        self._bars_held = 0
        self._qty = None

    def on_bar(self, bar: Bar) -> None:
        high = float(bar.high)
        low = float(bar.low)
        close = float(bar.close)
        self._highs.append(high)
        self._lows.append(low)
        self._closes.append(close)
        now = self._bar_time(bar)
        self._halt = apply_day_rollover(self._halt, now)

        instrument = self._instrument
        if instrument is None:
            return

        if not self._flat():
            if self._entry is None and self._pending_price is not None:
                self._entry = self._pending_price
                distance = self._pending_stop or 0.0
                self._stop = self._pending_price - distance
                self._tp = self._pending_price + self.cfg.tp_r_multiple * distance
                self._pending_price = None
                self._pending_stop = None
                self._pending_bars = 0
                self._bars_held = 0
            self._bars_held += 1
            if self._stop is not None and low <= self._stop:
                fill = self._stop - spec.tick_size(self.cfg.symbol)
                self._close_long("STOP", bar, fill)
                return
            if self._tp is not None and high >= self._tp:
                self._close_long("TP_2R", bar, self._tp)
                return
            if self._bars_held >= self.cfg.time_stop_hours:
                fill = close - spec.tick_size(self.cfg.symbol)
                self._close_long("TIME_STOP", bar, fill)
                return
            return

        if self._pending_price is not None:
            self._pending_bars += 1
            if self._pending_bars >= self.cfg.limit_ttl_hours:
                self._cancel_pending_entry()
            return

        if self._halt.halted or self._halt.halt_reason == "HALT_DAILY_PAUSE":
            return
        if self._halt.consecutive_losses >= self.cfg.consecutive_loss_halt:
            self._halt.halted = True
            self._halt.halt_reason = "HALT_CONSEC_LOSS"
            return

        decision = evaluate_long(
            self._highs,
            self._lows,
            self._closes,
            adx_period=self.cfg.adx_period,
            atr_period=self.cfg.atr_period,
            ema_fast_period=self.cfg.ema_fast_period,
            ema_slow_period=self.cfg.ema_slow_period,
            adx_min=self.cfg.adx_min,
            atr_pct_lo=self.cfg.atr_pct_lo,
            atr_pct_hi=self.cfg.atr_pct_hi,
            percentile_lookback=self.cfg.percentile_lookback,
            stop_atr_mult=self.cfg.stop_atr_mult,
        )
        if not decision.valid or decision.limit_price is None or decision.stop_distance is None:
            return

        interval_hours = spec.funding_interval_hours(self.cfg.symbol)
        if in_funding_blackout(
            now,
            None,
            interval_hours,
            self.cfg.funding_blackout_min,
            self.cfg.limit_ttl_hours,
        ):
            return

        sizing = size_from_risk(
            self.cfg.symbol,
            price=decision.limit_price,
            stop_distance=decision.stop_distance,
            risk_usdt=self.cfg.risk_usdt,
            leverage_cap=self.cfg.leverage_cap,
            margin_budget=self.cfg.margin_budget,
        )
        if not sizing.get("sizing_ok"):
            return
        funding_rate = self._funding_rate_at(now)
        funding_r = expected_funding_r(
            funding_rate,
            float(sizing["notional_usdt"]),
            self.cfg.time_stop_hours,
            interval_hours,
            self.cfg.risk_usdt,
        )
        if funding_r > self.cfg.funding_cost_max_r:
            return

        qty = self._submit_qty(str(sizing["qty"]))
        if qty is None:
            return
        limit_px = float(decision.limit_price)
        order = self.order_factory.limit(
            instrument_id=instrument.id,
            order_side=OrderSide.BUY,
            quantity=qty,
            price=self._price(limit_px),
            time_in_force=TimeInForce.GTC,
        )
        self.submit_order(order)
        self._qty = qty
        self._pending_price = limit_px
        self._pending_stop = float(decision.stop_distance)
        self._pending_bars = 0

    def on_stop(self) -> None:
        if self._instrument is not None:
            self.cancel_all_orders(self._instrument.id)
            self.close_all_positions(self._instrument.id)
