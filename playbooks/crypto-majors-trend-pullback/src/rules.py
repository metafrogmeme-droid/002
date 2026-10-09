"""Pure, side-effect-free decision rules shared by replay and live execution.

Every gate returns a stable reason code so the per-action log can explain why
an entry was taken or skipped. No I/O, no SDK calls, no randomness.
"""
import math
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


class Reason:
    OK = "OK"
    SIGNAL_INVALID = "SIGNAL_INVALID"          # NaN / warm-up / failed indicator -> no trade
    NO_TREND = "NO_TREND"                      # ADX below threshold
    DI_BEARISH = "DI_BEARISH"                  # -DI >= +DI
    BELOW_SLOW_EMA = "BELOW_SLOW_EMA"          # close under long-horizon trend
    VOL_RANK_LOW = "VOL_RANK_LOW"              # ATR%% percentile too low (dead market)
    VOL_RANK_HIGH = "VOL_RANK_HIGH"            # ATR%% percentile too high (panic regime)
    OVEREXTENDED = "OVEREXTENDED"              # price too far above pullback level
    FUNDING_WINDOW = "FUNDING_WINDOW"          # inside +/-15 min of an 8h settlement
    FUNDING_COST = "FUNDING_COST"              # expected funding over hold > 0.1R
    FUNDING_UNKNOWN = "FUNDING_UNKNOWN"        # funding data missing (gate disabled, reported)
    SLOT_OCCUPIED = "SLOT_OCCUPIED"            # cluster slot busy (pending order or open position)
    DAILY_PAUSE = "DAILY_PAUSE"                # daily realised <= pause threshold
    DAILY_STOP = "DAILY_STOP"                  # daily realised <= hard-stop threshold
    LOSS_STREAK_HALT = "LOSS_STREAK_HALT"      # consecutive-loss halt active
    SIZING_FAIL = "SIZING_FAIL"                # below exchange minimums after quantisation
    LIQUIDITY_SPREAD = "LIQUIDITY_SPREAD"      # spread above cap (live only)
    LIQUIDITY_VOLUME = "LIQUIDITY_VOLUME"      # 24h volume below floor (live only)
    DATA_STALE = "DATA_STALE"                  # feed older than allowed (live only)
    FOREIGN_POSITION = "FOREIGN_POSITION"      # position this Playbook did not open
    ENTRY_PLACED = "ENTRY_PLACED"
    ENTRY_FILLED = "ENTRY_FILLED"
    ENTRY_EXPIRED = "ENTRY_EXPIRED"            # unfilled limit cancelled after max age
    STOP_HIT = "STOP_HIT"
    TP_HIT = "TP_HIT"
    TIME_STOP = "TIME_STOP"
    HARD_STOP = "HARD_STOP"                    # daily hard stop reached -> user must stop Playbook
    EXECUTION_ERROR = "EXECUTION_ERROR"
    NOT_FOLLOW_TRADE = "NOT_FOLLOW_TRADE"


@dataclass
class InstrumentRules:
    tick: float
    size_step: float
    min_qty: float
    min_notional: float
    price_precision: int
    size_precision: int


@dataclass
class EntryPlan:
    symbol: str
    limit_price: float
    stop_price: float
    tp_price: float
    qty: float
    notional: float
    margin: float
    leverage: int
    stop_distance: float
    risk_usdt: float            # realised risk at stop after quantisation / caps
    target_risk_usdt: float
    atr: float
    adx: float
    sizing_capped: bool
    expected_funding_usdt: float
    funding_rate: float | None
    reasons: list[str] = field(default_factory=list)


def _is_bad(value: Any) -> bool:
    try:
        return value is None or not math.isfinite(float(value))
    except (TypeError, ValueError):
        return True


def floor_to_step(value: float, step: float, precision: int) -> float:
    if step <= 0:
        return round(value, precision)
    return round(math.floor(value / step + 1e-9) * step, precision)


def in_funding_window(decision_time: datetime, interval_hours: int, window_minutes: int) -> bool:
    """True when decision_time is within +/-window of a settlement (00:00 UTC anchored)."""
    if interval_hours <= 0:
        return False
    seconds_into_day = decision_time.hour * 3600 + decision_time.minute * 60 + decision_time.second
    period = interval_hours * 3600
    offset = seconds_into_day % period
    distance = min(offset, period - offset)
    return distance <= window_minutes * 60


