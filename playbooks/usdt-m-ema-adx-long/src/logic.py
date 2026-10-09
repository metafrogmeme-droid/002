"""Pure entry and halt decision. Invalid inputs return hold, never a side."""

from dataclasses import dataclass
from datetime import datetime

try:
    from .params import Config
    from .reasons import (
        FILTER_FUNDING_RATE,
        FILTER_FUNDING_WINDOW,
        FILTER_NO_CROSS,
        FILTER_REGIME_ADX,
        FILTER_REGIME_ATR_PCT,
        FILTER_REGIME_DI,
        FILTER_VOLUME,
        HALT_CONSECUTIVE_LOSSES,
        HALT_DAILY_LOSS,
        HALT_MAX_POSITIONS,
        HALT_PLAYBOOK_LOSS,
        HALT_STALE_DATA,
        INSUFFICIENT_HISTORY,
        INVALID_SIGNAL,
        SHORTS_DISABLED,
        SKIP_SYMBOL_BUSY,
        TRIGGER_LONG,
    )
    from .risk import in_funding_blackout, plan_long_size
except ImportError:
    from params import Config
    from reasons import (
        FILTER_FUNDING_RATE,
        FILTER_FUNDING_WINDOW,
        FILTER_NO_CROSS,
        FILTER_REGIME_ADX,
        FILTER_REGIME_ATR_PCT,
        FILTER_REGIME_DI,
        FILTER_VOLUME,
        HALT_CONSECUTIVE_LOSSES,
        HALT_DAILY_LOSS,
        HALT_MAX_POSITIONS,
        HALT_PLAYBOOK_LOSS,
        HALT_STALE_DATA,
        INSUFFICIENT_HISTORY,
        INVALID_SIGNAL,
        SHORTS_DISABLED,
        SKIP_SYMBOL_BUSY,
        TRIGGER_LONG,
    )
    from risk import in_funding_blackout, plan_long_size


def _finite(value: float | None) -> bool:
    return value is not None and value == value and value not in (float("inf"), float("-inf"))


@dataclass(frozen=True)
class Snapshot:
    symbol: str
    close_ts: datetime
    close: float | None
    atr: float | None
    atr_pct: float | None
    adx: float | None
    plus_di: float | None
    minus_di: float | None
    fast_ema: float | None
    slow_ema: float | None
    prev_fast_ema: float | None
    prev_slow_ema: float | None
    volume: float | None
    volume_avg_prev: float | None
    funding_rate: float | None
    price_tick: float
    size_step: float
    min_qty: float


@dataclass(frozen=True)
class AccountState:
    open_positions: int
    symbol_busy: bool
    daily_realised: float
    cumulative_realised: float
    consecutive_losses: int
    margin_remaining: float
    ticker_age_seconds: float | None
    apply_ticker_staleness: bool


@dataclass(frozen=True)
class Decision:
    action: str
    side: str
    reason_code: str
    entry: float | None = None
    stop: float | None = None
    take_profit: float | None = None
    qty: float | None = None
    risk_usdt: float | None = None
    margin: float | None = None


def _hold(reason: str) -> Decision:
    return Decision(action="hold", side="none", reason_code=reason)


