"""Load frozen v1 parameters from manifest strategy_config.

Numbers live in the manifest. This module does not substitute defaults when a
key is missing: a missing key is an invalid config and the caller must not trade.
"""

from dataclasses import dataclass
from typing import Any, Mapping


class ConfigError(ValueError):
    """Raised when strategy_config is incomplete or inconsistent."""


def _require(cfg: Mapping[str, Any], key: str) -> Any:
    if key not in cfg or cfg[key] is None:
        raise ConfigError(f"strategy_config.{key} is required")
    return cfg[key]


def _as_float(cfg: Mapping[str, Any], key: str) -> float:
    raw = _require(cfg, key)
    try:
        value = float(raw)
    except (TypeError, ValueError) as exc:
        raise ConfigError(f"strategy_config.{key} must be numeric") from exc
    if value != value or value in (float("inf"), float("-inf")):
        raise ConfigError(f"strategy_config.{key} must be finite")
    return value


def _as_int(cfg: Mapping[str, Any], key: str) -> int:
    value = _as_float(cfg, key)
    if int(value) != value:
        raise ConfigError(f"strategy_config.{key} must be an integer")
    return int(value)


def _as_symbol_floats(cfg: Mapping[str, Any], key: str, symbols: tuple[str, ...]) -> dict[str, float]:
    raw = _require(cfg, key)
    if not isinstance(raw, Mapping):
        raise ConfigError(f"strategy_config.{key} must be a mapping of symbol to number")
    values: dict[str, float] = {}
    for symbol in symbols:
        if symbol not in raw:
            raise ConfigError(f"strategy_config.{key}.{symbol} is required")
        try:
            number = float(raw[symbol])
        except (TypeError, ValueError) as exc:
            raise ConfigError(f"strategy_config.{key}.{symbol} must be numeric") from exc
        if number <= 0 or number != number or number in (float("inf"), float("-inf")):
            raise ConfigError(f"strategy_config.{key}.{symbol} must be a positive finite number")
        values[symbol] = number
    return values


def _as_bool(cfg: Mapping[str, Any], key: str) -> bool:
    raw = _require(cfg, key)
    if isinstance(raw, bool):
        return raw
    raise ConfigError(f"strategy_config.{key} must be a boolean")


def _as_tuple(cfg: Mapping[str, Any], key: str) -> tuple[str, ...]:
    raw = _require(cfg, key)
    if not isinstance(raw, (list, tuple)) or not raw:
        raise ConfigError(f"strategy_config.{key} must be a non-empty list")
    symbols: list[str] = []
    for item in raw:
        text = str(item or "").strip().upper()
        if not text or "/" in text or ":" in text:
            raise ConfigError(f"strategy_config.{key} has an invalid symbol {item!r}")
        if text not in symbols:
            symbols.append(text)
    return tuple(symbols)


@dataclass(frozen=True)
class Config:
    trading_symbols: tuple[str, ...]
    leverage: int
    max_leverage: int
    margin_budget: float
    fixed_loss_usdt: float
    adx_period: int
    adx_min: float
    atr_period: int
    atr_stop_mult: float
    atr_pct_lookback: int
    atr_pct_low: float
    atr_pct_high: float
    ema_fast: int
    ema_slow: int
    volume_mult: float
    volume_avg_bars: int
    bar_hours: int
    limit_timeout_hours: int
    time_stop_hours: int
    reward_r: float
    max_concurrent: int
    funding_blackout_minutes: int
    funding_against_max: float
    daily_pause_usdt: float
    playbook_stop_usdt: float
    max_consecutive_losses: int
    stale_ticker_seconds: int
    maker_fee: float
    taker_fee: float
    slippage_ticks: int
    min_notional_usdt: float
    shorts_enabled: bool
    walk_forward_split: str
    backtest_start: str
    backtest_end: str
    fee_tier_status: str
    version_label: str
    price_tick: dict[str, float]
    size_step: dict[str, float]
    min_qty: dict[str, float]

    @property
    def applied_leverage(self) -> int:
        return max(1, min(self.leverage, self.max_leverage))


