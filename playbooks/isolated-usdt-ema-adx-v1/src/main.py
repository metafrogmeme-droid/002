"""Managed entry point for the frozen v1 EMA-ADX Playbook."""

import copy
import json
import math
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from getagent import backtest, data, runtime


SYMBOL_TO_INSTRUMENT = {
    "BTCUSDT": "BTCUSDT.BITGET",
    "ETHUSDT": "ETHUSDT.BITGET",
    "SOLUSDT": "SOLUSDT.BITGET",
}


def _finite(value: Any) -> Any:
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def _fetch_two_year_bars(symbol: str) -> Any:
    spec = runtime.backtest_spec.get("execution", {}) or {}
    start = datetime.fromisoformat(
        str(spec["start"]).replace("Z", "+00:00")
    ).astimezone(timezone.utc)
    end = datetime.fromisoformat(
        str(spec["end"]).replace("Z", "+00:00")
    ).astimezone(timezone.utc)
    records: dict[str, dict[str, Any]] = {}
    cursor = start
    # Forty-day pages stay below the endpoint's 1000-row cap for hourly bars.
    while cursor < end:
        chunk_end = min(cursor + timedelta(days=40), end)
        response = data.crypto.futures.kline(
            symbol=symbol,
            interval="1h",
            exchange="bitget",
            limit=1000,
            start_time=int(cursor.timestamp() * 1000),
            end_time=int(chunk_end.timestamp() * 1000),
            closed_only=True,
        )
        for row in data.to_records(response):
            timestamp = str(row.get("date") or row.get("time") or "")
            if timestamp:
                records[timestamp] = row
        cursor = chunk_end
    frame = backtest.prepare_frame(list(records.values()))
    if frame.empty:
        raise RuntimeError(f"managed Bitget kline path returned no rows for {symbol}")
    frame = frame[(frame.index >= start) & (frame.index <= end)]
    expected_hours = int((end - start).total_seconds() // 3600)
    if len(frame) < int(expected_hours * 0.95):
        raise RuntimeError(
            f"{symbol} historical coverage incomplete: "
            f"rows={len(frame)} expected_at_least={int(expected_hours * 0.95)}"
        )
    return frame


def _cost_spec(multiplier: float) -> dict[str, Any]:
    spec = copy.deepcopy(dict(runtime.backtest_spec))
    instruments = spec.get("instruments", [])
    for instrument in instruments:
        instrument["maker_fee"] = str(0.0002 * multiplier)
        instrument["taker_fee"] = str(0.0006 * multiplier)
    return spec


def _result_metrics(result: Any, risk_usdt: float) -> dict[str, Any]:
    summary = result.summary or {}
    trades = int(result.total_trades or 0)
    net_pnl = float(summary.get("net_pnl", 0.0) or 0.0)
    net_expectancy_r = (
        net_pnl / (trades * risk_usdt) if trades > 0 else None
    )
    return {
        "trades": trades,
        "win_rate": _finite(result.win_rate),
        "average_r": _finite(net_expectancy_r),
        "net_expectancy_r": _finite(net_expectancy_r),
        "profit_factor": _finite(result.profit_factor),
        "max_drawdown_pct": _finite(result.max_drawdown_pct),
        "sharpe_ratio": _finite(result.sharpe_ratio),
        "net_pnl_usdt": net_pnl,
    }


def _write_real_outputs(result: Any, report: dict[str, Any]) -> str:
    output = Path("/workspace/output")
    output.mkdir(parents=True, exist_ok=True)
    raw = copy.deepcopy(result.raw or {})
    raw.pop("equity_curve", None)
    reports = raw.get("reports")
    curve_source: Any = None
    if isinstance(reports, dict):
        curve_source = reports.pop("equity_curve", None)
    raw["validation"] = report
    raw["net_pnl"] = report["cost_sensitivity"]["1x"]["net_pnl_usdt"]
    raw["metrics_basis"] = "strategy"
    (output / "backtest_report.json").write_text(
        json.dumps(raw, default=str), encoding="utf-8"
    )

    points: list[dict[str, Any]] = []
    if hasattr(curve_source, "to_dict"):
        try:
            points = curve_source.to_dict(orient="records")
        except TypeError:
            points = []
    elif isinstance(curve_source, list):
        points = [point for point in curve_source if isinstance(point, dict)]
    elif isinstance(curve_source, dict):
        candidate = curve_source.get("points", [])
        if isinstance(candidate, list):
            points = [point for point in candidate if isinstance(point, dict)]
    if points:
        lines = ["timestamp,value,nav"]
        for point in points:
            timestamp = point.get("timestamp") or point.get("time") or ""
            value = point.get("value") or point.get("equity") or ""
            nav = point.get("nav") or ""
            lines.append(f"{timestamp},{value},{nav}")
        (output / "equity_curve.csv").write_text(
            "\n".join(lines) + "\n", encoding="utf-8"
        )
    return backtest.generate_chart(result)


def _run_historical() -> None:
    cfg = runtime.manifest.get("strategy_config", {}) or {}
    symbols = list(cfg.get("trading_symbols") or [])
    if symbols != ["BTCUSDT", "ETHUSDT", "SOLUSDT"]:
        raise RuntimeError("v1 symbol universe is frozen")
    frames = {
        SYMBOL_TO_INSTRUMENT[symbol]: _fetch_two_year_bars(symbol)
        for symbol in symbols
    }
    risk_usdt = float(cfg.get("risk_usdt", 15))
    runs: dict[str, Any] = {}
    for label, multiplier in (("0x", 0.0), ("1x", 1.0), ("2x", 2.0)):
        result = backtest.run(ohlcv_data=frames, spec=_cost_spec(multiplier))
        runs[label] = result
    sensitivity = {
        label: _result_metrics(result, risk_usdt)
        for label, result in runs.items()
    }
    enough_trades = sensitivity["1x"]["trades"] >= 30
    two_x_positive = (sensitivity["2x"]["net_expectancy_r"] or 0.0) > 0.0
    report = {
        "data_evidence": {
            instrument: {
                "rows": len(frame),
                "first_timestamp": frame.index.min().isoformat(),
                "last_timestamp": frame.index.max().isoformat(),
            }
            for instrument, frame in frames.items()
        },
        "cost_sensitivity": sensitivity,
        "walk_forward": {
            "protocol": "12-month train / 3-month test, rolling every 3 months",
            "result": "PENDING",
            "reason": "managed run executes frozen v1; fold orchestration is not exposed",
        },
        "funding": {
            "result": "PENDING",
            "reason": "Nautilus managed result does not expose historical funding debits",
        },
        "verdict": (
            "PENDING"
            if not enough_trades or report_funding_pending()
            else "REJECT" if not two_x_positive else "PASS"
        ),
        "verdict_reason": (
            "No positive-net verdict is allowed until trade count, walk-forward, "
            "and funding-cost evidence are complete."
        ),
    }
    chart_path = _write_real_outputs(runs["1x"], report)
    runtime.emit_signal(
        action="watch",
        symbol="BTCUSDT",
        confidence=0.0,
        metrics={
            "net_pnl_usdt": sensitivity["1x"]["net_pnl_usdt"],
            "trades": sensitivity["1x"]["trades"],
            "win_rate": sensitivity["1x"]["win_rate"],
            "average_r": sensitivity["1x"]["average_r"],
            "net_expectancy_r": sensitivity["1x"]["net_expectancy_r"],
            "profit_factor": sensitivity["1x"]["profit_factor"],
            "max_drawdown_pct": sensitivity["1x"]["max_drawdown_pct"],
            "sharpe_ratio": sensitivity["1x"]["sharpe_ratio"],
        },
        meta={
            "verdict": report["verdict"],
            "cost_sensitivity": sensitivity,
            "funding": report["funding"],
            "walk_forward": report["walk_forward"],
            "chart_path": chart_path,
        },
    )


def report_funding_pending() -> bool:
    return True


def _run_live() -> None:
    # The documented SDK can attach isolated TP/SL to an entry order, but it
    # does not expose authoritative daily realized PnL/loss-streak accounting,
    # a documented 60-second source timestamp, or guaranteed order-state
    # persistence for the four-hour cancellation clock. v1 therefore fails
    # closed instead of claiming these protections or placing an order.
    runtime.emit_signal_or_follow(
        action="hold",
        symbol="",
        confidence=0.0,
        metrics={"live_execution_enabled": False},
        meta={
            "reason": "required account safety controls are not verifiable",
            "pending": [
                "daily realized PnL circuit breakers",
                "consecutive realized-loss halt",
                "60-second source freshness proof",
                "durable four-hour pending-order cancellation",
                "unknown-position anomaly classification",
            ],
            "action_log_schema": [
                "timestamp",
                "symbol",
                "side",
                "intended_price",
                "fill_price",
                "fees",
                "funding",
                "reason",
            ],
        },
        execute_trade=None,
        reason_code="SAFETY_CONTROLS_PENDING",
        reason_text="NO TRADE: mandatory account protections cannot be verified.",
        reason_locale="en",
    )


def run() -> None:
    if runtime.is_historical():
        _run_historical()
        return
    if runtime.is_live():
        _run_live()
        return
    raise ValueError(f"unsupported evaluation_mode={runtime.evaluation_mode!r}")


if __name__ == "__main__":
    run()