def regime_check(row: dict[str, Any], params: dict[str, Any]) -> str:
    """Return Reason.OK when the long-only trend regime is active, else the blocking reason."""
    needed = ("close", "ema_fast", "ema_slow", "atr", "adx", "plus_di", "minus_di", "atr_pct_rank")
    if any(_is_bad(row.get(key)) for key in needed):
        return Reason.SIGNAL_INVALID
    if float(row["adx"]) < float(params["adx_min"]):
        return Reason.NO_TREND
    if float(row["plus_di"]) <= float(row["minus_di"]):
        return Reason.DI_BEARISH
    if float(row["close"]) <= float(row["ema_slow"]):
        return Reason.BELOW_SLOW_EMA
    rank = float(row["atr_pct_rank"])
    if rank < float(params["atr_rank_min"]):
        return Reason.VOL_RANK_LOW
    if rank > float(params["atr_rank_max"]):
        return Reason.VOL_RANK_HIGH
    if float(row["close"]) - float(row["ema_fast"]) > float(params["max_extension_atr"]) * float(row["atr"]):
        return Reason.OVEREXTENDED
    return Reason.OK


def build_entry_plan(
    *,
    symbol: str,
    row: dict[str, Any],
    params: dict[str, Any],
    rules: InstrumentRules,
    decision_time: datetime,
    funding_rate: float | None,
    funding_known: bool,
) -> tuple[EntryPlan | None, str]:
    """Full entry evaluation: regime -> funding gates -> price levels -> sizing."""
    regime = regime_check(row, params)
    if regime != Reason.OK:
        return None, regime

    interval_hours = int(params["funding_interval_hours"])
    if in_funding_window(decision_time, interval_hours, int(params["funding_window_minutes"])):
        return None, Reason.FUNDING_WINDOW

    close = float(row["close"])
    atr = float(row["atr"])
    stop_mult = float(params["stop_atr_mult"])
    tp_r = float(params["take_profit_r"])
    leverage = int(params["leverage"])
    target_risk = float(params["risk_per_trade_usdt"])
    margin_budget = float(params["margin_budget"])

    # Pullback entry: rest a bid at the fast EMA, or at the close if price is already below it.
    limit_price = floor_to_step(min(close, float(row["ema_fast"])), rules.tick, rules.price_precision)
    if limit_price <= 0:
        return None, Reason.SIGNAL_INVALID
    stop_distance = stop_mult * atr
    stop_price = floor_to_step(limit_price - stop_distance, rules.tick, rules.price_precision)
    tp_price = floor_to_step(limit_price + tp_r * stop_distance, rules.tick, rules.price_precision)
    if stop_price <= 0 or stop_price >= limit_price or tp_price <= limit_price:
        return None, Reason.SIGNAL_INVALID

    qty = target_risk / stop_distance
    capped = False
    max_notional = margin_budget * leverage
    if qty * limit_price > max_notional:
        qty = max_notional / limit_price
        capped = True
    qty = floor_to_step(qty, rules.size_step, rules.size_precision)
    notional = qty * limit_price
    if qty < rules.min_qty or qty <= 0 or notional < rules.min_notional:
        return None, Reason.SIZING_FAIL
    realised_risk = qty * (limit_price - stop_price)

    hold_hours = float(params["time_stop_hours"])
    expected_funding = 0.0
    if funding_known and funding_rate is not None and not _is_bad(funding_rate):
        periods = hold_hours / float(interval_hours) if interval_hours else 0.0
        expected_funding = float(funding_rate) * notional * periods
        if expected_funding > float(params["max_funding_r"]) * realised_risk:
            return None, Reason.FUNDING_COST
    reasons = [Reason.OK]
    if not funding_known:
        reasons.append(Reason.FUNDING_UNKNOWN)
    if capped:
        reasons.append("SIZE_CAPPED_BY_MARGIN_BUDGET")

    plan = EntryPlan(
        symbol=symbol,
        limit_price=limit_price,
        stop_price=stop_price,
        tp_price=tp_price,
        qty=qty,
        notional=round(notional, 4),
        margin=round(notional / leverage, 4),
        leverage=leverage,
        stop_distance=round(limit_price - stop_price, rules.price_precision),
        risk_usdt=round(realised_risk, 4),
        target_risk_usdt=target_risk,
        atr=atr,
        adx=float(row["adx"]),
        sizing_capped=capped,
        expected_funding_usdt=round(expected_funding, 6),
        funding_rate=None if funding_rate is None or _is_bad(funding_rate) else float(funding_rate),
        reasons=reasons,
    )
    return plan, Reason.OK


