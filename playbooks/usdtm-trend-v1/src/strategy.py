"""Nautilus replay strategy for USDT-M Trend v1 (backtest path only).

Long-only EMA-ADX trend following on 1H bars with an ATR regime
gate, a volume-confirmation filter, an ATR stop, a fixed 2R target,
a bar-count time stop, and portfolio halt gates. Live-only gates
(funding blackout, funding guard, order TTL, stale feed) cannot be
replayed fairly and are enforced in ``main.py``; the replay assumes
those gates pass and this assumption is documented in the README.
"""

from decimal import Decimal
from typing import Dict, List, Optional

from nautilus_trader.config import StrategyConfig
from nautilus_trader.model.data import Bar, BarType
from nautilus_trader.model.enums import OrderSide, TimeInForce
from nautilus_trader.model.events import OrderFilled, PositionClosed
from nautilus_trader.model.identifiers import InstrumentId
from nautilus_trader.model.instruments import Instrument
from nautilus_trader.model.objects import Quantity
from nautilus_trader.trading.strategy import Strategy

from .indicators import TrendState
from .risk import check_portfolio_guards, position_qty, stop_take_prices


class UsdtmTrendStrategyConfig(StrategyConfig):
    instrument_ids: tuple = ()
    bar_types: tuple = ()
    instrument_id: Optional[InstrumentId] = None
    bar_type: Optional[BarType] = None
    ema_fast: int = 20
    ema_slow: int = 50
    adx_period: int = 14
    adx_threshold: float = 20.0
    atr_period: int = 14
    atr_stop_mult: float = 1.5
    atr_min_rank: float = 0.10
    volume_lookback: int = 20
    volume_mult: float = 1.5
    tp_r_mult: float = 2.0
    risk_per_trade_usdt: float = 15.0
    max_positions: int = 3
    time_stop_bars: int = 8
    daily_pause_usdt: float = -30.0
    daily_stop_usdt: float = -40.0
    max_consec_losses: int = 5


