"""Net-expectancy analytics computed from the real replay trade log.

All functions take the list of closed-trade records produced by
`strategy.PerpTrendStrategy` (fills from the Nautilus engine plus the explicit
funding / slippage cost model) and derive:

* per-trade R multiples, win rate, expectancy, profit factor, max drawdown,
  Sharpe (daily PnL on the margin budget, annualised)
* anchored walk-forward folds (train window / test window in months)
* cost sensitivity at 0x / 1x / 2x of all modelled costs (fees + funding +
  slippage), using the recorded gross PnL of each real trade

Nothing here is simulated or fabricated: every number is a function of the
recorded trades. If a fold has fewer than `min_trades_for_verdict` trades its
verdict is `INSUFFICIENT_TRADES`.
"""

import math
from datetime import datetime, timezone
from typing import Any, Optional

MIN_TRADES_FOR_VERDICT = 30
FORWARD_CRITERIA = {
    "min_live_trades": 30,
    "pass": {"profit_factor_min": 1.3, "sharpe_min": 0.5},
    "fail": {"profit_factor_max": 1.1},
    "rule": "PASS = PF >= 1.3 AND Sharpe >= 0.5 after >= 30 live trades; FAIL = PF <= 1.1 -> stop Playbook",
}

SECONDS_PER_DAY = 86400


def _finite(value: Optional[float]) -> Optional[float]:
    if value is None:
        return None
    try:
        v = float(value)
    except (TypeError, ValueError):
        return None
    return v if math.isfinite(v) else None


def _iso(ts: Optional[int]) -> Optional[str]:
    if ts is None:
        return None
    return datetime.fromtimestamp(int(ts), tz=timezone.utc).isoformat().replace("+00:00", "Z")


def net_with_cost_multiplier(trade: dict[str, Any], multiplier: float) -> float:
    gross = float(trade.get("gross_pnl_usdt", 0.0) or 0.0)
    cost = float(trade.get("total_cost_usdt", 0.0) or 0.0)
    return gross - multiplier * cost


