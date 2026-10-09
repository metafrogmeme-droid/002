"""Historical evaluation. Metrics come from the replay or stay null.

This module must not import getagent.trade. A missing series is a failed
coverage check, not a zero.
"""

import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from getagent import backtest, runtime

try:
    from .features import DataCoverageError, build_replay_frame
    from .params import ConfigError, load_config
    from .report import activation_verdict, rule_trades, split_by_entry, summarize
    from .risk import ClosedTrade
except ImportError:
    from features import DataCoverageError, build_replay_frame
    from params import ConfigError, load_config
    from report import activation_verdict, rule_trades, split_by_entry, summarize
    from risk import ClosedTrade


OUTPUT = Path("/workspace/output")
HOUR_MS = 60 * 60 * 1000


def run() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    try:
        cfg = load_config(runtime.manifest.get("strategy_config") or {})
    except ConfigError as exc:
        _fail(str(exc))
        return
    start_ms = _iso_ms(cfg.backtest_start)
    end_ms = _iso_ms(cfg.backtest_end)
    frames: dict[str, Any] = {}
    coverage: list[dict[str, Any]] = []
    try:
        for symbol in cfg.trading_symbols:
            frame, cov = build_replay_frame(symbol, start_ms, end_ms)
            frames[f"{symbol}.BITGET"] = frame
            coverage.append(cov)
        result = backtest.run(ohlcv_data=frames, spec=runtime.backtest_spec)
    except DataCoverageError as exc:
        _fail(str(exc), coverage=coverage)
        return
    except Exception as exc:
        _fail(f"{type(exc).__name__}: {exc}", coverage=coverage)
        return
    _finish(cfg, result, coverage, start_ms, end_ms)


def _finish(cfg: Any, result: Any, coverage: list[dict[str, Any]], start_ms: int, end_ms: int) -> None:
    chart_path = ""
    try:
        chart_path = backtest.generate_chart(result) or ""
    except Exception:
        chart_path = ""
    trades = rule_trades(_load_trades())
    shutdowns = [
        trade for trade in _load_trades() if trade.reason_code == "BACKTEST_SHUTDOWN"
    ]
    coverage_ok = _coverage_ok(coverage, start_ms, end_ms)
    full = summarize(trades, 1.0, cfg.margin_budget)
    cost_0 = summarize(trades, 0.0, cfg.margin_budget)
    cost_2 = summarize(trades, 2.0, cfg.margin_budget)
    train, test = split_by_entry(trades, cfg.walk_forward_split)
    train_summary = summarize(train, 1.0, cfg.margin_budget)
    test_summary = summarize(test, 1.0, cfg.margin_budget)
    if not coverage_ok:
        full = _pending_coverage(full)
        cost_0 = _pending_coverage(cost_0)
        cost_2 = _pending_coverage(cost_2)
        train_summary = _pending_coverage(train_summary)
        test_summary = _pending_coverage(test_summary)
    engine_sharpe = _finite(getattr(result, "sharpe_ratio", None))
    verdict, reasons = activation_verdict(
        full=full,
        cost_2x=cost_2,
        fee_tier_status=str(cfg.fee_tier_status),
        engine_sharpe=engine_sharpe,
        live_trades=0,
    )
    author_net = full.get("net_pnl") if full.get("status") == "OK" else None
    author_return = (
        float(author_net) / cfg.margin_budget * 100.0
        if isinstance(author_net, (int, float)) and cfg.margin_budget
        else None
    )
    summary = getattr(result, "summary", {}) or {}
    raw = dict(getattr(result, "raw", {}) or {})
    raw["net_pnl"] = _round(author_net)
    raw["total_return_pct"] = _round(author_return)
    raw["starting_balance"] = cfg.margin_budget
    raw["metrics_basis"] = "strategy"
    raw["author_metrics"] = {
        "full_1x": full,
        "cost_0x": cost_0,
        "cost_2x": cost_2,
        "train_1x": train_summary,
        "test_1x": test_summary,
        "engine_total_trades": getattr(result, "total_trades", None),
        "engine_win_rate": _finite(getattr(result, "win_rate", None)),
        "engine_profit_factor": _finite(getattr(result, "profit_factor", None)),
        "engine_sharpe_ratio": engine_sharpe,
        "engine_max_drawdown_pct": _finite(getattr(result, "max_drawdown_pct", None)),
        "engine_net_pnl": _finite(summary.get("net_pnl") if isinstance(summary, dict) else None),
        "shutdown_flats": len(shutdowns),
        "coverage_ok": coverage_ok,
        "coverage": coverage,
        "fee_tier_status": cfg.fee_tier_status,
        "verdict": verdict,
        "verdict_reasons": reasons,
        "walk_forward_split": cfg.walk_forward_split,
        "prediction": (
            "Test-window net expectancy per trade has the same sign as the "
            "train window if the edge is stable. A sign flip falsifies stability. "
            "This prediction does not claim either sign is positive."
        ),
    }
    reports = raw.get("reports")
    if isinstance(reports, dict):
        reports.pop("equity_curve", None)
    _write_equity(trades, cfg.margin_budget, cfg.backtest_start)
    (OUTPUT / "backtest_report.json").write_text(
        json.dumps(_clean(raw), default=str),
        encoding="utf-8",
    )
    (OUTPUT / "data_coverage.json").write_text(
        json.dumps(_clean({"coverage_ok": coverage_ok, "symbols": coverage}), default=str),
        encoding="utf-8",
    )
    runtime.emit_signal(
        action="watch",
        symbol=cfg.trading_symbols[0],
        confidence=0.0,
        metrics=_clean(
            {
                "metrics_basis": "strategy",
                "verdict": verdict,
                "total_trades": full.get("trades"),
                "win_rate": full.get("win_rate"),
                "avg_r": full.get("avg_r"),
                "expectancy_r": full.get("expectancy_r"),
                "expectancy_r_0x": cost_0.get("expectancy_r"),
                "expectancy_r_2x": cost_2.get("expectancy_r"),
                "profit_factor": full.get("profit_factor"),
                "max_drawdown_pct": full.get("max_drawdown_pct"),
                "sharpe_ratio": engine_sharpe,
                "net_pnl": author_net,
                "total_return_pct": author_return,
                "starting_balance": cfg.margin_budget,
                "coverage_ok": coverage_ok,
                "fee_tier_status": cfg.fee_tier_status,
                "live_trades": 0,
            }
        ),
        meta={
            "chart_path": chart_path,
            "verdict_reasons": reasons,
            "version_label": cfg.version_label,
            "walk_forward_split": cfg.walk_forward_split,
        },
    )


