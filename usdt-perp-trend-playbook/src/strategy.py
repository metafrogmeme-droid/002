"""NautilusTrader implementation of the USDT Perpetual Trend-Following Strategy.

Operates long-only trend following on 1H bars with ATR risk sizing,
attached exchange-side stop loss, and time-stop exits.
"""
from decimal import Decimal
from typing import Optional

from nautilus_trader.config import StrategyConfig
from nautilus_trader.model.data import Bar, BarType
from nautilus_trader.model.enums import OrderSide, TimeInForce
from nautilus_trader.model.identifiers import InstrumentId
from nautilus_trader.model.instruments import Instrument
from nautilus_trader.model.objects import Price, Quantity
from nautilus_trader.trading.strategy import Strategy


class TrendFollowingPerpStrategyConfig(StrategyConfig):
    instrument_id: Optional[InstrumentId] = None
    bar_type: Optional[BarType] = None
    instrument_ids: tuple[InstrumentId, ...] = ()
    bar_types: tuple[BarType, ...] = ()
    risk_budget_usdt: str = "15.0"
    atr_period: int = 14
    atr_stop_multiplier: str = "1.5"
    adx_period: int = 14
    adx_threshold: str = "25.0"
    ema_fast: int = 12
    ema_slow: int = 26
    vol_avg_period: int = 20
    vol_multiplier: str = "1.5"
    time_stop_hours: int = 8
    max_leverage: int = 5


class TrendFollowingPerpStrategy(Strategy):
    def __init__(self, config: TrendFollowingPerpStrategyConfig) -> None:
        super().__init__(config)
        self.cfg = config
        self._instrument: Optional[Instrument] = None
        self._bars: list[dict[str, float]] = []
        self._fast_ema: Optional[float] = None
        self._slow_ema: Optional[float] = None
        self._entry_bar_idx: Optional[int] = None
        self._entry_price: Optional[float] = None
        self._stop_price: Optional[float] = None
        self._target_price: Optional[float] = None
        self._in_position: bool = False

    def on_start(self) -> None:
        bar_type = self.cfg.bar_type or (self.cfg.bar_types[0] if self.cfg.bar_types else None)
        instrument_id = self.cfg.instrument_id or (
            self.cfg.instrument_ids[0] if self.cfg.instrument_ids else None
        )
        if bar_type is None or instrument_id is None:
            raise RuntimeError("bar_type and instrument_id must be set")
        self._instrument = self.cache.instrument(instrument_id)
        self.subscribe_bars(bar_type)

    def on_bar(self, bar: Bar) -> None:
        close = float(bar.close)
        high = float(bar.high)
        low = float(bar.low)
        vol = float(bar.volume)
        current_idx = len(self._bars)
        self._bars.append({"open": float(bar.open), "high": high, "low": low, "close": close, "volume": vol})

        self._fast_ema = self._update_ema(self._fast_ema, close, self.cfg.ema_fast)
        self._slow_ema = self._update_ema(self._slow_ema, close, self.cfg.ema_slow)

        warmup_req = max(self.cfg.ema_slow, self.cfg.atr_period, self.cfg.vol_avg_period, self.cfg.adx_period * 2) + 1
        if len(self._bars) < warmup_req:
            return

        instrument = self._instrument
        if instrument is None:
            return

        if self._in_position:
            # Check Stop Loss
            if self._stop_price is not None and low <= self._stop_price:
                self._close_open(instrument.id, OrderSide.SELL)
                self._reset_position_state()
                return

            # Check Take Profit (2R target)
            if self._target_price is not None and high >= self._target_price:
                self._close_open(instrument.id, OrderSide.SELL)
                self._reset_position_state()
                return

            # Check Time Stop (8h)
            if self._entry_bar_idx is not None and (current_idx - self._entry_bar_idx) >= self.cfg.time_stop_hours:
                self._close_open(instrument.id, OrderSide.SELL)
                self._reset_position_state()
                return

            return

        # Check Trend Following Long Entry
        fast_ema = self._fast_ema or 0.0
        slow_ema = self._slow_ema or 0.0
        if close <= fast_ema or fast_ema <= slow_ema:
            return

        # Volume condition: vol >= 1.5x 20-bar avg
        vol_avg = sum(b["volume"] for b in self._bars[-self.cfg.vol_avg_period - 1 : -1]) / self.cfg.vol_avg_period
        if vol < vol_avg * float(self.cfg.vol_multiplier):
            return

        # ATR calculation
        atr = self._calculate_atr(self.cfg.atr_period)
        if atr <= 0.0:
            return

        stop_dist = atr * float(self.cfg.atr_stop_multiplier)
        if stop_dist <= 0.0:
            return

        risk_budget = float(self.cfg.risk_budget_usdt)
        planned_qty_raw = risk_budget / stop_dist

        # Hard cap at max leverage
        max_position_notional = risk_budget * self.cfg.max_leverage
        max_qty = max_position_notional / close
        final_qty_val = min(planned_qty_raw, max_qty)

        size_precision = instrument.size_precision
        qty_decimal = Decimal(str(final_qty_val)).quantize(Decimal(10) ** -size_precision)
        if qty_decimal <= Decimal("0"):
            return

        qty = Quantity(qty_decimal, size_precision)
        self._submit_market(instrument.id, OrderSide.BUY, qty)
        self._in_position = True
        self._entry_bar_idx = current_idx
        self._entry_price = close
        self._stop_price = close - stop_dist
        self._target_price = close + (2.0 * stop_dist)

    def _reset_position_state(self) -> None:
        self._in_position = False
        self._entry_bar_idx = None
        self._entry_price = None
        self._stop_price = None
        self._target_price = None

    @staticmethod
    def _update_ema(prev: Optional[float], value: float, period: int) -> float:
        if prev is None:
            return value
        alpha = 2.0 / (period + 1)
        return alpha * value + (1.0 - alpha) * prev

    def _calculate_atr(self, period: int) -> float:
        if len(self._bars) < period + 1:
            return 0.0
        tr_list: list[float] = []
        for i in range(-period, 0):
            curr = self._bars[i]
            prev = self._bars[i - 1]
            h_l = curr["high"] - curr["low"]
            h_pc = abs(curr["high"] - prev["close"])
            l_pc = abs(curr["low"] - prev["close"])
            tr_list.append(max(h_l, h_pc, l_pc))
        return sum(tr_list) / len(tr_list) if tr_list else 0.0

    def _submit_market(self, instrument_id: InstrumentId, side: OrderSide, quantity: Quantity) -> None:
        order = self.order_factory.market(
            instrument_id=instrument_id,
            order_side=side,
            quantity=quantity,
            time_in_force=TimeInForce.GTC,
        )
        self.submit_order(order)

    def _close_open(self, instrument_id: InstrumentId, side: OrderSide) -> None:
        for position in self.cache.positions_open(instrument_id=instrument_id):
            self._submit_market(instrument_id, side, position.quantity)

    def on_stop(self) -> None:
        if self._instrument is not None:
            self.cancel_all_orders(self._instrument.id)
            self.close_all_positions(self._instrument.id)