def summarize(
    trades: list[dict[str, Any]],
    *,
    margin_budget: float,
    window_start_ts: Optional[int] = None,
    window_end_ts: Optional[int] = None,
    cost_multiplier: float = 1.0,
) -> dict[str, Any]:
    """Aggregate metrics for one set of trades (already filtered to a window)."""
    n = len(trades)
    out: dict[str, Any] = {
        "trades": n,
        "window_start": _iso(window_start_ts),
        "window_end": _iso(window_end_ts),
        "cost_multiplier": cost_multiplier,
        "verdict": "INSUFFICIENT_TRADES" if n < MIN_TRADES_FOR_VERDICT else None,
    }
    if n == 0:
        out.update(
            {
                "win_rate": None,
                "avg_r": None,
                "expectancy_r": None,
                "expectancy_usdt": None,
                "profit_factor": None,
                "max_drawdown_usdt": 0.0,
                "max_drawdown_pct_of_budget": 0.0,
                "sharpe_daily_annualized": None,
                "net_pnl_usdt": 0.0,
                "gross_pnl_usdt": 0.0,
                "total_costs_usdt": 0.0,
                "return_pct_of_budget": 0.0,
            }
        )
        return out

    pnls = [net_with_cost_multiplier(t, cost_multiplier) for t in trades]
    risks = [float(t.get("risk_usdt") or 0.0) for t in trades]
    rs = [p / r if r > 0 else 0.0 for p, r in zip(pnls, risks)]
    wins = [p for p in pnls if p > 0]
    losses = [p for p in pnls if p < 0]
    gross_win = sum(wins)
    gross_loss = -sum(losses)
    profit_factor = (gross_win / gross_loss) if gross_loss > 0 else (math.inf if gross_win > 0 else None)

    equity = 0.0
    peak = 0.0
    max_dd = 0.0
    ordered = sorted(zip((int(t.get("exit_ts") or 0) for t in trades), pnls))
    for _, p in ordered:
        equity += p
        peak = max(peak, equity)
        max_dd = max(max_dd, peak - equity)

    daily: dict[int, float] = {}
    for ts, p in ordered:
        day = ts // SECONDS_PER_DAY
        daily[day] = daily.get(day, 0.0) + p
    if window_start_ts is not None and window_end_ts is not None and window_end_ts > window_start_ts:
        first_day = window_start_ts // SECONDS_PER_DAY
        last_day = window_end_ts // SECONDS_PER_DAY
    else:
        first_day = min(daily)
        last_day = max(daily)
    day_returns = [daily.get(d, 0.0) / margin_budget for d in range(first_day, last_day + 1)]
    sharpe = None
    if len(day_returns) >= 2:
        mean = sum(day_returns) / len(day_returns)
        var = sum((x - mean) ** 2 for x in day_returns) / (len(day_returns) - 1)
        std = math.sqrt(var)
        sharpe = (mean / std) * math.sqrt(365.0) if std > 0 else None

    net = sum(pnls)
    out.update(
        {
            "win_rate": len(wins) / n,
            "avg_r": sum(rs) / n,
            "expectancy_r": sum(rs) / n,
            "expectancy_usdt": net / n,
            "avg_win_usdt": (gross_win / len(wins)) if wins else None,
            "avg_loss_usdt": (-gross_loss / len(losses)) if losses else None,
            "profit_factor": _finite(profit_factor) if profit_factor is not None else None,
            "profit_factor_is_inf": profit_factor == math.inf,
            "max_drawdown_usdt": max_dd,
            "max_drawdown_pct_of_budget": max_dd / margin_budget * 100.0,
            "sharpe_daily_annualized": _finite(sharpe),
            "net_pnl_usdt": net,
            "gross_pnl_usdt": sum(float(t.get("gross_pnl_usdt", 0.0) or 0.0) for t in trades),
            "total_costs_usdt": sum(float(t.get("total_cost_usdt", 0.0) or 0.0) for t in trades) * cost_multiplier,
            "fees_usdt": sum(float(t.get("fees_usdt", 0.0) or 0.0) for t in trades) * cost_multiplier,
            "funding_usdt": sum(float(t.get("funding_usdt", 0.0) or 0.0) for t in trades) * cost_multiplier,
            "slippage_usdt": sum(float(t.get("slippage_usdt", 0.0) or 0.0) for t in trades) * cost_multiplier,
            "return_pct_of_budget": net / margin_budget * 100.0,
            "calendar_days": len(day_returns),
            "exit_reasons": _count(trades, "exit_reason"),
            "by_symbol": _by_symbol(trades, pnls, rs),
        }
    )
    if out["verdict"] is None:
        out["verdict"] = "POSITIVE_NET_EXPECTANCY" if out["expectancy_r"] > 0 else "NEGATIVE_NET_EXPECTANCY"
    return out


