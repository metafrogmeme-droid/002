"""Historical path for Sleeve A BTC long v1.

Fetches two years of 1H BTCUSDT perpetual bars in sub-90-day chunks, runs the
Nautilus replay three times for the cost-sensitivity grid (zero, live, double
fees), partitions fills into in-sample / out-of-sample segments for the
walk-forward read, and writes the platform backtest output contract:
output/backtest_report.json plus output/equity_curve.csv, then emits the
managed signal. Never imports live trading code.
"""

import copy
import json
import math
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from getagent import backtest, data, runtime

SYMBOL = "BTCUSDT"
INTERVAL = "1h"
EXCHANGE = "bitget"
IS_END_ISO = "2026-04-01T00:00:00"
EXEC_START_ISO = "2024-10-09T00:00:00"
EXEC_END_ISO = "2026-10-01T00:00:00"
CHUNK_DAYS = 35


def _sanitize(value: Any) -> Any:
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def _sanitize_metrics(metrics: dict[str, Any]) -> dict[str, Any]:
    return {key: _sanitize(val) for key, val in metrics.items()}


def _to_ms(iso: str) -> int:
    return int(datetime.fromisoformat(iso).replace(tzinfo=timezone.utc).timestamp() * 1000)


def _fetch_two_years(symbol: str) -> list[dict[str, Any]]:
    start_ms = _to_ms(EXEC_START_ISO)
    end_ms = _to_ms(EXEC_END_ISO)
    records: list[dict[str, Any]] = []
    cursor = start_ms
    while cursor < end_ms:
        chunk_end = min(cursor + CHUNK_DAYS * 24 * 3600 * 1000, end_ms)
        bars = data.crypto.futures.kline(
            symbol=symbol,
            interval=INTERVAL,
            exchange=EXCHANGE,
            limit=1000,
            start_time=cursor,
            end_time=chunk_end,
            closed_only=True,
        )
        chunk = data.to_records(bars)
        if chunk:
            records.extend(chunk)
            last = chunk[-1]
            last_ts = last.get("time") or last.get("timestamp") or last.get("date")
            _ = last_ts
        cursor = chunk_end
    seen: dict[str, dict[str, Any]] = {}
    for row in records:
        key = str(row.get("date") or row.get("time") or row.get("timestamp"))
        seen[key] = row
    ordered = [seen[k] for k in sorted(seen.keys())]
    return ordered


def _clone_spec_with_fees(spec: Any, maker: str, taker: str) -> dict[str, Any]:
    def plain(obj: Any) -> Any:
        if isinstance(obj, dict):
            return {k: plain(v) for k, v in obj.items()}
        if isinstance(obj, (list, tuple)):
            return [plain(v) for v in obj]
        return obj

    spec_dict = plain(dict(spec)) if not isinstance(spec, dict) else copy.deepcopy(spec)
    if isinstance(spec_dict.get("instrument"), dict):
        spec_dict["instrument"]["maker_fee"] = maker
        spec_dict["instrument"]["taker_fee"] = taker
    for inst in spec_dict.get("instruments", []) or []:
        if isinstance(inst, dict):
            inst["maker_fee"] = maker
            inst["taker_fee"] = taker
    return spec_dict


def _extract_trades(raw: Any) -> list[dict[str, Any]]:
    """Best-effort per-trade (timestamp_ms, pnl) list from raw reports."""
    trades: list[dict[str, Any]] = []
    try:
        reports = (raw or {}).get("reports", {}) if isinstance(raw, dict) else {}
    except Exception:
        return trades
    positions = reports.get("positions")
    rows: Any = None
    if isinstance(positions, dict):
        for key in ("data", "rows", "list"):
            if isinstance(positions.get(key), list):
                rows = positions[key]
                break
    elif isinstance(positions, list):
        rows = positions
    if not rows:
        return trades
    for row in rows:
        if not isinstance(row, dict):
            continue
        pnl = row.get("realized_pnl", row.get("pnl", row.get("net_pnl")))
        ts_raw = row.get("close_time", row.get("ts_close", row.get("timestamp", row.get("date"))))
        try:
            pnl_f = float(pnl) if pnl is not None else None
        except (TypeError, ValueError):
            pnl_f = None
        if pnl_f is None:
            continue
        ts_ms: Any = None
        try:
            if isinstance(ts_raw, (int, float)):
                ts_ms = int(ts_raw) if ts_raw > 1e12 else int(ts_raw * 1000)
            elif isinstance(ts_raw, str) and ts_raw:
                parsed = datetime.fromisoformat(ts_raw.replace("Z", "+00:00"))
                ts_ms = int(parsed.timestamp() * 1000)
        except (TypeError, ValueError):
            ts_ms = None
        trades.append({"timestamp_ms": ts_ms, "pnl": pnl_f})
    return trades