class UsdtmTrendStrategy(Strategy):
    def __init__(self, config: UsdtmTrendStrategyConfig) -> None:
        super().__init__(config)
        self.cfg = config
        self._bar_to_inst: Dict[str, str] = {}
        self._states: Dict[str, TrendState] = {}
        self._prev_diff: Dict[str, Optional[float]] = {}
        self._open: Dict[str, dict] = {}
        self._pending: Dict[str, dict] = {}
        self._order_to_inst: Dict[str, str] = {}
        self._daily_pnl: Dict[str, float] = {}
        self._consec_losses = 0
        self._halted = False
        self._halt_reason = ""
        self._day_key = ""
        self.trades_logged: List[dict] = []

    def on_start(self) -> None:
        ids = list(self.cfg.instrument_ids) or ([self.cfg.instrument_id] if self.cfg.instrument_id is not None else [])
        bars = list(self.cfg.bar_types) or ([self.cfg.bar_type] if self.cfg.bar_type is not None else [])
        if not ids or not bars or len(ids) != len(bars):
            raise RuntimeError("instrument_ids and bar_types must be set with equal length")
        for inst_id, bar_type in zip(ids, bars):
            key = str(inst_id)
            self._bar_to_inst[str(bar_type)] = key
            self._states[key] = TrendState(
                ema_fast=self.cfg.ema_fast,
                ema_slow=self.cfg.ema_slow,
                adx_period=self.cfg.adx_period,
                atr_period=self.cfg.atr_period,
                volume_lookback=self.cfg.volume_lookback,
            )
            self._prev_diff[key] = None
            self.subscribe_bars(bar_type)

    def _instrument_for(self, key: str) -> Optional[Instrument]:
        for inst_id in list(self.cfg.instrument_ids):
            if str(inst_id) == key:
                return self.cache.instrument(inst_id)
        if self.cfg.instrument_id is not None:
            return self.cache.instrument(self.cfg.instrument_id)
        return None

    def on_bar(self, bar: Bar) -> None:
        key = self._bar_to_inst.get(str(bar.bar_type))
        if key is None or self._halted:
            return
        close = float(bar.close)
        snap = self._states[key].update(float(bar.high), float(bar.low), close, float(bar.volume))

        if key in self._open:
            self._manage_open(key, bar, close)
            return
        if key in self._pending:
            return
        if not snap["ready"]:
            self._prev_diff[key] = (snap["ema_fast"] - snap["ema_slow"]) if snap["ema_fast"] else self._prev_diff[key]
            return

        diff = snap["ema_fast"] - snap["ema_slow"]
        prev = self._prev_diff[key]
        self._prev_diff[key] = diff
        if prev is None:
            return

        day = str(bar.ts_event)[:10]
        if day != self._day_key:
            self._day_key = day
        daily = self._daily_pnl.get(day, 0.0)
        guard = check_portfolio_guards(
            daily, self._consec_losses,
            daily_pause=self.cfg.daily_pause_usdt,
            daily_stop=self.cfg.daily_stop_usdt,
            max_consec=self.cfg.max_consec_losses,
        )
        if not guard["allow"]:
            if guard["halt"]:
                self._halted = True
                self._halt_reason = guard["code"]
            return

        if len(self._open) >= self.cfg.max_positions:
            return
        if not (prev <= 0.0 < diff):
            return
        if snap["adx"] is None or snap["adx"] <= self.cfg.adx_threshold:
            return
        if snap["atr_pct_rank"] is None or snap["atr_pct_rank"] < self.cfg.atr_min_rank:
            return
        if snap["volume_ratio"] is None or snap["volume_ratio"] < self.cfg.volume_mult:
            return

        instrument = self._instrument_for(key)
        if instrument is None:
            return
        st = stop_take_prices(close, snap["atr"], self.cfg.atr_stop_mult, self.cfg.tp_r_mult, side="long")
        if not st["ok"]:
            return
        sized = position_qty(self.cfg.risk_per_trade_usdt, st["risk_dist"],
                             size_increment=str(instrument.size_increment),
                             min_qty=str(instrument.lot_size) if hasattr(instrument, "lot_size") else "0")
        if not sized["ok"]:
            return
        qty = Quantity(Decimal(sized["qty"]), instrument.size_precision)
        notional = Decimal(sized["qty"]) * Decimal(str(close))
        if notional < Decimal("5"):
            return
        order = self.order_factory.market(
            instrument_id=instrument.id,
            order_side=OrderSide.BUY,
            quantity=qty,
            time_in_force=TimeInForce.GTC,
        )
        self._pending[key] = {
            "atr": float(snap["atr"]),
            "signal_close": close,
            "qty": sized["qty"],
            "bar_ts": bar.ts_event,
        }
        self._order_to_inst[order.client_order_id.value] = key
        self.submit_order(order)

    def _manage_open(self, key: str, bar: Bar, close: float) -> None:
        info = self._open[key]
        info["bars_held"] += 1
        instrument = self._instrument_for(key)
        if instrument is None:
            return
        exit_side = OrderSide.SELL
        reason = ""
        if float(bar.low) <= float(info["stop"]):
            reason = "stop"
        elif float(bar.high) >= float(info["take"]):
            reason = "take_profit_2R"
        elif info["bars_held"] >= self.cfg.time_stop_bars:
            reason = "time_stop"
        if not reason:
            return
        info["exit_reason"] = reason
        for position in self.cache.positions_open(instrument_id=instrument.id):
            closing = self.order_factory.market(
                instrument_id=instrument.id,
                order_side=exit_side,
                quantity=position.quantity,
                time_in_force=TimeInForce.GTC,
            )
            self.submit_order(closing)
        self._open.pop(key, None)
        info["exit_close"] = close

    def on_order_filled(self, event: OrderFilled) -> None:
        key = self._order_to_inst.get(event.client_order_id.value)
        if key is None:
            return
        pend = self._pending.pop(key, None)
        if pend is None:
            return
        fill_px = float(event.last_px)
        st = stop_take_prices(fill_px, pend["atr"], self.cfg.atr_stop_mult, self.cfg.tp_r_mult, side="long")
        if not st["ok"]:
            return
        self._open[key] = {
            "entry": fill_px,
            "qty": str(event.last_qty),
            "stop": float(st["stop"]),
            "take": float(st["take"]),
            "risk_dist": float(st["risk_dist"]),
            "bars_held": 0,
            "entry_ts": event.ts_event,
        }

    def on_position_closed(self, event: PositionClosed) -> None:
        pnl = float(event.realized_pnl) if event.realized_pnl is not None else 0.0
        day = self._day_key or "unknown"
        self._daily_pnl[day] = self._daily_pnl.get(day, 0.0) + pnl
        if pnl < 0:
            self._consec_losses += 1
        else:
            self._consec_losses = 0
        self.trades_logged.append({"day": day, "pnl": pnl})
        guard = check_portfolio_guards(
            self._daily_pnl.get(day, 0.0), self._consec_losses,
            daily_pause=self.cfg.daily_pause_usdt,
            daily_stop=self.cfg.daily_stop_usdt,
            max_consec=self.cfg.max_consec_losses,
        )
        if guard["halt"]:
            self._halted = True
            self._halt_reason = guard["code"]

    def on_stop(self) -> None:
        ids = list(self.cfg.instrument_ids) or ([self.cfg.instrument_id] if self.cfg.instrument_id is not None else [])
        for inst_id in ids:
            self.cancel_all_orders(inst_id)
            self.close_all_positions(inst_id)
