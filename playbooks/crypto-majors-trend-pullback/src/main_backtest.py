"""Historical evaluation entry point (runtime.is_historical()).

Flow: fetch real Bitget bars + funding -> indicators -> Nautilus replay via
backtest.run -> ledger -> net-of-cost statistics -> artifacts -> signal.
Never imports getagent.trade.
"""
import copy
import json
import math
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from getagent import backtest, runtime

from . import features, reporting
from .rules import Reason, instrument_rules_from_spec
from .strategy import FEATURE_SIDECAR_DIR, REPLAY_STATE_PATH, REQUIRED_FEATURES

OUTPUT_DIR = Path("/workspace/output")
VENUE = "BITGET"
SIDECAR_COLUMNS = tuple(c for c in REQUIRED_FEATURES if c != "close") + ("close", "funding_rate")


def _write_feature_sidecars(frames: dict[str, pd.DataFrame]) -> None:
    FEATURE_SIDECAR_DIR.mkdir(parents=True, exist_ok=True)
    for symbol, frame in frames.items():
        cols = [c for c in SIDECAR_COLUMNS if c in frame.columns]
        payload = {
            "ts_ns": [int(ts.value) for ts in frame.index],
            "columns": {c: [None if pd.isna(v) else float(v) for v in frame[c].tolist()] for c in cols},
        }
        (FEATURE_SIDECAR_DIR / f"{symbol}.json").write_text(json.dumps(payload), encoding="utf-8")


def _remove_feature_sidecars() -> None:
    if not FEATURE_SIDECAR_DIR.exists():
        return
    for path in FEATURE_SIDECAR_DIR.glob("*.json"):
        path.unlink()
    FEATURE_SIDECAR_DIR.rmdir()


def _params() -> dict[str, Any]:
    cfg = dict(runtime.manifest.get("strategy_config", {}) or {})
    cfg["margin_budget"] = float(cfg.get("margin_budget", "500") or 500)
    return cfg


def _instrument_specs(spec: dict[str, Any]) -> dict[str, dict[str, Any]]:
    items = spec.get("instruments") or ([spec["instrument"]] if spec.get("instrument") else [])
    out: dict[str, dict[str, Any]] = {}
    for item in items:
        symbol = str(item.get("raw_symbol") or item.get("symbol") or str(item.get("id", "")).split(".", 1)[0]).upper()
        out[symbol] = item
    return out


