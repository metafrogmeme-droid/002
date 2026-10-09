"""Turn the replay ledger into net-of-cost statistics, folds, and artifacts.

Costs are applied per trade and labelled:
- fees: real engine commissions at the declared maker/taker rates
- slippage: ``slippage_ticks`` x tick x qty on every taker fill (stop / time stop)
- funding: sum of the as-of funding rate at each settlement crossed while in
  the position, times entry notional (long pays positive funding)
All headline figures use the 1x cost multiplier; 0x and 2x are reported for
sensitivity. Nothing here is fitted or fabricated: every number derives from
engine fills plus declared cost rules.
"""
import math
from datetime import datetime, timedelta, timezone
from typing import Any

import numpy as np
import pandas as pd

COST_MULTIPLIERS = (0.0, 1.0, 2.0)


def _settlement_times(start: datetime, end: datetime, interval_hours: int) -> list[datetime]:
    if interval_hours <= 0:
        return []
    anchor = start.replace(minute=0, second=0, microsecond=0)
    while anchor.hour % interval_hours != 0:
        anchor -= timedelta(hours=1)
    times: list[datetime] = []
    cursor = anchor
    while cursor <= end:
        if cursor > start:
            times.append(cursor)
        cursor += timedelta(hours=interval_hours)
    return times


def _asof_rate(frame: pd.DataFrame | None, when: datetime) -> float | None:
    if frame is None or "funding_rate" not in frame.columns or frame.empty:
        return None
    series = frame["funding_rate"].dropna()
    if series.empty:
        return None
    idx = series.index.searchsorted(pd.Timestamp(when), side="right") - 1
    if idx < 0:
        return None
    return float(series.iloc[idx])


def enrich_trades(
    ledger: list[dict[str, Any]],
    frames: dict[str, pd.DataFrame],
    params: dict[str, Any],
    ticks: dict[str, float],
) -> list[dict[str, Any]]:
    interval_hours = int(params["funding_interval_hours"])
    slippage_ticks = float(params["slippage_ticks"])
    enriched: list[dict[str, Any]] = []
    for trade in ledger:
        t = dict(trade)
        symbol = t["symbol"]
        entry = datetime.fromisoformat(t["entry_time"])
        exit_ = datetime.fromisoformat(t["exit_time"])
        tick = float(ticks.get(symbol, 0.0))
        taker_fills = 1 if t.get("exit_taker") else 0
        t["slippage"] = round(slippage_ticks * tick * float(t["qty"]) * taker_fills, 6)
        funding_total = 0.0
        funding_known = True
        for when in _settlement_times(entry, exit_, interval_hours):
            rate = _asof_rate(frames.get(symbol), when)
            if rate is None:
                funding_known = False
                continue
            funding_total += rate * float(t["notional"])
        t["funding"] = round(funding_total, 6)
        t["funding_known"] = funding_known
        cost_1x = float(t["fees"]) + t["slippage"] + t["funding"]
        t["cost_1x"] = round(cost_1x, 6)
        risk = float(t["risk_usdt"]) if float(t["risk_usdt"]) > 0 else float("nan")
        for mult in COST_MULTIPLIERS:
            key = f"{int(mult)}x"
            net = float(t["gross_pnl"]) - mult * cost_1x
            t[f"net_pnl_{key}"] = round(net, 6)
            t[f"r_{key}"] = round(net / risk, 4) if math.isfinite(risk) else None
        enriched.append(t)
    return enriched


def _sharpe_from_curve(curve: pd.Series, margin_budget: float) -> float | None:
    if curve is None or len(curve) < 3:
        return None
    daily = curve.resample("1D").last().dropna()
    if len(daily) < 3:
        return None
    rets = daily.diff().dropna() / margin_budget
    if rets.std(ddof=1) == 0 or not math.isfinite(rets.std(ddof=1)):
        return None
    return float(rets.mean() / rets.std(ddof=1) * math.sqrt(365.0))


def _max_drawdown(curve: pd.Series) -> float:
    if curve is None or curve.empty:
        return 0.0
    running_max = curve.cummax()
    dd = curve - running_max
    return float(-dd.min()) if len(dd) else 0.0


