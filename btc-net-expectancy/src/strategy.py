from decimal import Decimal, ROUND_DOWN
from typing import Optional

from nautilus_trader.config import StrategyConfig
from nautilus_trader.model.data import Bar, BarType
from nautilus_trader.model.enums import OrderSide, TimeInForce
from nautilus_trader.model.identifiers import InstrumentId
from nautilus_trader.model.instruments import Instrument
from nautilus_trader.model.objects import Price, Quantity
from nautilus_trader.trading.strategy import Strategy


class BtcNetExpectancyConfig(StrategyConfig):
    instrument_id: Optional[InstrumentId] = None
    bar_type: Optional[BarType] = None
    instrument_ids: tuple[InstrumentId, ...] = ()
    bar_types: tuple[BarType, ...] = ()
    risk_usdt: str = "15"
    atr_period: int = 14
    atr_stop_multiple: str = "1.5"
    adx_period: int = 14
    adx_min: str = "30"
    breakout_period: int = 48
    long_trend_period: int = 200
    trend_slope_hours: int = 24
    atr_percentile_lookback: int = 168
    atr_percentile_min: str = "30"
    atr_percentile_max: str = "75"
    min_atr_pct: str = "0.7"
    take_profit_r: str = "2"
    time_stop_hours: int = 8
    order_ttl_hours: int = 4
    min_24h_volume_usdt: str = "100000000"