def run() -> None:
    started = features.utc_now()
    params = _params()
    symbols = [str(s).upper() for s in (params.get("trading_symbols") or ["BTCUSDT"])]
    spec = copy.deepcopy(dict(runtime.backtest_spec or {}))
    inst_specs = _instrument_specs(spec)
    exchange = str(params.get("data_exchange", "bitget"))
    backtest_days = int(params.get("backtest_days", 730))
    warmup_days = int(params.get("warmup_days", 45))
    fetch_budget = float(params.get("backtest_fetch_budget_seconds", 95))

    window_end = started.replace(minute=0, second=0, microsecond=0)
    window_start = window_end - timedelta(days=backtest_days)
    fetch_start = window_start - timedelta(days=warmup_days)

    frames: dict[str, pd.DataFrame] = {}
    coverage: dict[str, Any] = {"bars": {}, "funding": {}}
    rules_json: dict[str, Any] = {}
    ticks: dict[str, float] = {}
    for index, symbol in enumerate(symbols):
        if symbol not in inst_specs:
            coverage["bars"][symbol] = {"error": "symbol not declared in backtest.yaml"}
            continue
        # Equal share of the fetch budget per symbol so coverage stays comparable.
        deadline = started + timedelta(seconds=fetch_budget * (index + 1) / len(symbols))
        # Funding first (few, small requests) so a slow kline path never silently
        # drops the funding feature; kline truncation shortens the window instead.
        funding, funding_report = features.fetch_funding_window(
            symbol, exchange=exchange, start=fetch_start, end=window_end, deadline=deadline
        )
        coverage["funding"][symbol] = funding_report
        bars, bar_report = features.fetch_klines_window(
            symbol, exchange=exchange, start=fetch_start, end=window_end, deadline=deadline
        )
        coverage["bars"][symbol] = bar_report
        if bars.empty or len(bars) < int(params["ema_slow_period"]) + 50:
            coverage["bars"][symbol]["dropped"] = "insufficient bars"
            continue
        frame = features.build_replay_frame(bars, funding, params)
        frame = frame[frame.index >= pd.Timestamp(max(window_start, bars.index.min().to_pydatetime()))]
        frames[symbol] = frame
        rules = instrument_rules_from_spec(inst_specs[symbol])
        rules_json[symbol] = {
            "tick": rules.tick, "size_step": rules.size_step, "min_qty": rules.min_qty,
            "min_notional": rules.min_notional, "price_precision": rules.price_precision,
            "size_precision": rules.size_precision,
        }
        ticks[symbol] = rules.tick

    if not frames:
        runtime.emit_signal(
            action="watch", symbol=symbols[0], confidence=0.0,
            metrics={"total_trades": 0, "rows": 0},
            meta={"reason": "no replayable bars returned", "coverage": reporting.sanitize(coverage)},
        )
        return

    # Effective window = intersection actually covered by data (reported honestly).
    eff_start = max(f.index.min() for f in frames.values()).to_pydatetime()
    eff_end = min(f.index.max() for f in frames.values()).to_pydatetime()
    frames = {s: f[(f.index >= pd.Timestamp(eff_start)) & (f.index <= pd.Timestamp(eff_end))] for s, f in frames.items()}
    funding_known = any(f["funding_rate"].notna().any() for f in frames.values())

    # Filter spec to loaded instruments and inject parameters.
    loaded = set(frames)
    items = spec.get("instruments") or [spec["instrument"]]
    spec["instruments"] = [i for i in items if str(i.get("raw_symbol") or i.get("symbol") or "").upper() in loaded]
    spec.pop("instrument", None)
    strategy_cfg = dict(spec.get("strategy", {}).get("config") or {})
    strategy_cfg["params_json"] = json.dumps(reporting.sanitize(params))
    strategy_cfg["instrument_rules_json"] = json.dumps(rules_json)
    spec.setdefault("strategy", {})["config"] = strategy_cfg
    spec.pop("execution", None)  # window already applied to the frames

    if REPLAY_STATE_PATH.exists():
        REPLAY_STATE_PATH.unlink()
    _write_feature_sidecars(frames)
    try:
        result = backtest.run(
            ohlcv_data={f"{symbol}.{VENUE}": frame for symbol, frame in frames.items()},
            spec=spec,
        )
    finally:
        _remove_feature_sidecars()
    chart_path = backtest.generate_chart(result)

    state: dict[str, Any] = {}
    if REPLAY_STATE_PATH.exists():
        state = json.loads(REPLAY_STATE_PATH.read_text(encoding="utf-8"))
        REPLAY_STATE_PATH.unlink()
    ledger = list(state.get("ledger") or [])
    trades = reporting.enrich_trades(ledger, frames, params, ticks)
    margin_budget = float(params["margin_budget"])

    summaries = {
        key: reporting.summarize(trades, frames, margin_budget, key=key, start=eff_start, end=eff_end)
        for key in ("0x", "1x", "2x")
    }
    folds = reporting.fold_report(trades, frames, margin_budget, eff_start, eff_end, folds=4)
    curve = reporting.equity_curve(trades, frames, margin_budget, key="1x", start=eff_start, end=eff_end)
    unresolved = state.get("unresolved_slot")
    if unresolved and unresolved.get("state") == "open" and unresolved.get("fill_px"):
        sym = unresolved["symbol"]
        closes = frames[sym]["close"]
        entry_ts = pd.Timestamp(datetime.fromtimestamp(int(unresolved["fill_ns"]) / 1e9, tz=timezone.utc))
        unreal = (closes[closes.index >= entry_ts] - float(unresolved["fill_px"])) * float(unresolved["fill_qty"])
        curve = curve.add(unreal.reindex(curve.index).fillna(0.0), fill_value=0.0)
    if curve.empty:
        all_index = None
        for f in frames.values():
            all_index = f.index if all_index is None else all_index.union(f.index)
        curve = pd.Series(margin_budget, index=all_index)

    head = summaries["1x"]
    net_pnl = float(head["net_pnl_usdt"] or 0.0)
    by_exit: dict[str, int] = {}
    for t in trades:
        by_exit[t["exit_reason"]] = by_exit.get(t["exit_reason"], 0) + 1
    per_symbol = {
        s: reporting.summarize([t for t in trades if t["symbol"] == s], frames, margin_budget, key="1x", start=eff_start, end=eff_end)
        for s in frames
    }
    engine_summary = dict(result.summary or {})
    forward_criteria = {
        "pass": "PF >= 1.3 AND Sharpe >= 0.5 after >= 30 live trades",
        "fail": "PF <= 1.1 -> stop",
        "status": "PENDING (no live trades yet)",
    }
    cost_sensitivity_verdict = (
        "REJECT (negative net at 2x costs)" if (summaries["2x"]["net_pnl_usdt"] or 0.0) < 0 and head["trades"] >= 30
        else "no verdict (<30 trades)" if head["trades"] < 30
        else "passes 2x cost test"
    )
    validation = {
        "data_source": f"getagent.data crypto.futures.kline / funding_rate, exchange={exchange}, interval=1h (Bitget USDT-FUTURES perpetual bars)",
        "effective_window": {"start": eff_start.isoformat(), "end": eff_end.isoformat(),
                             "days": round((eff_end - eff_start).total_seconds() / 86400.0, 2),
                             "requested_days": backtest_days},
        "coverage": coverage,
        "funding_known": funding_known,
        "funding_gate_active": funding_known,
        "cost_model": {
            "fees": "engine commissions at declared maker/taker (entry limit=maker, TP limit=maker, stop/time-stop market=taker)",
            "slippage": f"{params['slippage_ticks']} tick per taker fill",
            "funding": "as-of funding rate x entry notional at each settlement crossed" if funding_known else "UNAVAILABLE in replay data -> not deducted (degraded)",
        },
        "summary_by_cost_multiplier": summaries,
        "cost_sensitivity_verdict": cost_sensitivity_verdict,
        "folds_fixed_params_no_fitting": folds,
        "per_symbol_1x": per_symbol,
        "exits_by_reason": by_exit,
        "skip_counts": state.get("skip_counts", {}),
        "risk_state_end": state.get("risk_state", {}),
        "unresolved_open_position_at_end": unresolved is not None and unresolved.get("state") == "open",
        "engine_summary": reporting.sanitize(engine_summary),
        "engine_metrics": {
            "total_return_pct_account": result.total_return_pct,
            "sharpe_ratio": result.sharpe_ratio,
            "max_drawdown_pct_account": result.max_drawdown_pct,
            "win_rate": result.win_rate,
            "total_trades_fills": result.total_trades,
            "position_count": result.position_count,
            "profit_factor": result.profit_factor,
        },
        "forward_criteria": forward_criteria,
        "bars_seen": state.get("bars_seen"),
        "ts_is_close_time": state.get("ts_is_close_time"),
        "elapsed_seconds": round((features.utc_now() - started).total_seconds(), 2),
    }

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    raw = dict(result.raw or {})
    raw.pop("equity_curve", None)
    if isinstance(raw.get("reports"), dict):
        raw["reports"] = {k: v for k, v in raw["reports"].items() if k != "equity_curve"}
    raw["net_pnl"] = round(net_pnl, 4)
    raw["total_return_pct"] = round(net_pnl / margin_budget * 100.0, 4)
    raw["max_drawdown_pct"] = head["max_drawdown_pct_of_budget"]
    raw["starting_balance"] = margin_budget
    raw["metrics_basis_note"] = "net_pnl is net of engine fees + modelled slippage + funding (1x); denominator margin_budget"
    (OUTPUT_DIR / "backtest_report.json").write_text(json.dumps(reporting.sanitize(raw), default=str), encoding="utf-8")
    (OUTPUT_DIR / "equity_curve.csv").write_text(
        "\n".join(reporting.curve_to_csv_lines(curve, margin_budget)) + "\n", encoding="utf-8"
    )
    (OUTPUT_DIR / "trade_ledger.json").write_text(json.dumps(reporting.sanitize(trades), default=str), encoding="utf-8")
    (OUTPUT_DIR / "action_log.json").write_text(json.dumps(reporting.sanitize(state.get("action_log", [])), default=str), encoding="utf-8")
    (OUTPUT_DIR / "validation_report.json").write_text(json.dumps(reporting.sanitize(validation), default=str), encoding="utf-8")

    def _f(value: Any) -> Any:
        try:
            v = float(value)
            return v if math.isfinite(v) else None
        except (TypeError, ValueError):
            return None

    metrics = {
        "total_return_pct": _f(net_pnl / margin_budget * 100.0),
        "net_pnl": _f(net_pnl),
        "starting_balance": margin_budget,
        "sharpe_ratio": _f(head["sharpe_daily_annualised"]),
        "max_drawdown_pct": _f(head["max_drawdown_pct_of_budget"]),
        "win_rate": _f(head["win_rate"]),
        "total_trades": int(head["trades"]),
        "profit_factor": _f(head["profit_factor"]),
        "net_expectancy_r": _f(head["net_expectancy_r"]),
        "avg_r": _f(head["avg_r"]),
        "net_pnl_0x": _f(summaries["0x"]["net_pnl_usdt"]),
        "net_pnl_2x": _f(summaries["2x"]["net_pnl_usdt"]),
        "profit_factor_2x": _f(summaries["2x"]["profit_factor"]),
        "effective_days": validation["effective_window"]["days"],
        "funding_known": bool(funding_known),
        "rows": int(sum(len(f) for f in frames.values())),
        "engine_total_return_pct_account": _f(result.total_return_pct),
        "engine_sharpe_ratio": _f(result.sharpe_ratio),
    }
    action = "watch"
    if head["trades"] >= 30 and (head["profit_factor"] or 0) > 1.0 and (summaries["2x"]["net_pnl_usdt"] or 0) > 0:
        action = "long"
    runtime.emit_signal(
        action=action,
        symbol=symbols[0],
        confidence=_f(head["win_rate"]) or 0.0,
        metrics=metrics,
        meta={
            "chart_path": chart_path,
            "effective_window": validation["effective_window"],
            "cost_sensitivity_verdict": cost_sensitivity_verdict,
            "verdict_allowed": head["trades"] >= 30,
            "exits_by_reason": by_exit,
            "skip_counts": state.get("skip_counts", {}),
            "funding_gate_active": funding_known,
            "forward_criteria": forward_criteria,
            "reason_code": Reason.OK if head["trades"] else "NO_TRADES",
        },
    )