def _count(trades: list[dict[str, Any]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for t in trades:
        value = str(t.get(key))
        counts[value] = counts.get(value, 0) + 1
    return counts


def _by_symbol(trades: list[dict[str, Any]], pnls: list[float], rs: list[float]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for t, p, r in zip(trades, pnls, rs):
        sym = str(t.get("symbol"))
        row = out.setdefault(sym, {"trades": 0, "net_pnl_usdt": 0.0, "sum_r": 0.0, "wins": 0})
        row["trades"] += 1
        row["net_pnl_usdt"] += p
        row["sum_r"] += r
        row["wins"] += 1 if p > 0 else 0
    for row in out.values():
        row["expectancy_r"] = row["sum_r"] / row["trades"] if row["trades"] else None
        row["win_rate"] = row["wins"] / row["trades"] if row["trades"] else None
        row.pop("sum_r", None)
    return out


def _add_months(ts: int, months: int) -> int:
    dt = datetime.fromtimestamp(ts, tz=timezone.utc)
    month_index = dt.month - 1 + months
    year = dt.year + month_index // 12
    month = month_index % 12 + 1
    day = min(dt.day, 28)
    return int(datetime(year, month, day, dt.hour, tzinfo=timezone.utc).timestamp())


def walk_forward(
    trades: list[dict[str, Any]],
    *,
    start_ts: int,
    end_ts: int,
    margin_budget: float,
    train_months: int = 12,
    test_months: int = 3,
) -> dict[str, Any]:
    """Anchored walk-forward segmentation.

    Parameters are frozen a priori (no per-fold optimisation), so every test
    fold is genuinely out-of-sample relative to the author's prior; the train
    window is reported for stability comparison only.
    """
    folds: list[dict[str, Any]] = []
    test_start = _add_months(start_ts, train_months)
    fold_index = 0
    oos_trades: list[dict[str, Any]] = []
    while test_start < end_ts:
        test_end = min(_add_months(test_start, test_months), end_ts)
        train = [t for t in trades if start_ts <= int(t.get("exit_ts") or 0) < test_start]
        test = [t for t in trades if test_start <= int(t.get("exit_ts") or 0) < test_end]
        oos_trades.extend(test)
        folds.append(
            {
                "fold": fold_index,
                "train": summarize(train, margin_budget=margin_budget, window_start_ts=start_ts, window_end_ts=test_start),
                "test": summarize(test, margin_budget=margin_budget, window_start_ts=test_start, window_end_ts=test_end),
            }
        )
        fold_index += 1
        test_start = test_end
    return {
        "scheme": f"anchored, train {train_months}m / test {test_months}m, parameters frozen (no per-fold fitting)",
        "folds": folds,
        "oos_aggregate": summarize(oos_trades, margin_budget=margin_budget, window_start_ts=_add_months(start_ts, train_months), window_end_ts=end_ts),
    }


def cost_sensitivity(trades: list[dict[str, Any]], *, margin_budget: float, start_ts: int, end_ts: int) -> dict[str, Any]:
    rows = {}
    for mult in (0.0, 1.0, 2.0):
        rows[f"{mult:g}x"] = summarize(
            trades,
            margin_budget=margin_budget,
            window_start_ts=start_ts,
            window_end_ts=end_ts,
            cost_multiplier=mult,
        )
    two_x = rows["2x"]
    if two_x["trades"] < MIN_TRADES_FOR_VERDICT:
        decision = "INSUFFICIENT_TRADES"
    elif (two_x["expectancy_r"] or 0.0) <= 0:
        decision = "REJECTED_NEGATIVE_EXPECTANCY_AT_2X_COSTS"
    else:
        decision = "ACCEPTED_POSITIVE_AT_2X_COSTS"
    return {"rows": rows, "decision": decision}


def equity_curve(
    trades: list[dict[str, Any]],
    *,
    starting_value: float,
    first_ts: Optional[int],
    last_ts: Optional[int],
) -> list[dict[str, Any]]:
    """Real closed-trade equity points: start, every exit, and the final bar.

    No interpolation or forward-filling between events.
    """
    points: list[dict[str, Any]] = []
    if first_ts is not None:
        points.append({"timestamp": _iso(first_ts), "value": round(starting_value, 6), "nav": 1.0})
    equity = starting_value
    for t in sorted(trades, key=lambda x: int(x.get("exit_ts") or 0)):
        equity += float(t.get("net_pnl_usdt", 0.0) or 0.0)
        points.append(
            {
                "timestamp": _iso(int(t.get("exit_ts") or 0)),
                "value": round(equity, 6),
                "nav": round(equity / starting_value, 8) if starting_value else None,
            }
        )
    if last_ts is not None and (not points or points[-1]["timestamp"] != _iso(last_ts)):
        points.append({"timestamp": _iso(last_ts), "value": round(equity, 6), "nav": round(equity / starting_value, 8) if starting_value else None})
    return points
