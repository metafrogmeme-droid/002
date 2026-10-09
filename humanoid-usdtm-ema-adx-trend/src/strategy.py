"""Nautilus replay strategy for the EMA-ADX long-only trend Playbook."""
import math
from collections import defaultdict, deque
from decimal import Decimal
from typing import Optional

from nautilus_trader.config import StrategyConfig
from nautilus_trader.model.data import Bar, BarType
from nautilus_trader.model.enums import OrderSide, TimeInForce
from nautilus_trader.model.identifiers import InstrumentId
from nautilus_trader.model.instruments import Instrument
from nautilus_trader.model.objects import Price, Quantity
from nautilus_trader.trading.strategy import Strategy

from . import indicators, risk


class EmaAdxTrendStrategyConfig(StrategyConfig):
    instrument_id: Optional[InstrumentId] = None
    bar_type: Optional[BarType] = None
    instrument_ids: tuple[InstrumentId, ...] = ()
    bar_types: tuple[BarType, ...] = ()
    fast_period: int = 12
    slow_period: int = 26
    adx_period: int = 14
    adx_min: float = 25.0
    atr_period: int = 14
    atr_percentile_lookback: int = 500
    atr_pct_lo: float = 20.0
    atr_pct_hi: float = 90.0
    volume_avg_period: int = 20
    volume_mult: float = 1.5
    volume_confirm_bars: int = 4
    risk_usdt: str = "15"
    stop_atr_mult: float = 1.5
    first_tp_r: float = 1.5
    first_tp_fraction: float = 0.5
    trail_atr_mult: float = 1.0
    time_stop_hours: int = 8
    limit_ttl_hours: int = 4
    max_concurrent: int = 3
    maker_fee: float = 0.0002
    taker_fee: float = 0.0006
    slippage_ticks: int = 1


class _Book:
    def __init__(self) -> None:
        self.highs: list[float] = []
        self.lows: list[float] = []
        self.closes: list[float] = []
        self.volumes: list[float] = []
        self.times: list[int] = []
        self.setup_bar: int | None = None
        self.pending: dict[str, float | int] | None = None
        self.pos: dict[str, float | int | bool] | None = None