def equity_curve(
    trades: list[dict[str, Any]],
    frames: dict[str, pd.DataFrame],
    margin_budget: float,
    key: str = "1x",
    start: datetime | None = None,
    end: datetime | None = None,
) -> pd.Series:
    """Hourly mark-to-market equity (USDT) starting from margin_budget.

    Realised net PnL (chosen cost multiplier) is booked at exit; the open trade
    is marked at each hourly close using the real bar closes.
    """
    all_index = None
    for frame in frames.values():
        all_index = frame.index if all_index is None else all_index.union(frame.index)
    if all_index is None or len(all_index) == 0:
        return pd.Series(dtype=float)
    if start is not None:
        all_index = all_index[all_index >= pd.Timestamp(start)]
    if end is not None:
        all_index = all_index[all_index <= pd.Timestamp(end)]
    equity = pd.Series(0.0, index=all_index)
    realised = pd.Series(0.0, index=all_index)
    for t in trades:
        exit_ts = pd.Timestamp(t["exit_time"])
        pos = realised.index.searchsorted(exit_ts, side="left")
        if pos < len(realised):
            realised.iloc[pos] += float(t[f"net_pnl_{key}"])
        entry_ts = pd.Timestamp(t["entry_time"])
        closes = frames[t["symbol"]]["close"]
        window = closes[(closes.index >= entry_ts) & (closes.index < exit_ts)]
        if not window.empty:
            unreal = (window - float(t["entry_price"])) * float(t["qty"])
            equity = equity.add(unreal.reindex(all_index).fillna(0.0), fill_value=0.0)
    equity = equity + realised.cumsum() + margin_budget
    return equity


def summarize(
    trades: list[dict[str, Any]],
    frames: dict[str, pd.DataFrame],
    margin_budget: float,
    key: str = "1x",
    start: datetime | None = None,
    end: datetime | None = None,
) -> dict[str, Any]:
    n = len(trades)
    nets = np.array([float(t[f"net_pnl_{key}"]) for t in trades], dtype=float) if n else np.array([])
    rs = np.array([t[f"r_{key}"] for t in trades if t[f"r_{key}"] is not None], dtype=float) if n else np.array([])
    wins = nets[nets > 0] if n else np.array([])
    losses = nets[nets < 0] if n else np.array([])
    curve = equity_curve(trades, frames, margin_budget, key=key, start=start, end=end) if n else pd.Series(dtype=float)
    mdd = _max_drawdown(curve) if n else 0.0
    gross_profit = float(wins.sum()) if len(wins) else 0.0
    gross_loss = float(-losses.sum()) if len(losses) else 0.0
    return {
        "cost_multiplier": key,
        "trades": n,
        "win_rate": round(float((nets > 0).mean()), 4) if n else None,
        "avg_r": round(float(rs.mean()), 4) if len(rs) else None,
        "net_expectancy_r": round(float(rs.mean()), 4) if len(rs) else None,
        "net_pnl_usdt": round(float(nets.sum()), 4) if n else 0.0,
        "profit_factor": round(gross_profit / gross_loss, 4) if gross_loss > 0 else (None if n == 0 else float("inf")),
        "max_drawdown_usdt": round(mdd, 4),
        "max_drawdown_pct_of_budget": round(mdd / margin_budget * 100.0, 4) if margin_budget else None,
        "sharpe_daily_annualised": (lambda s: round(s, 4) if s is not None else None)(_sharpe_from_curve(curve, margin_budget)) if n else None,
        "avg_hold_hours": round(float(np.mean([t["hold_hours"] for t in trades])), 3) if n else None,
        "verdict_allowed": n >= 30,
    }


def fold_report(
    trades: list[dict[str, Any]],
    frames: dict[str, pd.DataFrame],
    margin_budget: float,
    start: datetime,
    end: datetime,
    folds: int = 4,
) -> list[dict[str, Any]]:
    """Sequential, non-overlapping segments with fixed parameters (no fitting).

    This is a fold-wise stability report, not an optimising walk-forward: the
    sandbox time budget does not allow re-fitting per fold, and the Playbook
    parameters are a priori defaults rather than in-sample optima.
    """
    total = (end - start).total_seconds()
    reports = []
    for i in range(folds):
        f_start = start + timedelta(seconds=total * i / folds)
        f_end = start + timedelta(seconds=total * (i + 1) / folds)
        subset = [t for t in trades if f_start <= datetime.fromisoformat(t["exit_time"]) < f_end]
        summary = summarize(subset, frames, margin_budget, key="1x", start=f_start, end=f_end)
        summary.update({"fold": i + 1, "start": f_start.isoformat(), "end": f_end.isoformat()})
        reports.append(summary)
    return reports


def sanitize(value: Any) -> Any:
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, dict):
        return {k: sanitize(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [sanitize(v) for v in value]
    if isinstance(value, (np.floating,)):
        return sanitize(float(value))
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (pd.Timestamp, datetime)):
        return value.isoformat()
    return value


def curve_to_csv_lines(curve: pd.Series, margin_budget: float) -> list[str]:
    lines = ["timestamp,value,nav"]
    for ts, value in curve.items():
        if value is None or not math.isfinite(float(value)):
            continue
        stamp = pd.Timestamp(ts).tz_convert("UTC").strftime("%Y-%m-%dT%H:%M:%S") if pd.Timestamp(ts).tzinfo else pd.Timestamp(ts).strftime("%Y-%m-%dT%H:%M:%S")
        lines.append(f"{stamp},{float(value):.4f},{float(value) / margin_budget:.6f}")
    return lines


def utc(dt: datetime) -> datetime:
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