def _r_stats(pnls: list[float]) -> dict[str, Any]:
    if not pnls:
        return {"avg_r": None, "expectancy_r": None, "trades": 0}
    losses = [p for p in pnls if p < 0]
    unit = (sum(abs(p) for p in losses) / len(losses)) if losses else None
    if not unit:
        return {"avg_r": None, "expectancy_r": None, "trades": len(pnls)}
    avg_r = (sum(pnls) / len(pnls)) / unit
    return {"avg_r": avg_r, "expectancy_r": avg_r, "trades": len(pnls)}


def _segment_metrics(trades: list[dict[str, Any]], is_end_ms: int) -> dict[str, Any]:
    dated = [t for t in trades if t.get("timestamp_ms") is not None]
    if not dated:
        return {"parseable": False}
    is_pnls = [t["pnl"] for t in dated if t["timestamp_ms"] < is_end_ms]
    oos_pnls = [t["pnl"] for t in dated if t["timestamp_ms"] >= is_end_ms]

    def seg(pnls: list[float]) -> dict[str, Any]:
        if not pnls:
            return {"trades": 0}
        wins = sum(1 for p in pnls if p > 0)
        gross_profit = sum(p for p in pnls if p > 0)
        gross_loss = abs(sum(p for p in pnls if p < 0))
        return {
            "trades": len(pnls),
            "win_rate": wins / len(pnls),
            "net_pnl": sum(pnls),
            "profit_factor": (gross_profit / gross_loss) if gross_loss > 0 else None,
        }

    return {"parseable": True, "in_sample": seg(is_pnls), "out_of_sample": seg(oos_pnls)}


