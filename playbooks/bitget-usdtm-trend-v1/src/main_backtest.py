"""Historical evaluation entry for bitget-usdtm-trend-v1.

Fetches real Bitget 1h bars (and settlement funding rates), replays the
strategy in the managed engine, then derives net-of-cost R-based metrics from
the strategy's own trade ledger. No numbers are fabricated: if data is missing
the run fails loudly instead of degrading silently.
"""
import json
import math
from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from getagent import backtest, runtime

try:
    from . import logic
    from . import features
except ImportError:  # loaded as a top-level module
    import logic  # type: ignore[no-redef]
    import features  # type: ignore[no-redef]

HOUR_MS = logic.HOUR_MS
DAY_MS = logic.DAY_MS


def _plain(obj: Any) -> Any:
    if isinstance(obj, Mapping):
        return {str(k): _plain(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_plain(v) for v in obj]
    return obj


def _clean(obj: Any) -> Any:
    if isinstance(obj, float) and not math.isfinite(obj):
        return None
    if isinstance(obj, dict):
        return {k: _clean(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_clean(v) for v in obj]
    return obj


def _window(p: Any) -> tuple[int, int]:
    end = logic.parse_iso_ms(p.trade_end) if p.trade_end else logic.floor_hour_ms(int(datetime.now(timezone.utc).timestamp() * 1000))
    start = logic.parse_iso_ms(p.trade_start) if p.trade_start else logic.add_months(end, -24)
    if end <= start:
        raise ValueError("trade_end must be after trade_start")
    return start, end


def _load_ledger() -> dict[str, Any]:
    path = Path("output") / "playbook_raw.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    try:
        from . import strategy as strat
    except ImportError:
        import strategy as strat  # type: ignore[no-redef]
    if strat.RESULTS:
        return dict(strat.RESULTS)
    raise RuntimeError("strategy produced no ledger (neither output/playbook_raw.json nor in-process RESULTS)")


def _equity_csv(trades: list[dict[str, Any]], start_ms: int, equity: float) -> str:
    lines = ["timestamp,value,nav", f"{logic.iso(start_ms)},{equity:.4f},1.0"]
    cum = 0.0
    for t in sorted(trades, key=lambda x: x["exit_ts_ms"]):
        cum += t["net_pnl"]
        lines.append(f"{logic.iso(t['exit_ts_ms'])},{equity + cum:.4f},{(equity + cum) / equity:.6f}")
    return "\n".join(lines) + "\n"


def _metrics(trades: list[dict[str, Any]], p: Any, start_ms: int, end_ms: int) -> dict[str, Any]:
    return logic.compute_metrics(trades, equity_basis=p.equity_basis, start_ms=start_ms, end_ms=end_ms)


def run() -> None:
    cfg = dict(runtime.manifest.get("strategy_config", {}) or {})
    p = logic.load_params(cfg)
    start_ms, end_ms = _window(p)
    data_start = start_ms - int(p.warmup_days) * DAY_MS
    mult = float(p.cost_multiplier)

    frames: dict[str, Any] = {}
    coverage: dict[str, Any] = {}
    funding_used: dict[str, Any] = {}
    for symbol in p.symbols:
        bars = features.fetch_klines(symbol, data_start, end_ms)
        coverage[symbol] = features.check_coverage(symbol, bars, data_start, end_ms)
        funding = features.fetch_funding(symbol, data_start, end_ms)
        if funding is None and p.require_funding_data:
            raise features.DataError(
                f"{symbol}: no settlement funding-rate rows from the data endpoint; "
                "refusing to report results that are not net of funding (probe the endpoint, see docs/validation-protocol.md)"
            )
        funding_used[symbol] = None if funding is None else {
            "symbol_used": funding.attrs.get("symbol_used"), "rows": int(len(funding)),
        }
        frames[f"{symbol}.BITGET"] = features.build_replay_frame(bars, funding)

    spec = _plain(runtime.backtest_spec)
    spec.setdefault("strategy", {}).setdefault("config", {})["params_json"] = json.dumps(cfg, default=str)
    instruments = spec.get("instruments") or [spec["instrument"]]
    spec.pop("instrument", None)
    spec["instruments"] = [i for i in instruments if i["id"] in frames]
    for inst in spec["instruments"]:
        for key in ("maker_fee", "taker_fee"):
            inst[key] = format(float(inst[key]) * mult, ".10f").rstrip("0").rstrip(".") or "0"

    Path("output").mkdir(parents=True, exist_ok=True)
    (Path("output") / "playbook_raw.json").unlink(missing_ok=True)
    result = backtest.run(ohlcv_data=frames, spec=spec)
    chart_path = backtest.generate_chart(result)
    ledger = _load_ledger()

    trades = [t for t in ledger["trades"] if start_ms <= t["entry_ts_ms"] < end_ms]
    pooled = _metrics(trades, p, start_ms, end_ms)
    sensitivity = {
        f"{m}x_repriced": _metrics(logic.reprice_trades(trades, m), p, start_ms, end_ms)
        for m in (0.0, 1.0, 2.0)
    }
    wf_rows = []
    oos: list[dict[str, Any]] = []
    for w in logic.walk_forward_windows(start_ms, end_ms, int(p.wf_train_months), int(p.wf_test_months), int(p.wf_step_months)):
        tr = logic.trades_in(trades, w["train_start"], w["train_end"])
        te = logic.trades_in(trades, w["test_start"], w["test_end"])
        oos.extend(te)
        wf_rows.append({
            "train": {"start": logic.iso(w["train_start"]), "end": logic.iso(w["train_end"]),
                      **_metrics(tr, p, w["train_start"], w["train_end"])},
            "test": {"start": logic.iso(w["test_start"]), "end": logic.iso(w["test_end"]),
                     **_metrics(te, p, w["test_start"], w["test_end"])},
        })
    oos_span = (wf_rows and (logic.parse_iso_ms(wf_rows[0]["test"]["start"]), logic.parse_iso_ms(wf_rows[-1]["test"]["end"]))) or (start_ms, end_ms)
    oos_pooled = _metrics(oos, p, oos_span[0], oos_span[1])

    expectancy_2x = sensitivity["2.0x_repriced"]["expectancy_r_net"]
    verdict = "INSUFFICIENT_TRADES_NO_VERDICT"
    if oos_pooled["trades"] >= 30:
        verdict = "REJECT_NEGATIVE_EXPECTANCY_AT_2X_COST" if (expectancy_2x is not None and expectancy_2x < 0) else "PASS_COST_SENSITIVITY_GATE"
    report = {
        "param_hash": ledger.get("param_hash"),
        "window": {"start": logic.iso(start_ms), "end": logic.iso(end_ms), "warmup_days": int(p.warmup_days)},
        "cost_multiplier_applied": mult,
        "pooled_all_trades": pooled,
        "cost_sensitivity_repriced_same_trades": sensitivity,
        "walk_forward": {
            "train_months": int(p.wf_train_months), "test_months": int(p.wf_test_months),
            "step_months": int(p.wf_step_months), "windows": wf_rows,
            "pooled_out_of_sample": oos_pooled,
            "note": "v1 has no fitted parameters; train windows are in-sample reference only.",
        },
        "cost_sensitivity_verdict_on_pooled_oos": verdict,
        "reason_counts": ledger.get("reason_counts"),
        "regime_counts": ledger.get("regime_counts"),
        "risk_events": ledger.get("risk_events"),
        "halts": ledger.get("halts"),
        "open_at_end_excluded": ledger.get("open_at_end_excluded"),
        "funding_modelled": ledger.get("funding_modelled"),
        "funding_source": funding_used,
        "data_coverage": coverage,
        "assumptions": {
            "bar_ts_convention": p.bar_ts_convention,
            "fees": "per-symbol Bitget public default tier (user tier PENDING)",
            "slippage_ticks_per_fill": p.slippage_ticks,
            "equity_basis_usdt": p.equity_basis,
        },
    }
    (Path("output") / "playbook_actions.json").write_text(
        json.dumps(_clean({"fields": list(logic.LOG_FIELDS), "records": ledger.get("logs", []),
                           "dropped": ledger.get("logs_dropped", 0)}), default=str), encoding="utf-8")
    (Path("output") / "playbook_trades.json").write_text(json.dumps(_clean(trades), default=str), encoding="utf-8")
    (Path("output") / "equity_curve.csv").write_text(_equity_csv(trades, start_ms, p.equity_basis), encoding="utf-8")

    raw = dict(result.raw or {})
    reports = raw.get("reports")
    if isinstance(reports, dict):
        reports.pop("equity_curve", None)
    net_pnl = float(pooled.get("net_pnl") or 0.0)
    overrides = {
        "engine_net_pnl": raw.get("net_pnl"),
        "engine_total_return_pct": raw.get("total_return_pct"),
        "net_pnl": round(net_pnl, 4),
        "total_return_pct": round(net_pnl / p.equity_basis * 100.0, 4),
        "starting_balance": p.equity_basis,
        "max_drawdown_pct": pooled.get("max_drawdown_pct_of_equity"),
        "sharpe_ratio": pooled.get("sharpe_daily_annualised"),
        "win_rate": pooled.get("win_rate"),
        "total_trades": pooled["trades"],
        "profit_factor": pooled.get("profit_factor"),
        "metrics_basis": "strategy",
    }
    raw.update(overrides)
    raw["playbook_report"] = report
    (Path("output") / "backtest_report.json").write_text(json.dumps(_clean(raw), default=str), encoding="utf-8")

    signal_metrics = _clean({**overrides, "expectancy_r_net": pooled.get("expectancy_r_net"),
                             "avg_r_gross": pooled.get("avg_r_gross"), "verdict": verdict})
    runtime.emit_signal(
        action="watch",
        symbol=p.symbols[0],
        confidence=0.0,
        metrics=signal_metrics,
        meta={"chart_path": chart_path, "param_hash": ledger.get("param_hash"),
              "window": report["window"], "funding_modelled": ledger.get("funding_modelled"),
              "note": "historical evaluation only; not a trade recommendation"},
    )


if __name__ == "__main__":
    run()
