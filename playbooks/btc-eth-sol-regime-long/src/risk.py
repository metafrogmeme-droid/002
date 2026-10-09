"""Sizing and risk-state rules shared by live execution and replay."""
import math
from dataclasses import dataclass
from typing import Any, Mapping, Optional

HARD_MAX_LEVERAGE = 5.0

RISK_DEFAULTS: dict[str, Any] = {
    "risk_per_trade_usdt": 15.0,
    "max_leverage": 5,
    "margin_budget": "1500",
    "max_concurrent": 3,
    "stop_atr_mult": 1.5,
    "tp_r_multiple": 2.0,
    "time_stop_hours": 8,
    "entry_ttl_hours": 4,
    "daily_pause_usdt": 30.0,
    "daily_stop_usdt": 40.0,
    "max_consecutive_losses": 5,
    "funding_block_minutes": 15,
    "funding_max_against_8h": 0.0003,
    "stale_data_seconds": 60,
    "allow_short": False,
}


def rv(cfg: Mapping[str, Any], key: str) -> Any:
    value = cfg.get(key)
    return RISK_DEFAULTS[key] if value is None else value


def leverage_cap(cfg: Mapping[str, Any]) -> float:
    return min(float(rv(cfg, "max_leverage")), HARD_MAX_LEVERAGE)


def round_to_step(value: float, step: float) -> float:
    return round(round(value / step) * step, 12)


def floor_to_step(value: float, step: float) -> float:
    return round(math.floor(value / step + 1e-9) * step, 12)


@dataclass
class OrderPlan:
    side: str
    limit: float
    stop: float
    tp: float
    qty: float
    risk_px: float
    notional: float
    margin: float
    reason_code: str

    @property
    def ok(self) -> bool:
        return self.reason_code == "ENTRY_SIGNAL"


def plan_entry(
    *,
    side: str,
    close: float,
    atr: float,
    tick: float,
    size_step: float,
    min_qty: float,
    cfg: Mapping[str, Any],
) -> OrderPlan:
    """Limit at the signal close, stop at stop_atr_mult*ATR, TP at tp_r_multiple*R,
    qty = risk_per_trade / stop distance (floored, so the loss at the stop never exceeds it)."""
    limit = round_to_step(close, tick)
    dist = float(rv(cfg, "stop_atr_mult")) * atr
    r_mult = float(rv(cfg, "tp_r_multiple"))
    if side == "long":
        stop = round_to_step(limit - dist, tick)
        risk_px = limit - stop
        tp = round_to_step(limit + r_mult * risk_px, tick)
    else:
        stop = round_to_step(limit + dist, tick)
        risk_px = stop - limit
        tp = round_to_step(limit - r_mult * risk_px, tick)
    if not (risk_px > 0 and math.isfinite(risk_px)):
        return OrderPlan(side, limit, stop, tp, 0.0, risk_px, 0.0, 0.0, "QTY_BELOW_MIN")
    qty = floor_to_step(float(rv(cfg, "risk_per_trade_usdt")) / risk_px, size_step)
    notional = qty * limit
    lev = leverage_cap(cfg)
    margin = notional / lev
    slot_margin = float(rv(cfg, "margin_budget")) / int(rv(cfg, "max_concurrent"))
    if qty < min_qty or qty <= 0:
        return OrderPlan(side, limit, stop, tp, qty, risk_px, notional, margin, "QTY_BELOW_MIN")
    if margin > slot_margin:
        return OrderPlan(side, limit, stop, tp, qty, risk_px, notional, margin, "SIZE_EXCEEDS_LEVERAGE_CAP")
    return OrderPlan(side, limit, stop, tp, qty, risk_px, notional, margin, "ENTRY_SIGNAL")


@dataclass
class RiskState:
    day: int = -1
    daily_realized: float = 0.0
    consecutive_losses: int = 0
    paused_day: int = -1
    latched_halt: str = ""

    def roll(self, day: int) -> None:
        if day != self.day:
            self.day = day
            self.daily_realized = 0.0

    def record_close(self, day: int, net_pnl: float, cfg: Mapping[str, Any]) -> Optional[str]:
        """Update state after a realised trade. Returns a new halt/pause reason code, if any."""
        self.roll(day)
        self.daily_realized += net_pnl
        self.consecutive_losses = self.consecutive_losses + 1 if net_pnl < 0 else 0
        if self.consecutive_losses >= int(rv(cfg, "max_consecutive_losses")):
            self.latched_halt = self.latched_halt or "HALT_CONSECUTIVE_LOSSES"
            return "HALT_CONSECUTIVE_LOSSES"
        if self.daily_realized <= -float(rv(cfg, "daily_stop_usdt")):
            self.latched_halt = self.latched_halt or "PLAYBOOK_STOP_DAILY_LOSS"
            return "PLAYBOOK_STOP_DAILY_LOSS"
        if self.daily_realized <= -float(rv(cfg, "daily_pause_usdt")) and self.paused_day != day:
            self.paused_day = day
            return "DAILY_PAUSE"
        return None

    def entry_block_reason(self, day: int) -> Optional[str]:
        self.roll(day)
        if self.latched_halt:
            return self.latched_halt
        if self.paused_day == day:
            return "DAILY_PAUSE"
        return None

    def to_dict(self) -> dict[str, Any]:
        return {"day": self.day, "daily_realized": self.daily_realized,
                "consecutive_losses": self.consecutive_losses, "paused_day": self.paused_day,
                "latched_halt": self.latched_halt}

    @classmethod
    def from_dict(cls, d: Mapping[str, Any]) -> "RiskState":
        return cls(int(d.get("day", -1)), float(d.get("daily_realized", 0.0)),
                   int(d.get("consecutive_losses", 0)), int(d.get("paused_day", -1)),
                   str(d.get("latched_halt", "")))