def _write_outputs(raw: Any, starting_balance: float, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    raw_out = copy.deepcopy(raw) if isinstance(raw, dict) else {}
    if isinstance(raw_out.get("reports"), dict):
        raw_out["reports"].pop("equity_curve", None)
    summary = raw_out.get("summary", {}) if isinstance(raw_out, dict) else {}
    try:
        ending = float(summary.get("total_balance", summary.get("ending_balance", starting_balance)))
    except (TypeError, ValueError):
        ending = starting_balance
    net_pnl = ending - starting_balance
    strategy_return_pct = (net_pnl / starting_balance * 100.0) if starting_balance else 0.0
    if isinstance(raw_out, dict):
        raw_out["net_pnl"] = round(net_pnl, 4)
        raw_out["total_return_pct"] = round(strategy_return_pct, 4)
        raw_out["starting_balance"] = starting_balance
    (out_dir / "backtest_report.json").write_text(json.dumps(raw_out, default=str), encoding="utf-8")
    points: list[tuple[str, float]] = []
    account = (raw or {}).get("reports", {}).get("account") if isinstance(raw, dict) else None
    rows_acc: Any = None
    if isinstance(account, dict):
        for key in ("data", "rows", "list", "history"):
            if isinstance(account.get(key), list):
                rows_acc = account[key]
                break
    elif isinstance(account, list):
        rows_acc = account
    if rows_acc:
        for row in rows_acc:
            if not isinstance(row, dict):
                continue
            ts = row.get("timestamp", row.get("date", row.get("time", "")))
            bal = row.get("total_balance", row.get("balance", row.get("value")))
            try:
                points.append((str(ts), float(bal)))
            except (TypeError, ValueError):
                continue
    if not points:
        for t in _extract_trades(raw):
            if t.get("timestamp_ms") is None:
                continue
            ts_iso = datetime.fromtimestamp(t["timestamp_ms"] / 1000, tz=timezone.utc).isoformat()
            points.append((ts_iso, starting_balance + t["pnl"]))
        running = starting_balance
        stepped: list[tuple[str, float]] = []
        for ts_iso, _ in points:
            running = starting_balance
            stepped.append((ts_iso, running))
        cum = starting_balance
        ordered_pts: list[tuple[str, float]] = []
        for trade in sorted(
            [t for t in _extract_trades(raw) if t.get("timestamp_ms") is not None],
            key=lambda x: x["timestamp_ms"],
        ):
            cum += trade["pnl"]
            ts_iso = datetime.fromtimestamp(trade["timestamp_ms"] / 1000, tz=timezone.utc).isoformat()
            ordered_pts.append((ts_iso, cum))
        points = ordered_pts
    lines = ["timestamp,value,nav"]
    for ts_iso, value in points:
        nav = value / starting_balance if starting_balance else 0.0
        lines.append(f"{ts_iso},{value},{nav}")
    if len(lines) == 1:
        lines.append(f"{EXEC_START_ISO},{starting_balance},1.0")
    (out_dir / "equity_curve.csv").write_text("\n".join(lines) + "\n", encoding="utf-8")


def run() -> None:
    cfg = runtime.manifest.get("strategy_config", {}) or {}
    symbol = str((cfg.get("trading_symbols") or [SYMBOL])[0])
    records = _fetch_two_years(symbol)
    replay_frame = backtest.prepare_frame(records, datetime_index="date")
    if replay_frame.empty or len(replay_frame) < 5000:
        runtime.emit_signal(
            action="hold",
            symbol=symbol,
            confidence=0.0,
            metrics={"rows": len(replay_frame)},
            meta={"reason_code": "INSUFFICIENT_HISTORY", "reason": "2y 1H replay requires deeper history"},
        )
        return
    first_ts = str(replay_frame.index.min())
    last_ts = str(replay_frame.index.max())
    instrument_key = f"{symbol}.BINANCE"
    base_spec = runtime.backtest_spec
    result_base = backtest.run(
        ohlcv_data={instrument_key: replay_frame},
        spec=base_spec,
    )
    summary = result_base.summary or {}
    try:
        starting_balance = float(summary.get("starting_balance", 100000) or 100000)
    except (TypeError, ValueError):
        starting_balance = 100000.0
    cost_runs: dict[str, Any] = {"live_1x": result_base}
    for label, maker, taker in (("zero_0x", "0", "0"), ("double_2x", "0.0004", "0.0012")):
        cost_runs[label] = backtest.run(
            ohlcv_data={instrument_key: replay_frame},
            spec=_clone_spec_with_fees(base_spec, maker, taker),
        )
    cost_table = {}
    for label, res in cost_runs.items():
        res_summary = res.summary or {}
        try:
            res_net = float(res_summary.get("net_pnl", 0) or 0)
        except (TypeError, ValueError):
            res_net = 0.0
        cost_table[label] = {
            "net_pnl": res_net,
            "total_trades": res.total_trades,
            "profit_factor": res.profit_factor,
        }
    try:
        base_net = float(summary.get("net_pnl", 0) or 0)
    except (TypeError, ValueError):
        base_net = 0.0
    trades = _extract_trades(result_base.raw)
    r_stats = _r_stats([t["pnl"] for t in trades]) if trades else {"avg_r": None, "expectancy_r": None, "trades": 0}
    is_end_ms = _to_ms(IS_END_ISO)
    segments = _segment_metrics(trades, is_end_ms)
    chart_path = backtest.generate_chart(result_base)
    out_dir = Path("/workspace/output")
    _write_outputs(result_base.raw, starting_balance, out_dir)
    last_bar_ms = int(replay_frame.index.max().timestamp() * 1000)
    total_trades = int(result_base.total_trades or 0)
    verdict = "PENDING"
    if total_trades >= 30 and base_net > 0:
        pf = result_base.profit_factor
        try:
            pf_f = float(pf) if pf is not None else None
        except (TypeError, ValueError):
            pf_f = None
        verdict = "EVIDENCE_POSITIVE" if (pf_f is not None and pf_f >= 1.3) else "EVIDENCE_MIXED"
    elif total_trades < 30:
        verdict = "PENDING_INSUFFICIENT_TRADES"
    metrics = _sanitize_metrics(
        {
            "total_return_pct": result_base.total_return_pct,
            "net_pnl": base_net,
            "starting_balance": summary.get("starting_balance"),
            "sharpe_ratio": result_base.sharpe_ratio,
            "max_drawdown_pct": result_base.max_drawdown_pct,
            "win_rate": result_base.win_rate,
            "total_trades": total_trades,
            "profit_factor": result_base.profit_factor,
            "avg_r": r_stats.get("avg_r"),
            "net_expectancy_r": r_stats.get("expectancy_r"),
            "rows": len(replay_frame),
            "last_bar_ts": last_bar_ms,
        }
    )
    runtime.emit_signal(
        action="long" if (base_net > 0 and total_trades >= 30) else "hold",
        symbol=symbol,
        confidence=_sanitize(result_base.win_rate) or 0.0,
        metrics=metrics,
        meta={
            "chart_path": chart_path,
            "walk_forward_split": {"in_sample": f"{EXEC_START_ISO}/{IS_END_ISO}", "out_of_sample": f"{IS_END_ISO}/{EXEC_END_ISO}"},
            "segments": segments,
            "cost_sensitivity": cost_table,
            "data_window": {"first_bar": first_ts, "last_bar": last_ts, "exchange": EXCHANGE, "interval": INTERVAL},
            "verdict": verdict,
        },
    )
