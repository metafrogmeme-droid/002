"""Historical replay: 2y 1H Bitget BTCUSDT perp, walk-forward split, net costs."""

import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from getagent import backtest, runtime

from . import spec
from . import strategy as strategy_mod
from .features import build_replay_frame, warmup_start

WINDOW_START = datetime(2024, 10, 9, tzinfo=timezone.utc)
WINDOW_END = datetime(2026, 10, 9, tzinfo=timezone.utc)
IS_END = datetime(2026, 4, 9, tzinfo=timezone.utc)
INSTRUMENT_KEY = "BTCUSDT.BITGET"
OUT_DIR = Path("/workspace/output")


def _sanitize(value: Any) -> Any:
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def _cfg() -> dict[str, Any]:
    return runtime.manifest.get("strategy_config", {}) or {}


def _parse_time(value: object) -> datetime | None:
    text = str(value or "")
    if not text:
        return None
    try:
        if text.endswith("Z"):
            text = text.replace("Z", "+00:00")
        stamp = datetime.fromisoformat(text)
        if stamp.tzinfo is None:
            stamp = stamp.replace(tzinfo=timezone.utc)
        return stamp
    except ValueError:
        return None


def _trade_metrics(trips: list[dict[str, Any]]) -> dict[str, Any]:
    if not trips:
        return {
            "trades": 0,
            "win_rate": None,
            "avg_R": None,
            "net_expectancy_R": None,
            "profit_factor": None,
            "verdict": "NO_VERDICT_UNDER_30_TRADES",
            "data": "strategy_round_trips_net_of_listed_fees_funding_1tick_stop",
        }
    nets = [float(item.get("net_usdt") or 0.0) for item in trips]
    rs = [float(item.get("r") or 0.0) for item in trips]
    wins = [value for value in nets if value > 0]
    losses = [value for value in nets if value < 0]
    win_rate = len(wins) / len(trips)
    avg_r = sum(rs) / len(rs)
    expectancy_r = sum(rs) / len(rs)
    gross_win = sum(wins)
    gross_loss = abs(sum(losses))
    profit_factor = (gross_win / gross_loss) if gross_loss > 0 else None
    verdict = "NO_VERDICT_UNDER_30_TRADES" if len(trips) < 30 else "PENDING_FORWARD_LIVE"
    return {
        "trades": len(trips),
        "win_rate": _sanitize(win_rate),
        "avg_R": _sanitize(avg_r),
        "net_expectancy_R": _sanitize(expectancy_r),
        "profit_factor": _sanitize(profit_factor),
        "verdict": verdict,
        "data": "strategy_round_trips_net_of_listed_fees_funding_1tick_stop",
    }


def _cost_sensitivity(trips: list[dict[str, Any]]) -> dict[str, Any]:
    if not trips:
        return {"0x": None, "1x": None, "2x": None, "reject_at_2x": "PENDING"}
    rows = {}
    for label, scale in (("0x", 0.0), ("1x", 1.0), ("2x", 2.0)):
        rs = []
        for item in trips:
            gross = float(item.get("gross_usdt") or 0.0)
            fees = float(item.get("fees_usdt") or 0.0) * scale
            funding = float(item.get("funding_usdt") or 0.0) * scale
            risk = float(_cfg().get("risk_usdt") or 15)
            rs.append((gross - fees - funding) / risk if risk else 0.0)
        rows[label] = {
            "net_expectancy_R": _sanitize(sum(rs) / len(rs)),
            "trades": len(rs),
        }
    two = rows["2x"]["net_expectancy_R"]
    rows["reject_at_2x"] = True if two is not None and two < 0 else False if two is not None else "PENDING"
    return rows


def _extract_equity(result: Any, starting: float) -> list[dict[str, Any]]:
    raw = result.raw or {}
    reports = raw.get("reports") or {}
    candidates = [
        reports.get("equity_curve"),
        reports.get("equity"),
        reports.get("account"),
        raw.get("equity_curve"),
    ]
    points: list[dict[str, Any]] = []
    for candidate in candidates:
        if not isinstance(candidate, list) or not candidate:
            continue
        for item in candidate:
            if not isinstance(item, dict):
                continue
            ts = item.get("timestamp") or item.get("time") or item.get("ts")
            value = item.get("value") or item.get("equity") or item.get("balance")
            if ts is None or value is None:
                continue
            try:
                number = float(value)
            except (TypeError, ValueError):
                continue
            nav = number / starting if starting else None
            points.append({"timestamp": str(ts), "value": number, "nav": nav})
        if points:
            return points
    return points


def _write_outputs(result: Any, metrics: dict[str, Any], starting: float, net_pnl: float) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    raw = dict(result.raw or {})
    raw.pop("equity_curve", None)
    reports = dict(raw.get("reports") or {})
    reports.pop("equity_curve", None)
    raw["reports"] = reports
    raw["net_pnl"] = round(net_pnl, 4)
    raw["total_return_pct"] = round((net_pnl / starting) * 100.0, 4) if starting else None
    raw["starting_balance"] = starting
    raw["metrics_basis"] = "strategy"
    raw["net_expectancy"] = metrics
    (OUT_DIR / "backtest_report.json").write_text(json.dumps(raw, default=str), encoding="utf-8")

    points = _extract_equity(result, starting)
    if not points:
        points = [
            {
                "timestamp": WINDOW_START.isoformat(),
                "value": starting,
                "nav": 1.0,
            },
            {
                "timestamp": WINDOW_END.isoformat(),
                "value": starting + net_pnl,
                "nav": (starting + net_pnl) / starting if starting else None,
            },
        ]
    lines = ["timestamp,value,nav"]
    for point in points:
        lines.append(f"{point.get('timestamp','')},{point.get('value','')},{point.get('nav','')}")
    (OUT_DIR / "equity_curve.csv").write_text("\n".join(lines) + "\n", encoding="utf-8")


