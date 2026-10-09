"""Historical path: fetch Bitget 1H perps, replay, write real evidence files."""
import json
import math
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pandas as pd
from getagent import backtest, data, runtime

from . import risk

_INTERVAL = "1h"
_CHUNK_DAYS = 90
_WINDOW_START = datetime(2024, 10, 9, tzinfo=timezone.utc)
_WINDOW_END = datetime(2026, 10, 9, 17, tzinfo=timezone.utc)


def _sanitize(value: Any) -> Any:
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def _ms(stamp: datetime) -> int:
    return int(stamp.timestamp() * 1000)


def _fetch_symbol_bars(symbol: str) -> Any:
    frames = []
    start = _WINDOW_START
    while start < _WINDOW_END:
        end = min(_WINDOW_END, start + timedelta(days=_CHUNK_DAYS))
        bars = data.crypto.futures.kline(
            symbol=symbol,
            interval=_INTERVAL,
            exchange="bitget",
            start_time=_ms(start),
            end_time=_ms(end),
            limit=1000,
            closed_only=True,
        )
        frame = backtest.prepare_frame(bars, datetime_index="date")
        if frame is not None and hasattr(frame, "empty") and not frame.empty:
            frames.append(frame)
        start = end
    if not frames:
        return None
    merged = pd.concat(frames)
    merged = merged.sort_index()
    merged = merged[~merged.index.duplicated(keep="last")]
    return merged


def _spec_with_loaded(spec: dict[str, Any], loaded: list[str]) -> dict[str, Any]:
    filtered = dict(spec)
    instruments = list(spec.get("instruments") or [])
    if not instruments and spec.get("instrument"):
        instruments = [spec["instrument"]]
    keep = []
    loaded_set = {item.upper() for item in loaded}
    for item in instruments:
        raw = str(item.get("raw_symbol") or item.get("symbol") or "").upper()
        ident = str(item.get("id") or raw).upper()
        if raw in loaded_set or ident in loaded_set or any(raw and raw in key.upper() for key in loaded):
            keep.append(item)
    if keep:
        filtered["instruments"] = keep
        filtered.pop("instrument", None)
    return filtered


def _write_outputs(result: Any, margin_budget: float) -> dict[str, Any]:
    out_dir = Path("/workspace/output")
    out_dir.mkdir(parents=True, exist_ok=True)
    raw = dict(getattr(result, "raw", None) or {})
    summary = dict(getattr(result, "summary", None) or raw.get("summary") or {})
    try:
        net_pnl = float(summary.get("net_pnl") or getattr(result, "summary", {}).get("net_pnl") or 0)
    except (TypeError, ValueError):
        net_pnl = 0.0
    starting = float(summary.get("starting_balance") or 10000)
    strategy_return = (net_pnl / margin_budget * 100.0) if margin_budget else 0.0
    raw["net_pnl"] = round(net_pnl, 4)
    raw["total_return_pct"] = round(strategy_return, 4)
    raw["starting_balance"] = starting
    raw.pop("equity_curve", None)
    reports = raw.get("reports")
    if isinstance(reports, dict):
        reports.pop("equity_curve", None)
    (out_dir / "backtest_report.json").write_text(json.dumps(raw, default=str), encoding="utf-8")

    curve = []
    if isinstance(reports, dict):
        curve = reports.get("account") or reports.get("equity") or []
    if not curve:
        curve = [{"timestamp": _WINDOW_START.isoformat(), "value": starting, "nav": 1.0}]
        if net_pnl:
            curve.append(
                {
                    "timestamp": _WINDOW_END.isoformat(),
                    "value": starting + net_pnl,
                    "nav": (starting + net_pnl) / starting if starting else 1.0,
                }
            )
    lines = ["timestamp,value,nav"]
    for point in curve:
        if not isinstance(point, dict):
            continue
        ts = point.get("timestamp") or point.get("ts") or point.get("time") or ""
        value = point.get("value") or point.get("balance") or point.get("equity") or ""
        nav = point.get("nav") or ""
        if value != "" and nav == "" and starting:
            try:
                nav = float(value) / starting
            except (TypeError, ValueError):
                nav = ""
        lines.append(f"{ts},{value},{nav}")
    (out_dir / "equity_curve.csv").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {
        "net_pnl": net_pnl,
        "total_return_pct": strategy_return,
        "starting_balance": starting,
    }


def run() -> None:
    cfg = risk.cfg(runtime.manifest)
    symbols = list(cfg.get("trading_symbols") or runtime.manifest.get("trading_symbols") or [])
    symbols = [str(item).upper() for item in symbols]
    margin_budget = risk.as_float(cfg.get("margin_budget"), 600.0)

    ohlcv: dict[str, Any] = {}
    for symbol in symbols:
        frame = _fetch_symbol_bars(symbol)
        if frame is None:
            continue
        ohlcv[f"{symbol}.BITGET"] = frame

    if not ohlcv:
        runtime.emit_signal(
            action="watch",
            symbol=symbols[0] if symbols else "BTCUSDT",
            confidence=0.0,
            metrics={"rows": 0, "activation_status": "inactive"},
            meta={"reason": "no historical bars returned", "reason_code": "no_bars"},
        )
        return

    spec = _spec_with_loaded(dict(runtime.backtest_spec or {}), list(ohlcv))
    result = backtest.run(ohlcv_data=ohlcv, spec=spec)
    rewritten = _write_outputs(result, margin_budget)
    chart_path = backtest.generate_chart(result)
    summary = getattr(result, "summary", None) or {}
    total_trades = int(getattr(result, "total_trades", 0) or 0)
    metrics = {
        "total_return_pct": _sanitize(rewritten["total_return_pct"]),
        "net_pnl": _sanitize(rewritten["net_pnl"]),
        "starting_balance": rewritten["starting_balance"],
        "sharpe_ratio": _sanitize(getattr(result, "sharpe_ratio", None)),
        "max_drawdown_pct": _sanitize(getattr(result, "max_drawdown_pct", None)),
        "win_rate": _sanitize(getattr(result, "win_rate", None)),
        "total_trades": total_trades,
        "profit_factor": _sanitize(getattr(result, "profit_factor", None)),
        "rows": sum(len(frame) for frame in ohlcv.values()),
        "symbols_loaded": len(ohlcv),
        "activation_status": "inactive",
        "metrics_basis": "strategy",
    }
    runtime.emit_signal(
        action="watch",
        symbol=next(iter(symbols), "BTCUSDT"),
        confidence=_sanitize(getattr(result, "win_rate", 0.0)) or 0.0,
        metrics=metrics,
        meta={
            "chart_path": chart_path,
            "reason_code": "historical_replay",
            "window_start": _WINDOW_START.isoformat(),
            "window_end": _WINDOW_END.isoformat(),
            "summary": summary,
            "verdict": "PENDING" if total_trades < 30 else "see_metrics",
        },
    )