class EmaAdxTrendStrategy(Strategy):
    def __init__(self, config: EmaAdxTrendStrategyConfig) -> None:
        super().__init__(config)
        self.cfg = config
        self.feature_frames = {}
        self._books: dict[InstrumentId, _Book] = {}
        self._instruments: dict[InstrumentId, Instrument] = {}
        self._bar_to_inst: dict[BarType, InstrumentId] = {}
        self._consec_loss = 0
        self._realized = 0.0
        self._halted = False
        self._funding: dict[str, deque] = defaultdict(deque)

    def set_feature_frames(self, feature_frames) -> None:
        self.feature_frames = feature_frames or {}

    def on_start(self) -> None:
        bar_types = list(self.cfg.bar_types)
        instrument_ids = list(self.cfg.instrument_ids)
        if self.cfg.bar_type is not None and not bar_types:
            bar_types = [self.cfg.bar_type]
        if self.cfg.instrument_id is not None and not instrument_ids:
            instrument_ids = [self.cfg.instrument_id]
        if not bar_types or not instrument_ids:
            raise RuntimeError("bar_type/instrument_id must be set")
        for bar_type, instrument_id in zip(bar_types, instrument_ids):
            instrument = self.cache.instrument(instrument_id)
            if instrument is None:
                raise RuntimeError(f"missing instrument {instrument_id}")
            self._instruments[instrument_id] = instrument
            self._books[instrument_id] = _Book()
            self._bar_to_inst[bar_type] = instrument_id
            self.subscribe_bars(bar_type)

    def on_bar(self, bar: Bar) -> None:
        instrument_id = self._bar_to_inst.get(bar.bar_type)
        if instrument_id is None:
            return
        book = self._books[instrument_id]
        close = float(bar.close)
        book.highs.append(float(bar.high))
        book.lows.append(float(bar.low))
        book.closes.append(close)
        book.volumes.append(float(bar.volume))
        ts = int(bar.ts_event)
        if ts > 10**15:
            ts = ts // 1_000_000
        if ts > 10**12:
            ts = ts // 1000 if ts > 10**13 else ts
        book.times.append(int(bar.ts_event / 1_000_000) if bar.ts_event > 10**15 else int(bar.ts_event))
        self._manage(instrument_id, book, bar)
        if self._halted or self._consec_loss >= 5 or self._realized <= -40:
            self._halted = True
            return
        self._maybe_enter(instrument_id, book, bar)

    def _pack(self, book: _Book) -> dict[str, list[float]]:
        return {
            "ema_fast": indicators.ema(book.closes, self.cfg.fast_period),
            "ema_slow": indicators.ema(book.closes, self.cfg.slow_period),
            "adx": indicators.adx(book.highs, book.lows, book.closes, self.cfg.adx_period),
            "atr": indicators.atr(book.highs, book.lows, book.closes, self.cfg.atr_period),
            "vol_sma": indicators.sma(book.volumes, self.cfg.volume_avg_period),
        }

    def _atr_pctile(self, book: _Book, atr_vals: list[float]) -> float:
        atr_pct = [
            (atr_vals[i] / book.closes[i] * 100.0) if book.closes[i] else math.nan
            for i in range(len(book.closes))
        ]
        series = indicators.rolling_percentile(atr_pct, self.cfg.atr_percentile_lookback)
        value = series[-1] if series else math.nan
        return value

    def _manage(self, instrument_id: InstrumentId, book: _Book, bar: Bar) -> None:
        instrument = self._instruments[instrument_id]
        if book.pending is not None:
            limit = float(book.pending["limit"])
            age_h = (len(book.closes) - 1) - int(book.pending["bar"])
            if age_h >= self.cfg.limit_ttl_hours:
                self.cancel_all_orders(instrument_id)
                book.pending = None
            elif float(bar.low) <= limit and book.pos is None:
                fill = limit + float(instrument.price_increment) * self.cfg.slippage_ticks
                book.pos = {
                    "entry": fill,
                    "qty": float(book.pending["qty"]),
                    "remaining": float(book.pending["qty"]),
                    "stop": float(book.pending["stop"]),
                    "first_tp": float(book.pending["first_tp"]),
                    "atr": float(book.pending["atr"]),
                    "bar": len(book.closes) - 1,
                    "half": False,
                }
                book.pending = None
        pos = book.pos
        if pos is None:
            return
        stop = float(pos["stop"])
        if float(bar.low) <= stop:
            self._flatten(instrument_id, book, stop, "stop")
            return
        if not pos["half"] and float(bar.high) >= float(pos["first_tp"]):
            self._take_half(instrument_id, book, float(pos["first_tp"]))
        if book.pos and book.pos["half"]:
            trail = float(bar.close) - self.cfg.trail_atr_mult * float(book.pos["atr"])
            if trail > float(book.pos["stop"]):
                book.pos["stop"] = trail
        if book.pos and (len(book.closes) - 1) - int(book.pos["bar"]) >= self.cfg.time_stop_hours:
            self._flatten(instrument_id, book, float(bar.close), "time_stop")

    def _maybe_enter(self, instrument_id: InstrumentId, book: _Book, bar: Bar) -> None:
        if book.pos is not None or book.pending is not None:
            return
        open_count = sum(1 for item in self._books.values() if item.pos or item.pending)
        if open_count >= self.cfg.max_concurrent:
            return
        if len(book.closes) < max(self.cfg.slow_period, 2 * self.cfg.adx_period, 80):
            return
        ts = book.times[-1]
        if risk.near_funding(ts if ts < 10**12 else ts // 1000):
            return
        pack = self._pack(book)
        adx_now = pack["adx"][-1]
        atr_now = pack["atr"][-1]
        fast = pack["ema_fast"][-1]
        slow = pack["ema_slow"][-1]
        vol_sma = pack["vol_sma"][-1]
        atr_pctile = self._atr_pctile(book, pack["atr"])
        needed = (adx_now, atr_now, fast, slow, vol_sma, atr_pctile)
        if any(isinstance(v, float) and math.isnan(v) for v in needed):
            return
        in_regime = (
            fast > slow
            and adx_now >= self.cfg.adx_min
            and self.cfg.atr_pct_lo <= atr_pctile <= self.cfg.atr_pct_hi
        )
        if not in_regime:
            book.setup_bar = None
            return
        if book.setup_bar is None:
            book.setup_bar = len(book.closes) - 1
        if (len(book.closes) - 1) - book.setup_bar > self.cfg.volume_confirm_bars:
            return
        if book.volumes[-1] < self.cfg.volume_mult * vol_sma:
            return
        stop_dist = self.cfg.stop_atr_mult * atr_now
        instrument = self._instruments[instrument_id]
        lot = float(instrument.size_increment)
        qty = risk.position_qty(
            risk_usdt=float(self.cfg.risk_usdt),
            stop_distance=stop_dist,
            lot=lot,
        )
        if qty <= 0:
            return
        limit = float(bar.close)
        book.pending = {
            "limit": limit,
            "qty": qty,
            "stop": limit - stop_dist,
            "first_tp": limit + self.cfg.first_tp_r * stop_dist,
            "atr": atr_now,
            "bar": len(book.closes) - 1,
        }
        book.setup_bar = None
        quantity = Quantity(Decimal(str(qty)), instrument.size_precision)
        price = Price(Decimal(str(limit)), instrument.price_precision)
        order = self.order_factory.limit(
            instrument_id=instrument_id,
            order_side=OrderSide.BUY,
            quantity=quantity,
            price=price,
            time_in_force=TimeInForce.GTC,
        )
        self.submit_order(order)

    def _take_half(self, instrument_id: InstrumentId, book: _Book, price: float) -> None:
        pos = book.pos
        if pos is None:
            return
        qty = float(pos["qty"]) * self.cfg.first_tp_fraction
        self._emit_close(instrument_id, qty)
        pos["remaining"] = float(pos["remaining"]) - qty
        pos["half"] = True

    def _flatten(self, instrument_id: InstrumentId, book: _Book, price: float, reason: str) -> None:
        pos = book.pos
        if pos is None:
            return
        remaining = float(pos["remaining"])
        entry = float(pos["entry"])
        pnl = (price - entry) * remaining
        self._realized += pnl
        if pnl < 0:
            self._consec_loss += 1
        else:
            self._consec_loss = 0
        self._emit_close(instrument_id, remaining)
        book.pos = None
        _ = reason

    def _emit_close(self, instrument_id: InstrumentId, qty: float) -> None:
        instrument = self._instruments[instrument_id]
        if qty <= 0:
            return
        quantity = Quantity(Decimal(str(qty)), instrument.size_precision)
        order = self.order_factory.market(
            instrument_id=instrument_id,
            order_side=OrderSide.SELL,
            quantity=quantity,
            time_in_force=TimeInForce.GTC,
        )
        self.submit_order(order)

    def on_stop(self) -> None:
        for instrument_id in self._instruments:
            self.cancel_all_orders(instrument_id)
            self.close_all_positions(instrument_id)
