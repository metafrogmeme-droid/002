"""Nautilus replay strategy for Sleeve A BTC long v1.

Long-only, single-position, 1H bars. Entries gated by EMA alignment plus an
ADX/ATR-percentile regime read (the replayable analogue of the "AI/signal
validity" layer: no valid read means no trade). Every position carries a
volatility stop with a fixed multiple-of-risk target and a regime-dependent
time stop. One correlation cluster (crypto majors) maps to at most one open
position here because v1 trades BTCUSDT only.
"""

from decimal import Decimal
from typing import Optional

from nautilus_trader.config import StrategyConfig
from nautilus_trader.model.data import Bar, BarType
from nautilus_trader.model.enums import OrderSide, TimeInForce
from nautilus_trader.model.identifiers import InstrumentId
from nautilus_trader.model.instruments import Instrument
from nautilus_trader.model.objects import Quantity
from nautilus_trader.trading.strategy import Strategy

from .features import WilderState, ema_update


class BtcLongAtrStrategyConfig(StrategyConfig):
    instrument_id: Optional[InstrumentId] = None
    bar_type: Optional[BarType] = None
    instrument_ids: tuple[InstrumentId, ...] = ()
    bar_types: tuple[BarType, ...] = ()
    order_id_tag: str = "001"
    trade_size: str = "0.01"
    ema_fast: int = 20
    ema_slow: int = 50
    adx_period: int = 14
    adx_threshold: int = 20
    atr_period: int = 14
    atr_mult: float = 1.5
    tp_r_mult: float = 2.0
    rsi_period: int = 14
    rsi_oversold: int = 30
    atr_pct_lookback: int = 100
    atr_pct_max: int = 95
    trend_time_stop_bars: int = 8
    mr_time_stop_bars: int = 2


class BtcLongAtrStrategy(Strategy):
    def __init__(self, config: BtcLongAtrStrategyConfig) -> None:
        super().__init__(config)
        self.cfg = config
        self._instrument: Optional[Instrument] = None
        self._bar_type: Optional[BarType] = None
        self._closes: list[float] = []
        self._fast_ema: Optional[float] = None
        self._slow_ema: Optional[float] = None
        self._wilder = WilderState(
            atr_period=int(config.atr_period),
            adx_period=int(config.adx_period),
            rsi_period=int(config.rsi_period),
        )
        self._in_position = False
        self._entry_price = 0.0
        self._stop_price = 0.0
        self._target_price = 0.0
        self._bars_held = 0
        self._time_stop = 0

    def on_start(self) -> None:
        bar_type = self.cfg.bar_type or (
            self.cfg.bar_types[0] if self.cfg.bar_types else None
        )
        instrument_id = self.cfg.instrument_id or (
            self.cfg.instrument_ids[0] if self.cfg.instrument_ids else None
        )
        if bar_type is None or instrument_id is None:
            raise RuntimeError("bar_type and instrument_id must be set")
        self._bar_type = bar_type
        self._instrument = self.cache.instrument(instrument_id)
        self.subscribe_bars(bar_type)

    def on_bar(self, bar: Bar) -> None:
        instrument = self._instrument
        if instrument is None or self._bar_type is None:
            return
        close = float(bar.close)
        high = float(bar.high)
        low = float(bar.low)
        self._closes.append(close)
        self._fast_ema = ema_update(self._fast_ema, close, int(self.cfg.ema_fast))
        self._slow_ema = ema_update(self._slow_ema, close, int(self.cfg.ema_slow))
        read = self._wilder.update(high, low, close)
        if read is None:
            return

        if self._in_position:
            self._bars_held += 1
            if low <= self._stop_price:
                self._close_all(instrument.id, OrderSide.SELL)
                self._reset_position()
                return
            if high >= self._target_price:
                self._close_all(instrument.id, OrderSide.SELL)
                self._reset_position()
                return
            if self._bars_held >= self._time_stop:
                self._close_all(instrument.id, OrderSide.SELL)
                self._reset_position()
            return

        if not self._wilder.ready(int(self.cfg.ema_slow), int(self.cfg.atr_pct_lookback)):
            return
        if self._fast_ema is None or self._slow_ema is None:
            return
        adx = self._wilder.adx
        rsi = self._wilder.rsi
        atr = self._wilder.atr
        if adx is None or rsi is None or atr is None or atr <= 0:
            return
        atr_pctile = self._wilder.atr_pct_percentile(int(self.cfg.atr_pct_lookback))
        if atr_pctile is None or atr_pctile > float(self.cfg.atr_pct_max):
            return

        stop_dist = float(self.cfg.atr_mult) * atr
        if stop_dist <= 0:
            return
        signal_kind = ""
        if (
            adx >= float(self.cfg.adx_threshold)
            and self._fast_ema > self._slow_ema
            and close > self._slow_ema
        ):
            signal_kind = "trend"
            self._time_stop = int(self.cfg.trend_time_stop_bars)
        elif adx < float(self.cfg.adx_threshold) and rsi <= float(self.cfg.rsi_oversold):
            signal_kind = "mr"
            self._time_stop = int(self.cfg.mr_time_stop_bars)
        if not signal_kind:
            return
        qty = Quantity(Decimal(self.cfg.trade_size), instrument.size_precision)
        order = self.order_factory.market(
            instrument_id=instrument.id,
            order_side=OrderSide.BUY,
            quantity=qty,
            time_in_force=TimeInForce.GTC,
        )
        self.submit_order(order)
        self._in_position = True
        self._entry_price = close
        self._stop_price = close - stop_dist
        self._target_price = close + float(self.cfg.tp_r_mult) * stop_dist
        self._bars_held = 0

    def _close_all(self, instrument_id: InstrumentId, side: OrderSide) -> None:
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
        self._target_price = 0.0
        self._bars_held = 0
        self._time_stop = 0

    def on_stop(self) -> None:
        if self._instrument is not None:
            self.cancel_all_orders(self._instrument.id)
            self.close_all_positions(self._instrument.id)