def decide(snapshot: Snapshot, cfg: Config, account: AccountState) -> Decision:
    """Return a long plan only when every gate passes. Otherwise hold."""
    if account.cumulative_realised <= cfg.playbook_stop_usdt:
        return _hold(HALT_PLAYBOOK_LOSS)
    if account.consecutive_losses >= cfg.max_consecutive_losses:
        return _hold(HALT_CONSECUTIVE_LOSSES)
    if account.daily_realised <= cfg.daily_pause_usdt:
        return _hold(HALT_DAILY_LOSS)
    if account.apply_ticker_staleness:
        age = account.ticker_age_seconds
        if not _finite(age) or age is None or age > cfg.stale_ticker_seconds:
            return _hold(HALT_STALE_DATA)
    if account.open_positions >= cfg.max_concurrent:
        return _hold(HALT_MAX_POSITIONS)
    if account.symbol_busy:
        return _hold(SKIP_SYMBOL_BUSY)

    required = (
        snapshot.close,
        snapshot.atr,
        snapshot.atr_pct,
        snapshot.adx,
        snapshot.plus_di,
        snapshot.minus_di,
        snapshot.fast_ema,
        snapshot.slow_ema,
        snapshot.prev_fast_ema,
        snapshot.prev_slow_ema,
        snapshot.volume,
        snapshot.volume_avg_prev,
        snapshot.funding_rate,
    )
    if any(not _finite(value) for value in required):
        history_missing = (
            snapshot.atr is None
            or snapshot.atr_pct is None
            or snapshot.adx is None
            or snapshot.fast_ema is None
            or snapshot.slow_ema is None
            or snapshot.prev_fast_ema is None
            or snapshot.prev_slow_ema is None
        )
        if history_missing and _finite(snapshot.close):
            return _hold(INSUFFICIENT_HISTORY)
        return _hold(INVALID_SIGNAL)

    assert snapshot.fast_ema is not None
    assert snapshot.slow_ema is not None
    assert snapshot.prev_fast_ema is not None
    assert snapshot.prev_slow_ema is not None
    assert snapshot.adx is not None
    assert snapshot.plus_di is not None
    assert snapshot.minus_di is not None
    assert snapshot.atr_pct is not None
    assert snapshot.volume is not None
    assert snapshot.volume_avg_prev is not None
    assert snapshot.funding_rate is not None
    assert snapshot.close is not None
    assert snapshot.atr is not None

    prev_diff = snapshot.prev_fast_ema - snapshot.prev_slow_ema
    diff = snapshot.fast_ema - snapshot.slow_ema
    cross_up = prev_diff <= 0.0 < diff
    cross_down = prev_diff >= 0.0 > diff
    if cross_down and not cfg.shorts_enabled:
        return _hold(SHORTS_DISABLED)
    if not cross_up:
        return _hold(FILTER_NO_CROSS)
    if snapshot.adx < cfg.adx_min:
        return _hold(FILTER_REGIME_ADX)
    if snapshot.plus_di <= snapshot.minus_di:
        return _hold(FILTER_REGIME_DI)
    if snapshot.atr_pct < cfg.atr_pct_low or snapshot.atr_pct > cfg.atr_pct_high:
        return _hold(FILTER_REGIME_ATR_PCT)
    if snapshot.volume_avg_prev <= 0 or snapshot.volume < cfg.volume_mult * snapshot.volume_avg_prev:
        return _hold(FILTER_VOLUME)
    if in_funding_blackout(snapshot.close_ts, cfg.funding_blackout_minutes):
        return _hold(FILTER_FUNDING_WINDOW)
    if snapshot.funding_rate > cfg.funding_against_max:
        return _hold(FILTER_FUNDING_RATE)

    plan = plan_long_size(
        close=snapshot.close,
        atr=snapshot.atr,
        atr_stop_mult=cfg.atr_stop_mult,
        reward_r=cfg.reward_r,
        fixed_loss_usdt=cfg.fixed_loss_usdt,
        price_tick=snapshot.price_tick,
        size_step=snapshot.size_step,
        min_qty=snapshot.min_qty,
        min_notional_usdt=cfg.min_notional_usdt,
        leverage=cfg.applied_leverage,
        margin_remaining=account.margin_remaining,
    )
    if plan.reason != TRIGGER_LONG:
        return _hold(plan.reason)
    return Decision(
        action="long",
        side="long",
        reason_code=TRIGGER_LONG,
        entry=float(plan.entry),
        stop=float(plan.stop),
        take_profit=float(plan.take_profit),
        qty=float(plan.qty),
        risk_usdt=float(plan.risk_usdt),
        margin=float(plan.margin),
    )