@dataclass
class RiskState:
    """Daily / streak circuit breakers. Identical semantics in replay and live."""

    day_key: str = ""
    daily_realised: float = 0.0
    consecutive_losses: int = 0
    halt_until_ms: int = 0
    hard_stop_events: int = 0
    pause_events: int = 0
    streak_halt_events: int = 0

    def roll_day(self, now: datetime) -> None:
        key = now.strftime("%Y-%m-%d")
        if key != self.day_key:
            self.day_key = key
            self.daily_realised = 0.0

    def register_close(self, now: datetime, net_pnl: float, params: dict[str, Any]) -> list[str]:
        self.roll_day(now)
        self.daily_realised += net_pnl
        events: list[str] = []
        if net_pnl < 0:
            self.consecutive_losses += 1
        elif net_pnl > 0:
            self.consecutive_losses = 0
        if self.consecutive_losses >= int(params["max_consecutive_losses"]):
            cooldown_ms = int(float(params["halt_cooldown_hours"]) * 3_600_000)
            self.halt_until_ms = int(now.timestamp() * 1000) + cooldown_ms
            self.consecutive_losses = 0
            self.streak_halt_events += 1
            events.append(Reason.LOSS_STREAK_HALT)
        if self.daily_realised <= -abs(float(params["daily_stop_usdt"])):
            self.hard_stop_events += 1
            events.append(Reason.HARD_STOP)
        elif self.daily_realised <= -abs(float(params["daily_pause_usdt"])):
            self.pause_events += 1
            events.append(Reason.DAILY_PAUSE)
        return events

    def entry_block_reason(self, now: datetime, params: dict[str, Any]) -> str:
        self.roll_day(now)
        if int(now.timestamp() * 1000) < self.halt_until_ms:
            return Reason.LOSS_STREAK_HALT
        if self.daily_realised <= -abs(float(params["daily_stop_usdt"])):
            return Reason.DAILY_STOP
        if self.daily_realised <= -abs(float(params["daily_pause_usdt"])):
            return Reason.DAILY_PAUSE
        return Reason.OK

    def to_dict(self) -> dict[str, Any]:
        return {
            "day_key": self.day_key,
            "daily_realised": round(self.daily_realised, 6),
            "consecutive_losses": self.consecutive_losses,
            "halt_until_ms": self.halt_until_ms,
            "hard_stop_events": self.hard_stop_events,
            "pause_events": self.pause_events,
            "streak_halt_events": self.streak_halt_events,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any] | None) -> "RiskState":
        state = cls()
        if not payload:
            return state
        for key in ("day_key",):
            setattr(state, key, str(payload.get(key, "") or ""))
        state.daily_realised = float(payload.get("daily_realised", 0.0) or 0.0)
        for key in ("consecutive_losses", "halt_until_ms", "hard_stop_events", "pause_events", "streak_halt_events"):
            setattr(state, key, int(payload.get(key, 0) or 0))
        return state


def instrument_rules_from_spec(spec: dict[str, Any]) -> InstrumentRules:
    """Build quantisation rules from a backtest.yaml instrument block."""
    price_precision = int(spec.get("price_precision", 2))
    size_precision = int(spec.get("size_precision", 4))
    return InstrumentRules(
        tick=float(spec.get("price_increment", 10 ** -price_precision)),
        size_step=float(spec.get("size_increment", 10 ** -size_precision)),
        min_qty=float(spec.get("lot_size", spec.get("size_increment", 10 ** -size_precision))),
        min_notional=float(spec.get("min_notional", 5.0)),
        price_precision=price_precision,
        size_precision=size_precision,
    )