def load_config(strategy_config: Mapping[str, Any] | None) -> Config:
    if not isinstance(strategy_config, Mapping):
        raise ConfigError("strategy_config must be a mapping")
    cfg = strategy_config
    fast = _as_int(cfg, "ema_fast")
    slow = _as_int(cfg, "ema_slow")
    if fast >= slow:
        raise ConfigError("ema_fast must be shorter than ema_slow")
    low = _as_float(cfg, "atr_pct_low")
    high = _as_float(cfg, "atr_pct_high")
    if not 0 <= low < high <= 100:
        raise ConfigError("atr percentile band must satisfy 0 <= low < high <= 100")
    leverage = _as_int(cfg, "leverage")
    max_leverage = _as_int(cfg, "max_leverage")
    if leverage < 1 or max_leverage < 1:
        raise ConfigError("leverage must be at least 1")
    if leverage > max_leverage:
        raise ConfigError("leverage exceeds max_leverage")
    bar_hours = _as_int(cfg, "bar_hours")
    if bar_hours != 1:
        raise ConfigError("v1 only supports 1H bars")
    reward_r = _as_float(cfg, "reward_r")
    if reward_r <= 0:
        raise ConfigError("reward_r must be positive")
    daily_pause = _as_float(cfg, "daily_pause_usdt")
    playbook_stop = _as_float(cfg, "playbook_stop_usdt")
    if playbook_stop > daily_pause:
        raise ConfigError("playbook stop must be at least as strict as the daily pause")
    symbols = _as_tuple(cfg, "trading_symbols")
    return Config(
        trading_symbols=symbols,
        leverage=leverage,
        max_leverage=max_leverage,
        margin_budget=_as_float(cfg, "margin_budget"),
        fixed_loss_usdt=_as_float(cfg, "fixed_loss_usdt"),
        adx_period=_as_int(cfg, "adx_period"),
        adx_min=_as_float(cfg, "adx_min"),
        atr_period=_as_int(cfg, "atr_period"),
        atr_stop_mult=_as_float(cfg, "atr_stop_mult"),
        atr_pct_lookback=_as_int(cfg, "atr_pct_lookback"),
        atr_pct_low=low,
        atr_pct_high=high,
        ema_fast=fast,
        ema_slow=slow,
        volume_mult=_as_float(cfg, "volume_mult"),
        volume_avg_bars=_as_int(cfg, "volume_avg_bars"),
        bar_hours=bar_hours,
        limit_timeout_hours=_as_int(cfg, "limit_timeout_hours"),
        time_stop_hours=_as_int(cfg, "time_stop_hours"),
        reward_r=reward_r,
        max_concurrent=_as_int(cfg, "max_concurrent"),
        funding_blackout_minutes=_as_int(cfg, "funding_blackout_minutes"),
        funding_against_max=_as_float(cfg, "funding_against_max"),
        daily_pause_usdt=daily_pause,
        playbook_stop_usdt=playbook_stop,
        max_consecutive_losses=_as_int(cfg, "max_consecutive_losses"),
        stale_ticker_seconds=_as_int(cfg, "stale_ticker_seconds"),
        maker_fee=_as_float(cfg, "maker_fee"),
        taker_fee=_as_float(cfg, "taker_fee"),
        slippage_ticks=_as_int(cfg, "slippage_ticks"),
        min_notional_usdt=_as_float(cfg, "min_notional_usdt"),
        shorts_enabled=_as_bool(cfg, "shorts_enabled"),
        walk_forward_split=str(_require(cfg, "walk_forward_split")),
        backtest_start=str(_require(cfg, "backtest_start")),
        backtest_end=str(_require(cfg, "backtest_end")),
        fee_tier_status=str(_require(cfg, "fee_tier_status")),
        version_label=str(_require(cfg, "version_label")),
        price_tick=_as_symbol_floats(cfg, "price_tick", symbols),
        size_step=_as_symbol_floats(cfg, "size_step", symbols),
        min_qty=_as_symbol_floats(cfg, "min_qty", symbols),
    )
