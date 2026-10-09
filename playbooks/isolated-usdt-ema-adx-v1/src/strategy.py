from decimal import Decimal, ROUND_DOWN
from typing import Optional

from nautilus_trader.config import StrategyConfig
from nautilus_trader.model.data import Bar, BarType
from nautilus_trader.model.enums import OrderSide, TimeInForce
from nautilus_trader.model.identifiers import InstrumentId
from nautilus_trader.model.instruments import Instrument
from nautilus_trader.model.objects import Price, Quantity
from nautilus_trader.trading.strategy import Strategy


class EmaAdxTrendStrategyConfig(StrategyConfig):
    instrument_ids: tuple[InstrumentId, ...] = ()
    bar_types: tuple[BarType, ...] = ()
    fast_ema_period: int = 20
    slow_ema_period: int = 50
    adx_period: int = 14
    adx_minimum: float = 25.0
    atr_period: int = 14
    atr_percentile_lookback: int = 252
    atr_percentile_minimum: float = 20.0
    atr_percentile_maximum: float = 80.0
    volume_average_period: int = 20
    volume_multiplier: float = 1.5
    stop_atr_multiplier: float = 1.5
    take_profit_r: float = 2.0
    risk_usdt: float = 15.0
    time_stop_bars: int = 8
    entry_cancel_bars: int = 4
    max_concurrent_positions: int = 3
    daily_entry_pause_usdt: float = 30.0
    daily_stop_usdt: float = 40.0
    consecutive_loss_halt: int = 5
    slippage_ticks: int = 1


