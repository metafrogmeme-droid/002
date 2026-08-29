from decimal import Decimal
from typing import Optional

from nautilus_trader.config import StrategyConfig
from nautilus_trader.model.data import Bar, BarType
from nautilus_trader.model.enums import OrderSide, TimeInForce
from nautilus_trader.model.identifiers import InstrumentId
from nautilus_trader.model.instruments import Instrument
from nautilus_trader.model.objects import Quantity
from nautilus_trader.trading.strategy import Strategy


class EmaCrossStrategyConfig(StrategyConfig):
    instrument_id: Optional[InstrumentId] = None
    bar_type: Optional[BarType] = None
    instrument_ids: tuple[InstrumentId, ...] = ()
    bar_types: tuple[BarType, ...] = ()
    trade_size: str = "0.01"
    fast_period: int = 12
    slow_period: int = 26


class EmaCrossStrategy(Strategy):
    def __init__(self, config: EmaCrossStrategyConfig) -> None:
        super().__init__(config)
        self.cfg = config
        self._closes: list[float] = []
        self._fast_ema: Optional[float] = None
        self._slow_ema: Optional[float] = None
        self._prev_diff: Optional[float] = None
        self._position: str = "NONE"
        self._instrument: Optional[Instrument] = None

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
        close = float(bar.close)
        self._closes.append(close)

        # Need enough warm-up before either EMA is meaningful.
        warmup = max(self.cfg.slow_period, self.cfg.fast_period) + 1
        if len(self._closes) < warmup:
            self._fast_ema = self._update_ema(self._fast_ema, close, self.cfg.fast_period)
            self._slow_ema = self._update_ema(self._slow_ema, close, self.cfg.slow_period)
            return

        self._fast_ema = self._update_ema(self._fast_ema, close, self.cfg.fast_period)
        self._slow_ema = self._update_ema(self._slow_ema, close, self.cfg.slow_period)

        diff = self._fast_ema - self._slow_ema  # type: ignore[operator]
        if self._prev_diff is None:
            self._prev_diff = diff
            return

        cross_up = self._prev_diff <= 0.0 < diff
        cross_down = self._prev_diff >= 0.0 > diff
        self._prev_diff = diff

        instrument = self._instrument
        if instrument is None:
            return
        qty = Quantity(Decimal(self.cfg.trade_size), instrument.size_precision)

        if self._position == "NONE":
            if cross_up:
                self._submit(instrument.id, OrderSide.BUY, qty)
                self._position = "LONG"
            elif cross_down:
                self._submit(instrument.id, OrderSide.SELL, qty)
                self._position = "SHORT"
            return

        if self._position == "LONG" and cross_down:
            self._close_open(instrument.id, OrderSide.SELL)
            self._position = "NONE"
        elif self._position == "SHORT" and cross_up:
            self._close_open(instrument.id, OrderSide.BUY)
            self._position = "NONE"

    @staticmethod
    def _update_ema(prev: Optional[float], value: float, period: int) -> float:
        if prev is None:
            return value
        alpha = 2.0 / (period + 1)
        return alpha * value + (1.0 - alpha) * prev

    def _submit(
        self,
        instrument_id: InstrumentId,
        side: OrderSide,
        quantity: Quantity,
    ) -> None:
        order = self.order_factory.market(
            instrument_id=instrument_id,
            order_side=side,
            quantity=quantity,
            time_in_force=TimeInForce.GTC,
        )
        self.submit_order(order)

    def _close_open(self, instrument_id: InstrumentId, side: OrderSide) -> None:
        for position in self.cache.positions_open(instrument_id=instrument_id):
            self._submit(instrument_id, side, position.quantity)

    def on_stop(self) -> None:
        if self._instrument is not None:
            self.cancel_all_orders(self._instrument.id)
            self.close_all_positions(self._instrument.id)
