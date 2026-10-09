"""Turn the replay trade ledger into net-of-cost R metrics.

Costs per trade: maker fee on the limit entry, taker fee on every exit (Bitget
preset TP/SL and time-stop closes execute as market orders), one tick of
slippage on each side, and funding paid on every settlement the position was
held through. Cost multiplier ``k`` scales fees, slippage and funding paid;
funding received is never scaled up.
"""

import math
from datetime import datetime, timezone
from statistics import mean, pstdev
from typing import Iterable

DAY_MS = 86_400_000
HOUR_MS = 3_600_000


def funding_paid(rec: dict, funding: list[tuple[int, float]], interval_hours: int) -> tuple[float, int, int]:
    """Funding (USDT, positive = paid) for a long held from fill to exit."""
    start, end = int(rec["fill_ts_ms"]), int(rec["exit_ts_ms"])
    period = interval_hours * HOUR_MS
    s = -(-start // period) * period
    if s == start:
        s += period
    notional = float(rec["fill_price"]) * float(rec["qty"])
    total, n, missing = 0.0, 0, 0
    j = 0
    while s <= end:
        while j + 1 < len(funding) and funding[j + 1][0] <= s:
            j += 1
        if funding and funding[j][0] <= s:
            total += funding[j][1] * notional
        else:
            missing += 1
        n += 1
        s += period
    return total, n, missing


def price_trade(rec: dict, k: float, *, maker: float, taker: float, slip_ticks: int, risk: float,
                funding_usdt: float, pessimistic: bool = False) -> dict:
    entry = float(rec["fill_price"])
    qty = float(rec["qty"])
    exit_px = float(rec["exit_price"])
    reason = rec["exit_reason"]
    if pessimistic and is_ambiguous(rec) and exit_px > float(rec["stop"]):
        exit_px = float(rec["stop"])
        reason = "EXIT_SL"
    gross = (exit_px - entry) * qty
    fees = maker * entry * qty + taker * exit_px * qty
    slip = 2 * slip_ticks * float(rec["tick"]) * qty
    fund = k * funding_usdt if funding_usdt > 0 else funding_usdt
    if k == 0:
        fund = 0.0
    net = gross - k * (fees + slip) - fund
    return {"net": net, "r": net / risk, "gross": gross, "fees": fees * k, "slip": slip * k,
            "funding": fund, "reason": reason}


def is_ambiguous(rec: dict) -> bool:
    if rec["exit_reason"] in ("EXIT_SL", "EXIT_SL_IMMEDIATE"):
        return False
    return bool(rec.get("exit_bar_both_touched")) or bool(rec.get("entry_bar_stop_touched"))


def _max_dd(values: Iterable[float]) -> float:
    peak, dd, cum = 0.0, 0.0, 0.0
    for v in values:
        cum += v
        peak = max(peak, cum)
        dd = min(dd, cum - peak)
    return dd


def summarize(priced: list[dict], start_ms: int, end_ms: int, close_ts: list[int], budget: float) -> dict:
    n = len(priced)
    if n == 0:
        return {"trades": 0, "win_rate": None, "avg_r": None, "net_expectancy_r": None,
                "profit_factor": None, "max_dd_usdt": 0.0, "max_dd_r": 0.0, "sharpe": None,
                "net_pnl_usdt": 0.0, "verdict_eligible": False}
    nets = [t["net"] for t in priced]
    rs = [t["r"] for t in priced]
    wins = [x for x in nets if x > 0]
    losses = [x for x in nets if x <= 0]
    pf = (sum(wins) / abs(sum(losses))) if losses and sum(losses) != 0 else (math.inf if wins else None)
    days = max(1, int((end_ms - start_ms) // DAY_MS))
    daily = [0.0] * days
    for t, ts in zip(priced, close_ts):
        d = int((ts - start_ms) // DAY_MS)
        if 0 <= d < days:
            daily[d] += t["net"]
    rets = [x / budget for x in daily]
    sd = pstdev(rets) if len(rets) > 1 else 0.0
    sharpe = (mean(rets) / sd * math.sqrt(365)) if sd > 0 else None
    return {
        "trades": n,
        "win_rate": round(len(wins) / n, 4),
        "avg_r": round(mean(rs), 4),
        "net_expectancy_r": round(mean(rs), 4),
        "profit_factor": None if pf is None else (round(pf, 3) if math.isfinite(pf) else "inf"),
        "max_dd_usdt": round(_max_dd(nets), 2),
        "max_dd_r": round(_max_dd(rs), 3),
        "sharpe": None if sharpe is None else round(sharpe, 3),
        "net_pnl_usdt": round(sum(nets), 2),
        "verdict_eligible": n >= 30,
    }


def iso(ms: int) -> str:
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def month_start_ms(year: int, month: int) -> int:
    return int(datetime(year, month, 1, tzinfo=timezone.utc).timestamp() * 1000)


def build_report(
    trades: list[dict],
    funding: dict[str, list[tuple[int, float]]],
    *,
    start_ms: int,
    end_ms: int,
    folds: list[tuple[str, int, int]],
    split: tuple[str, int],
    maker: float,
    taker: float,
    slip_ticks: int,
    risk: float,
    budget: float,
    interval_hours: int,
) -> dict:
    trades = [t for t in trades if start_ms <= int(t["signal_close_ms"]) < end_ms]
    fund_info = [funding_paid(t, funding.get(t["symbol"], []), interval_hours) for t in trades]
    close_ts = [int(t["exit_ts_ms"]) for t in trades]

    def priced(k: float, pess: bool = False) -> list[dict]:
        return [
            price_trade(t, k, maker=maker, taker=taker, slip_ticks=slip_ticks, risk=risk,
                        funding_usdt=f[0], pessimistic=pess)
            for t, f in zip(trades, fund_info)
        ]

    p0, p1, p2 = priced(0.0), priced(1.0), priced(2.0)
    p1_pess = priced(1.0, True)

    def subset(sel: list[dict], lo: int, hi: int) -> dict:
        idx = [i for i, t in enumerate(trades) if lo <= int(t["signal_close_ms"]) < hi]
        return summarize([sel[i] for i in idx], lo, hi, [close_ts[i] for i in idx], budget)

    sens = {
        "0x": summarize(p0, start_ms, end_ms, close_ts, budget),
        "1x": summarize(p1, start_ms, end_ms, close_ts, budget),
        "2x": summarize(p2, start_ms, end_ms, close_ts, budget),
    }
    split_name, split_ms = split
    wf = [{"fold": name, "start": iso(lo), "end": iso(hi), **subset(p1, lo, hi)} for name, lo, hi in folds]
    by_symbol = {}
    for sym in sorted({t["symbol"] for t in trades}):
        idx = [i for i, t in enumerate(trades) if t["symbol"] == sym]
        by_symbol[sym] = summarize([p1[i] for i in idx], start_ms, end_ms, [close_ts[i] for i in idx], budget)
    reasons: dict[str, int] = {}
    for t in p1:
        reasons[t["reason"]] = reasons.get(t["reason"], 0) + 1

    exp2 = sens["2x"]["net_expectancy_r"]
    n1 = sens["1x"]["trades"]
    if n1 < 30:
        verdict = "NO_VERDICT_UNDER_30_TRADES"
    elif exp2 is None or exp2 <= 0:
        verdict = "REJECT_NEGATIVE_AT_2X_COSTS"
    elif (sens["1x"]["net_expectancy_r"] or 0) <= 0:
        verdict = "REJECT_NEGATIVE_AT_1X_COSTS"
    else:
        verdict = "CANDIDATE_FOR_FORWARD_TEST"

    equity = []
    cum = 0.0
    ordered = sorted(zip(close_ts, p1), key=lambda x: x[0])
    j = 0
    day = start_ms
    while day <= end_ms:
        while j < len(ordered) and ordered[j][0] < day + DAY_MS:
            cum += ordered[j][1]["net"]
            j += 1
        value = budget + cum
        equity.append({"timestamp": iso(min(day + DAY_MS, end_ms)), "value": round(value, 4),
                       "nav": round(value / budget, 6)})
        day += DAY_MS

    totals = {
        "fees_usdt": round(sum(t["fees"] for t in p1), 2),
        "slippage_usdt": round(sum(t["slip"] for t in p1), 2),
        "funding_usdt": round(sum(t["funding"] for t in p1), 2),
        "gross_usdt": round(sum(t["gross"] for t in p1), 2),
        "funding_settlements": sum(f[1] for f in fund_info),
        "funding_settlements_missing_rate": sum(f[2] for f in fund_info),
    }
    return {
        "window": {"start": iso(start_ms), "end": iso(end_ms)},
        "cost_sensitivity": sens,
        "pessimistic_same_bar_1x": summarize(p1_pess, start_ms, end_ms, close_ts, budget),
        "ambiguous_trades": sum(1 for t in trades if is_ambiguous(t)),
        "in_sample": {"label": f"IS before {split_name}", **subset(p1, start_ms, split_ms)},
        "out_of_sample": {"label": f"OOS from {split_name}", **subset(p1, split_ms, end_ms)},
        "walk_forward": wf,
        "by_symbol": by_symbol,
        "exit_reasons": reasons,
        "cost_totals_1x": totals,
        "verdict": verdict,
        "equity_curve": equity,
        "per_trade_1x": [
            {"symbol": t["symbol"], "signal": iso(int(t["signal_close_ms"])), "fill": iso(int(t["fill_ts_ms"])),
             "exit": iso(int(t["exit_ts_ms"])), "intended": t["limit"], "filled": t["fill_price"],
             "exit_px": t["exit_price"], "qty": t["qty"], "reason": p["reason"],
             "fees": round(p["fees"], 4), "slip": round(p["slip"], 4), "funding": round(p["funding"], 4),
             "net": round(p["net"], 4), "r": round(p["r"], 4)}
            for t, p in zip(trades, p1)
        ],
    }