class BtcNetExpectancyStrategy(Strategy):
    def __init__(self, config: BtcNetExpectancyConfig) -> None:
        super().__init__(config)
        self.cfg = config
        self._instrument: Optional[Instrument] = None
        self._bar_type: Optional[BarType] = None
        self._highs: list[float] = []
        self._lows: list[float] = []
        self._closes: list[float] = []
        self._volumes: list[float] = []
        self._trs: list[float] = []
        self._atr_history: list[float] = []
        self._pending_entry = False
        self._pending_bars = 0
        self._entry_price = 0.0
        self._stop_price = 0.0
        self._target_price = 0.0
        self._entry_bar = 0

    def on_start(self) -> None:
        self._bar_type = self.cfg.bar_type or (
            self.cfg.bar_types[0] if self.cfg.bar_types else None
        )
        instrument_id = self.cfg.instrument_id or (
            self.cfg.instrument_ids[0] if self.cfg.instrument_ids else None
        )
        if self._bar_type is None or instrument_id is None:
            raise RuntimeError("bar_type and instrument_id must be set")
        self._instrument = self.cache.instrument(instrument_id)
        if self._instrument is None:
            raise RuntimeError(f"instrument not found: {instrument_id}")
        self.subscribe_bars(self._bar_type)

    def on_bar(self, bar: Bar) -> None:
        instrument = self._instrument
        if instrument is None:
            return

        high = float(bar.high)
        low = float(bar.low)
        close = float(bar.close)
        volume = float(bar.volume)
        previous_close = self._closes[-1] if self._closes else close
        true_range = max(high - low, abs(high - previous_close), abs(low - previous_close))

        self._highs.append(high)
        self._lows.append(low)
        self._closes.append(close)
        self._volumes.append(volume)
        self._trs.append(true_range)

        atr = self._mean(self._trs[-self.cfg.atr_period :])
        if len(self._trs) >= self.cfg.atr_period:
            self._atr_history.append(atr)

        positions = self.cache.positions_open(instrument_id=instrument.id)
        has_position = bool(positions)
        if self._pending_entry and has_position:
            self._pending_entry = False
            self._entry_bar = len(self._closes) - 1

        if has_position:
            elapsed = len(self._closes) - 1 - self._entry_bar
            if low <= self._stop_price:
                self._close_long(instrument)
            elif high >= self._target_price:
                self._close_long(instrument)
            elif elapsed >= self.cfg.time_stop_hours:
                self._close_long(instrument)
            return

        if self._pending_entry:
            self._pending_bars += 1
            if self._pending_bars >= self.cfg.order_ttl_hours:
                self.cancel_all_orders(instrument.id)
                self._pending_entry = False
            return

        warmup = max(
            self.cfg.breakout_period + 1,
            self.cfg.adx_period * 2 + 1,
            self.cfg.long_trend_period + self.cfg.trend_slope_hours,
            self.cfg.atr_percentile_lookback + self.cfg.atr_period,
            24,
        )
        if len(self._closes) < warmup or atr <= 0:
            return

        adx = self._adx(self.cfg.adx_period)
        atr_percentile = self._percentile_rank(
            self._atr_history[-self.cfg.atr_percentile_lookback :],
            atr,
        )
        prior_high = max(self._highs[-self.cfg.breakout_period - 1 : -1])
        trend_now = self._ema(self._closes[-self.cfg.long_trend_period :])
        trend_then = self._ema(
            self._closes[
                -self.cfg.long_trend_period - self.cfg.trend_slope_hours :
                -self.cfg.trend_slope_hours
            ]
        )
        quote_volume_24h = sum(
            self._volumes[-24 + i] * self._closes[-24 + i] for i in range(24)
        )
        if close <= prior_high:
            return
        if close <= trend_now or trend_now <= trend_then:
            return
        if adx < float(self.cfg.adx_min):
            return
        if not (
            float(self.cfg.atr_percentile_min)
            <= atr_percentile
            <= float(self.cfg.atr_percentile_max)
        ):
            return
        if atr / close * 100.0 < float(self.cfg.min_atr_pct):
            return
        if quote_volume_24h < float(self.cfg.min_24h_volume_usdt):
            return

        tick = float(instrument.price_increment)
        entry = close - tick
        stop_distance = float(self.cfg.atr_stop_multiple) * atr
        stop = entry - stop_distance - tick
        target = entry + float(self.cfg.take_profit_r) * stop_distance - tick
        raw_qty = Decimal(self.cfg.risk_usdt) / Decimal(str(stop_distance))
        step = Decimal(str(instrument.size_increment))
        qty_decimal = (raw_qty / step).to_integral_value(rounding=ROUND_DOWN) * step
        if qty_decimal <= 0:
            return

        qty = Quantity(qty_decimal, instrument.size_precision)
        price = Price(Decimal(str(entry)), instrument.price_precision)
        order = self.order_factory.limit(
            instrument_id=instrument.id,
            order_side=OrderSide.BUY,
            quantity=qty,
            price=price,
            time_in_force=TimeInForce.GTC,
        )
        self.submit_order(order)
        self._pending_entry = True
        self._pending_bars = 0
        self._entry_price = entry
        self._stop_price = stop
        self._target_price = target

    def _close_long(self, instrument: Instrument) -> None:
        for position in self.cache.positions_open(instrument_id=instrument.id):
            order = self.order_factory.market(
                instrument_id=instrument.id,
                order_side=OrderSide.SELL,
                quantity=position.quantity,
                time_in_force=TimeInForce.GTC,
            )
            self.submit_order(order)

    def _adx(self, period: int) -> float:
        dx_values: list[float] = []
        first_end = max(period + 1, len(self._closes) - period + 1)
        for end in range(first_end, len(self._closes) + 1):
            start = end - period
            plus_dm = 0.0
            minus_dm = 0.0
            tr_sum = 0.0
            for idx in range(start, end):
                up = self._highs[idx] - self._highs[idx - 1]
                down = self._lows[idx - 1] - self._lows[idx]
                plus_dm += up if up > down and up > 0 else 0.0
                minus_dm += down if down > up and down > 0 else 0.0
                tr_sum += self._trs[idx]
            if tr_sum <= 0:
                continue
            plus_di = 100.0 * plus_dm / tr_sum
            minus_di = 100.0 * minus_dm / tr_sum
            denominator = plus_di + minus_di
            if denominator > 0:
                dx_values.append(100.0 * abs(plus_di - minus_di) / denominator)
        return self._mean(dx_values[-period:])

    @staticmethod
    def _mean(values: list[float]) -> float:
        return sum(values) / len(values) if values else 0.0

    @staticmethod
    def _ema(values: list[float]) -> float:
        if not values:
            return 0.0
        alpha = 2.0 / (len(values) + 1)
        current = values[0]
        for value in values[1:]:
            current = alpha * value + (1.0 - alpha) * current
        return current

    @staticmethod
    def _percentile_rank(values: list[float], current: float) -> float:
        if not values:
            return 0.0
        return 100.0 * sum(1 for value in values if value <= current) / len(values)

    def on_stop(self) -> None:
        if self._instrument is not None:
            self.cancel_all_orders(self._instrument.id)
            self.close_all_positions(self._instrument.id)