def _coverage_ok(coverage: list[dict[str, Any]], start_ms: int, end_ms: int) -> bool:
    if not coverage:
        return False
    for item in coverage:
        first = item.get("kline_first_ms")
        last = item.get("kline_last_ms")
        fund_first = item.get("funding_first_ms")
        fund_last = item.get("funding_last_ms")
        if not all(isinstance(value, int) for value in (first, last, fund_first, fund_last)):
            return False
        if first > start_ms + HOUR_MS or last < end_ms - 2 * HOUR_MS:
            return False
        if fund_first > start_ms + 24 * HOUR_MS or fund_last < end_ms - 24 * HOUR_MS:
            return False
    return True


def _pending_coverage(summary: dict[str, Any]) -> dict[str, Any]:
    kept_trades = summary.get("trades")
    return {
        "trades": kept_trades,
        "win_rate": None,
        "avg_r": None,
        "expectancy_r": None,
        "profit_factor": None,
        "max_drawdown_pct": None,
        "net_pnl": None,
        "status": "PENDING",
        "pending_reason": "kline or funding coverage does not span the declared 2y window",
        "provisional_status": summary.get("status"),
    }


def _load_trades() -> list[ClosedTrade]:
    path = OUTPUT / "closed_trades.json"
    if not path.exists():
        return []
    raw = json.loads(path.read_text(encoding="utf-8"))
    trades: list[ClosedTrade] = []
    if not isinstance(raw, list):
        return []
    for row in raw:
        if not isinstance(row, dict):
            continue
        trades.append(
            ClosedTrade(
                symbol=str(row.get("symbol") or ""),
                entry_ts=str(row.get("entry_ts") or ""),
                exit_ts=str(row.get("exit_ts") or ""),
                side=str(row.get("side") or ""),
                qty=float(row.get("qty") or 0),
                entry_price=float(row.get("entry_price") or 0),
                exit_price=float(row.get("exit_price") or 0),
                entry_fee_rate=float(row.get("entry_fee_rate") or 0),
                exit_fee_rate=float(row.get("exit_fee_rate") or 0),
                slippage_usdt=float(row.get("slippage_usdt") or 0),
                funding_usdt=float(row.get("funding_usdt") or 0),
                funding_known=bool(row.get("funding_known")),
                risk_usdt=float(row.get("risk_usdt") or 0),
                reason_code=str(row.get("reason_code") or ""),
            )
        )
    return trades


def _write_equity(trades: list[ClosedTrade], start_equity: float, start_iso: str) -> None:
    points = [("timestamp,value,nav",)]
    lines = ["timestamp,value,nav"]
    equity = start_equity
    lines.append(f"{start_iso},{equity},{1.0 if start_equity else 0.0}")
    for trade in trades:
        net = trade.net(1.0)
        if net is None:
            continue
        equity += net
        nav = equity / start_equity if start_equity else 0.0
        lines.append(f"{trade.exit_ts},{equity},{nav}")
    if len(lines) == 1:
        return
    (OUTPUT / "equity_curve.csv").write_text("\n".join(lines) + "\n", encoding="utf-8")
    del points


def _fail(reason: str, coverage: list[dict[str, Any]] | None = None) -> None:
    payload = {
        "net_pnl": None,
        "total_return_pct": None,
        "author_metrics": {
            "status": "PENDING",
            "pending_reason": reason,
            "coverage": coverage or [],
            "verdict": "do_not_activate",
        },
    }
    (OUTPUT / "backtest_report.json").write_text(json.dumps(payload), encoding="utf-8")
    symbol = "BTCUSDT"
    try:
        symbols = (runtime.manifest.get("trading_symbols") or ["BTCUSDT"])
        if symbols:
            symbol = str(symbols[0])
    except Exception:
        symbol = "BTCUSDT"
    runtime.emit_signal(
        action="watch",
        symbol=symbol,
        confidence=0.0,
        metrics={"verdict": "do_not_activate", "total_trades": None, "expectancy_r": None},
        meta={"pending_reason": reason},
    )


def _iso_ms(value: str) -> int:
    text = value.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(text)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return int(parsed.timestamp() * 1000)


def _finite(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(number):
        return None
    return number


def _round(value: Any) -> float | None:
    number = _finite(value)
    if number is None:
        return None
    return round(number, 4)


def _clean(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _clean(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_clean(item) for item in value]
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value
