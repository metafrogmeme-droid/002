"""Pure decision rules shared by live and replay paths."""

import math
from dataclasses import dataclass
from typing import Any, Mapping, Optional

from .indicators import IndicatorState, Snapshot

HOUR_MS = 3_600_000


@dataclass(frozen=True)
class Params:
    symbols: tuple[str, ...]
    leverage: int
    margin_budget: float
    risk_usdt: float
    atr_period: int
    adx_period: int
    ema_fast: int
    ema_slow: int
    atr_rank_window: int
    adx_min: float
    atr_rank_min: float
    atr_rank_max: float
    pullback_atr: float
    stop_atr: float
    tp_r: float
    entry_ttl_hours: int
    time_stop_hours: int
    min_quote_volume_usd: float
    max_spread_bps: float
    funding_interval_hours: int
    funding_blackout_minutes: int
    max_funding_r: float
    daily_pause_usdt: float
    daily_stop_usdt: float
    max_consecutive_losses: int
    max_data_age_seconds: int
    max_concurrent: int
    slippage_ticks: int

    @classmethod
    def from_config(cls, cfg: Mapping[str, Any]) -> "Params":
        def f(key: str, default: float) -> float:
            value = cfg.get(key, default)
            return float(default if value in (None, "") else value)

        def i(key: str, default: int) -> int:
            return int(f(key, default))

        symbols = tuple(str(s).upper() for s in (cfg.get("trading_symbols") or ("BTCUSDT", "ETHUSDT", "SOLUSDT")))
        leverage = min(max(i("leverage", 5), 1), 5)
        return cls(
            symbols=symbols,
            leverage=leverage,
            margin_budget=f("margin_budget", 1000.0),
            risk_usdt=f("risk_per_trade_usdt", 15.0),
            atr_period=i("atr_period", 14),
            adx_period=i("adx_period", 14),
            ema_fast=i("ema_fast", 20),
            ema_slow=i("ema_slow", 50),
            atr_rank_window=i("atr_rank_window_bars", 720),
            adx_min=f("adx_min", 25.0),
            atr_rank_min=f("atr_rank_min", 20.0),
            atr_rank_max=f("atr_rank_max", 90.0),
            pullback_atr=f("pullback_atr", 0.5),
            stop_atr=f("stop_atr", 1.5),
            tp_r=f("take_profit_r", 2.0),
            entry_ttl_hours=i("entry_ttl_hours", 4),
            time_stop_hours=i("time_stop_hours", 8),
            min_quote_volume_usd=f("min_quote_volume_usd_m", 100.0) * 1_000_000.0,
            max_spread_bps=f("max_spread_bps", 5.0),
            funding_interval_hours=i("funding_interval_hours", 8),
            funding_blackout_minutes=i("funding_blackout_minutes", 15),
            max_funding_r=f("max_funding_r", 0.1),
            daily_pause_usdt=f("daily_pause_loss_usdt", 30.0),
            daily_stop_usdt=f("daily_stop_loss_usdt", 40.0),
            max_consecutive_losses=i("max_consecutive_losses", 5),
            max_data_age_seconds=i("max_data_age_seconds", 60),
            max_concurrent=i("max_concurrent_positions", 1),
            slippage_ticks=i("slippage_ticks", 1),
        )

    def new_indicator_state(self) -> IndicatorState:
        return IndicatorState(
            atr_period=self.atr_period,
            adx_period=self.adx_period,
            ema_fast=self.ema_fast,
            ema_slow=self.ema_slow,
            atr_rank_window=self.atr_rank_window,
        )

    @property
    def warmup_bars(self) -> int:
        return self.atr_rank_window + self.atr_period + 2 * self.adx_period + 5


@dataclass(frozen=True)
class Setup:
    ok: bool
    reason: str
    limit: float = 0.0
    stop: float = 0.0
    take_profit: float = 0.0
    adx: float = 0.0
    atr: float = 0.0


def evaluate_setup(snap: Snapshot, p: Params) -> Setup:
    """Long-only trend-pullback trigger on the latest closed bar."""
    if not snap.ready():
        return Setup(False, "NO_TRADE_SIGNAL_INVALID")
    vals = (snap.atr, snap.adx, snap.ema_fast, snap.ema_slow, snap.close)
    if any((v is None) or (not math.isfinite(v)) or v <= 0 for v in vals):
        return Setup(False, "NO_TRADE_SIGNAL_INVALID")
    if snap.quote_volume_24h < p.min_quote_volume_usd:
        return Setup(False, "SKIP_VOLUME")
    trend = (
        snap.adx >= p.adx_min
        and snap.plus_di > snap.minus_di
        and snap.close > snap.ema_slow
        and snap.ema_fast > snap.ema_slow
    )
    if not trend:
        return Setup(False, "NO_TRADE_NO_SIGNAL")
    if not (p.atr_rank_min <= snap.atr_pct_rank <= p.atr_rank_max):
        return Setup(False, "SKIP_VOL_REGIME")
    limit = snap.close - p.pullback_atr * snap.atr
    stop = limit - p.stop_atr * snap.atr
    if limit <= 0 or stop <= 0 or stop >= limit:
        return Setup(False, "NO_TRADE_SIGNAL_INVALID")
    tp = limit + p.tp_r * (limit - stop)
    return Setup(True, "SIGNAL_TREND_PULLBACK", limit, stop, tp, float(snap.adx), float(snap.atr))


def in_funding_blackout(ts_ms: int, p: Params) -> bool:
    """True when ``ts_ms`` is within the blackout of an 8h funding settlement."""
    if p.funding_interval_hours != 8:
        return False
    period = p.funding_interval_hours * HOUR_MS
    offset = ts_ms % period
    dist = min(offset, period - offset)
    return dist <= p.funding_blackout_minutes * 60_000


def settlements_between(start_ms: int, end_ms: int, interval_hours: int) -> int:
    period = interval_hours * HOUR_MS
    first = -(-start_ms // period) * period
    if first > end_ms:
        return 0
    return int((end_ms - first) // period) + 1


def expected_funding_usdt(rate: Optional[float], notional: float, start_ms: int, p: Params) -> Optional[float]:
    """Worst-case funding paid by a long over the planned order+hold window."""
    if rate is None or not math.isfinite(rate):
        return None
    horizon = (p.entry_ttl_hours + p.time_stop_hours) * HOUR_MS
    n = settlements_between(start_ms, start_ms + horizon, p.funding_interval_hours)
    return max(rate, 0.0) * notional * n


def floor_to_step(value: float, step: float) -> float:
    if step <= 0:
        return value
    return math.floor(value / step + 1e-9) * step


def size_order(limit: float, stop: float, p: Params, size_step: float, min_qty: float, min_notional: float) -> tuple[float, str]:
    """Qty such that a stop-out loses ``risk_usdt`` before costs."""
    dist = limit - stop
    if dist <= 0:
        return 0.0, "SKIP_SIZE"
    qty = floor_to_step(p.risk_usdt / dist, size_step)
    if qty < min_qty or qty * limit < min_notional:
        return 0.0, "SKIP_SIZE_MIN"
    if qty * limit > p.leverage * p.margin_budget:
        return 0.0, "SKIP_SIZE_CAP"
    return qty, "OK"