class EmaAdxTrendStrategy(Strategy):
    """Long-only EMA trend strategy with explicit regime and risk gates."""

    def __init__(self, config: EmaAdxTrendStrategyConfig) -> None:
        super().__init__(config)
        self.cfg = config
        self._instruments: dict[str, Instrument] = {}
        self._bars: dict[str, list[dict[str, float]]] = {}
        self._atr_history: dict[str, list[float]] = {}
        self._pending: dict[str, dict[str, float]] = {}
        self._active: dict[str, dict[str, float]] = {}
        self._exit_pending: dict[str, float] = {}
        self._day_key: Optional[int] = None
        self._daily_realized = 0.0
        self._consecutive_losses = 0
        self._hard_stopped = False

    def on_start(self) -> None:
        if not self.cfg.instrument_ids or not self.cfg.bar_types:
            raise RuntimeError("multi-instrument ids and bar types are required")
        if len(self.cfg.instrument_ids) != len(self.cfg.bar_types):
            raise RuntimeError("instrument_ids and bar_types must align")
        for instrument_id, bar_type in zip(
            self.cfg.instrument_ids, self.cfg.bar_types
        ):
            instrument = self.cache.instrument(instrument_id)
            if instrument is None:
                raise RuntimeError(f"instrument unavailable: {instrument_id}")
            key = str(instrument_id)
            self._instruments[key] = instrument
            self._bars[key] = []
            self._atr_history[key] = []
            self.subscribe_bars(bar_type)

    def on_bar(self, bar: Bar) -> None:
        instrument_id = bar.bar_type.instrument_id
        key = str(instrument_id)
        instrument = self._instruments.get(key)
        if instrument is None:
            return
        day_key = int(bar.ts_event // 86_400_000_000_000)
        if self._day_key != day_key:
            self._day_key = day_key
            self._daily_realized = 0.0

        row = {
            "open": float(bar.open),
            "high": float(bar.high),
            "low": float(bar.low),
            "close": float(bar.close),
            "volume": float(bar.volume),
        }
        history = self._bars[key]
        history.append(row)
        max_history = max(self.cfg.atr_percentile_lookback + 100, 500)
        if len(history) > max_history:
            del history[:-max_history]

        atr, adx = self._atr_adx(history)
        if atr is not None:
            atr_values = self._atr_history[key]
            atr_values.append(atr)
            if len(atr_values) > self.cfg.atr_percentile_lookback:
                del atr_values[:-self.cfg.atr_percentile_lookback]

        positions = self.cache.positions_open(instrument_id=instrument_id)
        if key in self._exit_pending and not positions:
            outcome = self._exit_pending.pop(key)
            self._daily_realized += outcome
            if outcome < 0:
                self._consecutive_losses += 1
            else:
                self._consecutive_losses = 0
            self._active.pop(key, None)
            if (
                self._daily_realized <= -self.cfg.daily_stop_usdt
                or self._consecutive_losses >= self.cfg.consecutive_loss_halt
            ):
                self._hard_stopped = True

        if positions and key not in self._active and key in self._pending:
            plan = self._pending.pop(key)
            self._active[key] = {
                "entry": plan["entry"],
                "stop": plan["stop"],
                "target": plan["target"],
                "bars": 0.0,
            }

        active = self._active.get(key)
        if active is not None and positions:
            active["bars"] += 1.0
            reason_r: Optional[float] = None
            if row["low"] <= active["stop"]:
                reason_r = -1.0
            elif row["high"] >= active["target"]:
                reason_r = self.cfg.take_profit_r
            elif active["bars"] >= self.cfg.time_stop_bars:
                reason_r = (
                    (row["close"] - active["entry"])
                    / (active["entry"] - active["stop"])
                )
            elif self._ema(history, self.cfg.fast_ema_period) < self._ema(
                history, self.cfg.slow_ema_period
            ):
                reason_r = (
                    (row["close"] - active["entry"])
                    / (active["entry"] - active["stop"])
                )
            if reason_r is not None:
                for position in positions:
                    self._submit_market(
                        instrument_id, OrderSide.SELL, position.quantity
                    )
                # Circuit breakers use a conservative, fee-unadjusted estimate
                # during replay. Final evidence uses engine fills and fees.
                self._exit_pending[key] = min(
                    reason_r * self.cfg.risk_usdt,
                    self.cfg.take_profit_r * self.cfg.risk_usdt,
                )
            return

        pending = self._pending.get(key)
        if pending is not None:
            pending["bars"] += 1.0
            if pending["bars"] >= self.cfg.entry_cancel_bars:
                self.cancel_all_orders(instrument_id)
                self._pending.pop(key, None)
            return

        if atr is None or adx is None or not self._entry_allowed():
            return
        if len(history) < max(
            self.cfg.slow_ema_period + 2,
            self.cfg.volume_average_period + 2,
            self.cfg.atr_percentile_lookback,
        ):
            return

        fast_now = self._ema(history, self.cfg.fast_ema_period)
        slow_now = self._ema(history, self.cfg.slow_ema_period)
        fast_previous = self._ema(history[:-1], self.cfg.fast_ema_period)
        close_previous = history[-2]["close"]
        close_now = history[-1]["close"]
        crossed_up = close_previous <= fast_previous and close_now > fast_now
        prior_volumes = [
            item["volume"]
            for item in history[-self.cfg.volume_average_period - 1 : -1]
        ]
        average_volume = sum(prior_volumes) / len(prior_volumes)
        volume_ok = row["volume"] >= self.cfg.volume_multiplier * average_volume
        atr_percentile = self._percentile_rank(self._atr_history[key], atr)
        regime_ok = (
            adx >= self.cfg.adx_minimum
            and self.cfg.atr_percentile_minimum
            <= atr_percentile
            <= self.cfg.atr_percentile_maximum
        )
        if not (
            crossed_up
            and fast_now > slow_now
            and close_now > fast_now
            and volume_ok
            and regime_ok
        ):
            return

        tick = float(instrument.price_increment)
        entry = close_now + self.cfg.slippage_ticks * tick
        stop_distance = self.cfg.stop_atr_multiplier * atr
        if stop_distance <= 0:
            return
        raw_qty = self.cfg.risk_usdt / stop_distance
        step = Decimal(1).scaleb(-instrument.size_precision)
        qty_value = Decimal(str(raw_qty)).quantize(step, rounding=ROUND_DOWN)
        if qty_value <= 0:
            return
        quantity = Quantity(qty_value, instrument.size_precision)
        entry_price = Price(Decimal(str(entry)), instrument.price_precision)
        order = self.order_factory.limit(
            instrument_id=instrument_id,
            order_side=OrderSide.BUY,
            quantity=quantity,
            price=entry_price,
            time_in_force=TimeInForce.GTC,
        )
        self.submit_order(order)
        self._pending[key] = {
            "entry": entry,
            "stop": entry - stop_distance,
            "target": entry + self.cfg.take_profit_r * stop_distance,
            "bars": 0.0,
        }

    def _entry_allowed(self) -> bool:
        if self._hard_stopped:
            return False
        if self._daily_realized <= -self.cfg.daily_entry_pause_usdt:
            return False
        if self._consecutive_losses >= self.cfg.consecutive_loss_halt:
            return False
        open_count = sum(
            len(self.cache.positions_open(instrument_id=instrument.id))
            for instrument in self._instruments.values()
        )
        return open_count < self.cfg.max_concurrent_positions

    @staticmethod
    def _ema(history: list[dict[str, float]], period: int) -> float:
        values = [item["close"] for item in history]
        alpha = 2.0 / (period + 1.0)
        value = values[0]
        for item in values[1:]:
            value = alpha * item + (1.0 - alpha) * value
        return value

    def _atr_adx(
        self, history: list[dict[str, float]]
    ) -> tuple[Optional[float], Optional[float]]:
        period = self.cfg.adx_period
        if len(history) < period * 2 + 1:
            return None, None
        true_ranges: list[float] = []
        plus_dm: list[float] = []
        minus_dm: list[float] = []
        for previous, current in zip(history[:-1], history[1:]):
            true_ranges.append(
                max(
                    current["high"] - current["low"],
                    abs(current["high"] - previous["close"]),
                    abs(current["low"] - previous["close"]),
                )
            )
            up = current["high"] - previous["high"]
            down = previous["low"] - current["low"]
            plus_dm.append(up if up > down and up > 0 else 0.0)
            minus_dm.append(down if down > up and down > 0 else 0.0)
        dx_values: list[float] = []
        for end in range(period, len(true_ranges) + 1):
            tr_sum = sum(true_ranges[end - period : end])
            if tr_sum <= 0:
                continue
            plus_di = 100.0 * sum(plus_dm[end - period : end]) / tr_sum
            minus_di = 100.0 * sum(minus_dm[end - period : end]) / tr_sum
            denominator = plus_di + minus_di
            if denominator > 0:
                dx_values.append(100.0 * abs(plus_di - minus_di) / denominator)
        if len(dx_values) < period:
            return None, None
        atr = sum(true_ranges[-self.cfg.atr_period :]) / self.cfg.atr_period
        adx = sum(dx_values[-period:]) / period
        return atr, adx

    @staticmethod
    def _percentile_rank(values: list[float], current: float) -> float:
        if not values:
            return 0.0
        return 100.0 * sum(value <= current for value in values) / len(values)

    def _submit_market(
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

    def on_stop(self) -> None:
        for instrument_id in self.cfg.instrument_ids:
            self.cancel_all_orders(instrument_id)
            self.close_all_positions(instrument_id)
