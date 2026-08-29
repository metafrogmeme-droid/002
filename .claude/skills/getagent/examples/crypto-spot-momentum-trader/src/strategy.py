from decimal import Decimal
from typing import Optional

from nautilus_trader.config import StrategyConfig
from nautilus_trader.model.data import Bar, BarType
from nautilus_trader.model.enums import OrderSide, TimeInForce
from nautilus_trader.model.identifiers import InstrumentId
from nautilus_trader.model.instruments import Instrument
from nautilus_trader.model.objects import Quantity
from nautilus_trader.trading.strategy import Strategy


class SpotEmaMomentumStrategyConfig(StrategyConfig):
    instrument_id: Optional[InstrumentId] = None
    bar_type: Optional[BarType] = None
    instrument_ids: tuple[InstrumentId, ...] = ()
    bar_types: tuple[BarType, ...] = ()
    trade_size: str = "0.001"
    fast_period: int = 12
    slow_period: int = 26


class SpotEmaMomentumStrategy(Strategy):
    def __init__(self, config: SpotEmaMomentumStrategyConfig) -> None:
        super().__init__(config)
        self.cfg = config
        self._fast_ema: Optional[float] = None
        self._slow_ema: Optional[float] = None
        self._prev_diff: Optional[float] = None
        self._bar_count = 0
        self._invested = False
        self._instrument: Optional[Instrument] = None

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
        self._bar_count += 1
        self._fast_ema = self._update_ema(self._fast_ema, close, self.cfg.fast_period)
        self._slow_ema = self._update_ema(self._slow_ema, close, self.cfg.slow_period)
        if not self._is_warmed_up():
            return

        diff = self._fast_ema - self._slow_ema  # type: ignore[operator]
        if self._prev_diff is None:
            self._prev_diff = diff
            return
        self._trade_cross(diff)
        self._prev_diff = diff

    def _is_warmed_up(self) -> bool:
        return self._bar_count >= max(self.cfg.fast_period, self.cfg.slow_period) + 1

    @staticmethod
    def _update_ema(prev: Optional[float], value: float, period: int) -> float:
        if prev is None:
            return value
        alpha = 2.0 / (period + 1)
        return alpha * value + (1.0 - alpha) * prev

    def _trade_cross(self, diff: float) -> None:
        instrument = self._instrument
        if instrument is None or self._prev_diff is None:
            return
        cross_up = self._prev_diff <= 0.0 < diff
        cross_down = self._prev_diff >= 0.0 > diff
        if not self._invested and cross_up:
            self._buy(instrument)
        elif self._invested and cross_down:
            self._sell_open(instrument)

    def _buy(self, instrument: Instrument) -> None:
        qty = Quantity(Decimal(self.cfg.trade_size), instrument.size_precision)
        self._submit(instrument.id, OrderSide.BUY, qty)
        self._invested = True

    def _sell_open(self, instrument: Instrument) -> None:
        for position in self.cache.positions_open(instrument_id=instrument.id):
            self._submit(instrument.id, OrderSide.SELL, position.quantity)
        self._invested = False

    def _submit(self, instrument_id: InstrumentId, side: OrderSide, quantity: Quantity) -> None:
        order = self.order_factory.market(
            instrument_id=instrument_id,
            order_side=side,
            quantity=quantity,
            time_in_force=TimeInForce.GTC,
        )
        self.submit_order(order)

    def on_stop(self) -> None:
        if self._instrument is not None:
            self.cancel_all_orders(self._instrument.id)
            self.close_all_positions(self._instrument.id)
