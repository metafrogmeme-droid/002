"""Nautilus Trader Strategy implementation for Crypto Perps Regime Trend-Following."""

from decimal import Decimal
from typing import Optional

from nautilus_trader.config import StrategyConfig
from nautilus_trader.model.data import Bar, BarType
from nautilus_trader.model.enums import OrderSide, TimeInForce
from nautilus_trader.model.identifiers import InstrumentId
from nautilus_trader.model.instruments import Instrument
from nautilus_trader.model.objects import Price, Quantity
from nautilus_trader.trading.strategy import Strategy

from .indicators import compute_adx, compute_atr, compute_ema


class CryptoPerpsRegimeStrategyConfig(StrategyConfig):
    instrument_id: Optional[InstrumentId] = None
    bar_type: Optional[BarType] = None
    instrument_ids: tuple[InstrumentId, ...] = ()
    bar_types: tuple[BarType, ...] = ()
    order_id_tag: str = "001"
    trade_size: str = "0.01"
    fast_period: int = 12
    slow_period: int = 26
    adx_period: int = 14
    atr_period: int = 14
    adx_threshold: float = 25.0
    risk_usdt: float = 15.0
    leverage: int = 3
    tp_mode: str = "fixed_2r"


class CryptoPerpsRegimeStrategy(Strategy):
    def __init__(self, config: CryptoPerpsRegimeStrategyConfig) -> None:
        super().__init__(config)
        self.cfg = config
        self._highs: list[float] = []
        self._lows: list[float] = []
        self._closes: list[float] = []
        self._instrument: Optional[Instrument] = None

        # Position tracking
        self._in_position = False
        self._entry_price: float = 0.0
        self._stop_price: float = 0.0
        self._tp_price: float = 0.0
        self._bars_in_position: int = 0
        self._time_stop_bars: int = 8

    def on_start(self) -> None:
        bar_type = self.cfg.bar_type or (
            self.cfg.bar_types[0] if self.cfg.bar_types else None
        )
        instrument_id = self.cfg.instrument_id or (
            self.cfg.instrument_ids[0] if self.cfg.instrument_ids else None
        )
        if bar_type is None or instrument_id is None:
            raise RuntimeError("bar_type and instrument_id must be set")
        self._instrument = self.cache.instrument(instrument_id)
        self.subscribe_bars(bar_type)

    def on_bar(self, bar: Bar) -> None:
        high = float(bar.high)
        low = float(bar.low)
        close = float(bar.close)

        self._highs.append(high)
        self._lows.append(low)
        self._closes.append(close)

        instrument = self._instrument
        if instrument is None:
            return

        warmup = max(self.cfg.slow_period, self.cfg.adx_period * 2) + 5
        if len(self._closes) < warmup:
            return

        # Position management
        if self._in_position:
            self._bars_in_position += 1

            # Check stop loss hit
            if low <= self._stop_price:
                self._close_position(instrument.id, OrderSide.SELL)
                self._reset_position()
                return

            # Check take profit hit
            if high >= self._tp_price:
                self._close_position(instrument.id, OrderSide.SELL)
                self._reset_position()
                return

            # Time stop exit (8h trend limit)
            if self._bars_in_position >= self._time_stop_bars:
                self._close_position(instrument.id, OrderSide.SELL)
                self._reset_position()
                return

            return

        # Entry logic: ADX regime check + EMA cross
        adx_series, plus_di, minus_di = compute_adx(
            self._highs, self._lows, self._closes, self.cfg.adx_period
        )
        current_adx = adx_series[-1]
        current_pdi = plus_di[-1]
        current_mdi = minus_di[-1]

        # Trending regime requirement
        if current_adx < self.cfg.adx_threshold or current_pdi <= current_mdi:
            return

        # EMA momentum check
        fast_ema = compute_ema(self._closes, self.cfg.fast_period)
        slow_ema = compute_ema(self._closes, self.cfg.slow_period)

        prev_fast = fast_ema[-2]
        prev_slow = slow_ema[-2]
        curr_fast = fast_ema[-1]
        curr_slow = slow_ema[-1]

        cross_up = prev_fast <= prev_slow and curr_fast > curr_slow
        if not cross_up:
            return

        # ATR calculation for risk sizing and stop placement
        atr_series = compute_atr(
            self._highs, self._lows, self._closes, self.cfg.atr_period
        )
        current_atr = atr_series[-1]
        if current_atr <= 0:
            return

        # Stop distance: 1.5 * ATR(14)
        stop_dist = 1.5 * current_atr
        self._stop_price = close - stop_dist
        self._entry_price = close

        # Target: 2R
        if self.cfg.tp_mode == "fixed_2r":
            self._tp_price = close + (2.0 * stop_dist)
        else:
            self._tp_price = close + (1.5 * stop_dist)

        # Dynamic sizing: 15 USDT risk / stop distance
        raw_size = self.cfg.risk_usdt / stop_dist
        step = 10 ** (-instrument.size_precision)
        quantized_size = max(float(instrument.min_quantity or step), round(raw_size // step * step, instrument.size_precision))

        order_qty = Quantity(Decimal(str(quantized_size)), instrument.size_precision)
        order = self.order_factory.market(
            instrument_id=instrument.id,
            order_side=OrderSide.BUY,
            quantity=order_qty,
            time_in_force=TimeInForce.GTC,
        )
        self.submit_order(order)
        self._in_position = True
        self._bars_in_position = 0

    def _close_position(self, instrument_id: InstrumentId, side: OrderSide) -> None:
        for position in self.cache.positions_open(instrument_id=instrument_id):
            order = self.order_factory.market(
                instrument_id=instrument_id,
                order_side=side,
                quantity=position.quantity,
                time_in_force=TimeInForce.GTC,
            )
            self.submit_order(order)

    def _reset_position(self) -> None:
        self._in_position = False
        self._entry_price = 0.0
        self._stop_price = 0.0
        self._tp_price = 0.0
        self._bars_in_position = 0

    def on_stop(self) -> None:
        if self._instrument is not None:
            self.cancel_all_orders(self._instrument.id)
            self.close_all_positions(self._instrument.id)