def run() -> None:
    cfg = _cfg()
    symbol = str((cfg.get("trading_symbols") or ["BTCUSDT"])[0])
    if symbol != "BTCUSDT":
        runtime.emit_signal(
            action="watch",
            symbol=symbol,
            confidence=0.0,
            metrics={"rows": 0},
            meta={
                "reason": "OFFICIAL_REPLAY_IS_BTCUSDT_ONLY",
                "universe": list(spec.UNIVERSE),
                "note": "ETHUSDT/SOLUSDT share the live sleeve but not the 2y official replay package",
            },
        )
        return

    fetch_start = warmup_start(WINDOW_START)
    replay_frame = build_replay_frame(symbol, fetch_start, WINDOW_END)
    if replay_frame is None or getattr(replay_frame, "empty", True):
        runtime.emit_signal(
            action="watch",
            symbol=symbol,
            confidence=0.0,
            metrics={"rows": 0},
            meta={"reason": "no historical bars returned", "exchange": "bitget"},
        )
        return
    if "funding_rate" not in replay_frame.columns:
        raise RuntimeError("funding_rate missing from replay frame; refuse silent fill")

    instrument_key = f"{symbol}.BITGET"
    result = backtest.run(
        ohlcv_data={instrument_key: replay_frame},
        spec=runtime.backtest_spec,
    )
    chart_path = backtest.generate_chart(result)
    trips = list(strategy_mod.ROUND_TRIPS)
    full = _trade_metrics(trips)
    is_trips = [item for item in trips if (_parse_time(item.get("time")) or WINDOW_START) < IS_END]
    oos_trips = [item for item in trips if (_parse_time(item.get("time")) or WINDOW_START) >= IS_END]
    cost = _cost_sensitivity(trips)

    summary = result.summary or {}
    try:
        engine_net = float(summary.get("net_pnl", 0) or 0)
    except (TypeError, ValueError):
        engine_net = 0.0
    strategy_net = sum(float(item.get("net_usdt") or 0.0) for item in trips)
    margin_budget = float(cfg.get("margin_budget") or 500)
    last_bar_ts = None
    try:
        last_bar_ts = int(replay_frame.index.max().timestamp() * 1000)
    except Exception:
        last_bar_ts = None

    metrics = {
        "total_return_pct": _sanitize((strategy_net / margin_budget) * 100.0 if margin_budget else None),
        "net_pnl": _sanitize(strategy_net),
        "engine_net_pnl": _sanitize(engine_net),
        "starting_balance": margin_budget,
        "sharpe_ratio": _sanitize(result.sharpe_ratio),
        "max_drawdown_pct": _sanitize(result.max_drawdown_pct),
        "win_rate": full.get("win_rate"),
        "total_trades": full.get("trades"),
        "profit_factor": full.get("profit_factor"),
        "avg_R": full.get("avg_R"),
        "net_expectancy_R": full.get("net_expectancy_R"),
        "rows": len(replay_frame),
        "last_bar_ts": last_bar_ts,
        "walk_forward": {
            "split": "IS 2024-10-09..2026-04-08 / OOS 2026-04-09..2026-10-09",
            "in_sample": _trade_metrics(is_trips),
            "out_of_sample": _trade_metrics(oos_trips),
        },
        "cost_sensitivity": cost,
        "engine_fill_count": result.total_trades,
        "forward_pass_rule": "PASS = PF>=1.3 AND Sharpe>=0.5 after >=30 live trades; FAIL = PF<=1.1",
        "displayed_roi_ignored": True,
        "data_label": {
            "ohlcv": "bitget 1h crypto.futures.kline",
            "funding": "bitget crypto.futures.funding_rate 4h asof-joined",
            "fees": "contract listed maker 0.0002 / taker 0.0006; user tier PENDING",
            "engine_metrics": "Nautilus account reports",
            "expectancy": "strategy round-trips net of listed fees, funding, 1-tick stop",
        },
    }
    _write_outputs(result, metrics, margin_budget, strategy_net)
    runtime.emit_signal(
        action="watch",
        symbol=symbol,
        confidence=_sanitize(full.get("win_rate")) or 0.0,
        metrics={key: _sanitize(value) if not isinstance(value, (dict, list)) else value for key, value in metrics.items()},
        meta={
            "chart_path": chart_path,
            "sleeve": spec.SLEEVE,
            "cluster": spec.CLUSTER,
            "window": f"{WINDOW_START.date()} / {WINDOW_END.date()}",
            "verdict": full.get("verdict"),
            "reject_at_2x_costs": cost.get("reject_at_2x"),
        },
    )
