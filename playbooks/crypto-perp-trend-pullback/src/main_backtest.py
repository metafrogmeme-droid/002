"""Historical replay: Bitget 1H bars + funding -> Nautilus -> net-of-cost R report."""

import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from getagent import backtest, runtime

from . import ledger
from .market_data import load_history
from .signals import Params

OUT = Path("output")


def _clean(value: Any) -> Any:
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, dict):
        return {k: _clean(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_clean(v) for v in value]
    return value


def _plain(obj: Any) -> Any:
    return json.loads(json.dumps(obj, default=str))


def _clock() -> float:
    return datetime.now(timezone.utc).timestamp()


def _data_sources(coverage: dict, led: dict) -> dict:
    starts = {s: v.get("funding_bitget_from") for s, v in coverage.get("symbols", {}).items()}
    return {
        "signals_and_fills": "Bitget USDT-M perpetual 1H klines (getagent.data, exchange=bitget)",
        "fees": "Bitget public contract config base tier: maker 0.02% entry, taker 0.06% every exit",
        "slippage": "1 tick per side on every fill",
        "funding": "Bitget funding history from the dates below; Binance USDT-M funding as proxy before",
        "funding_bitget_from": starts,
        "funding_gate": led.get("funding_gate"),
        "spread_gate": "live only (no historical order book); Bitget majors quote ~0.01-0.1 bps",
    }


def _read_ledger() -> dict:
    for path in (OUT / "trades_ledger.json", Path("/workspace/output/trades_ledger.json")):
        if path.exists():
            return json.loads(path.read_text())
    raise RuntimeError("replay finished without writing output/trades_ledger.json")


def run() -> None:
    t0 = _clock()
    OUT.mkdir(parents=True, exist_ok=True)
    cfg = dict(runtime.manifest.get("strategy_config", {}) or {})
    p = Params.from_config(cfg)
    bt = cfg.get("backtest") or {}
    fetch_start = ledger.month_start_ms(*bt.get("fetch_start_ym", [2024, 8]))
    start_ms = ledger.month_start_ms(*bt.get("start_ym", [2024, 10]))
    end_ms = ledger.month_start_ms(*bt.get("end_ym", [2026, 10]))
    symbols = list(p.symbols)

    frames, funding, coverage = load_history(
        symbols, fetch_start, end_ms, str(bt.get("funding_interval", "4h")),
        int(bt.get("fetch_concurrency", 6)),
    )
    t_fetch = _clock() - t0

    spec = _plain(dict(runtime.backtest_spec))
    venue = spec["venue"]["name"]
    instruments = spec.get("instruments") or [spec["instrument"]]
    ohlcv: dict[str, pd.DataFrame] = {}
    loaded, skipped = [], {}
    for ins in instruments:
        sym = ins["raw_symbol"]
        if sym not in symbols:
            continue
        df = frames.get(sym)
        if df is None or len(df) < p.warmup_bars + 24:
            skipped[sym] = "insufficient bars"
            continue
        frame = backtest.prepare_frame(df, datetime_index="date")
        ohlcv[ins["id"]] = frame
        loaded.append(ins)

    if not loaded:
        runtime.emit_signal(
            action="watch",
            symbol=symbols[0],
            confidence=0.0,
            metrics={"total_trades": 0},
            meta={"reason": "NO_REPLAYABLE_DATA", "coverage": coverage, "skipped": skipped},
        )
        return

    if "instruments" in spec:
        spec["instruments"] = loaded
    loaded_syms = [i["raw_symbol"] for i in loaded]
    scfg = spec["strategy"].setdefault("config", {})
    scfg.update({
        "symbols_csv": ",".join(loaded_syms),
        "venue_name": venue,
        "params_json": json.dumps({**cfg, "trading_symbols": loaded_syms}, default=str),
        "trade_start_ms": start_ms,
        "trade_end_ms": end_ms,
        "ledger_path": str(OUT / "trades_ledger.json"),
        "funding_json": json.dumps({s: funding.get(s, []) for s in loaded_syms if funding.get(s)}),
    })

    result = backtest.run(ohlcv_data=ohlcv, spec=spec)
    t_replay = _clock() - t0 - t_fetch
    led = _read_ledger()

    folds = [(f["name"], ledger.month_start_ms(*f["start_ym"]), ledger.month_start_ms(*f["end_ym"]))
             for f in bt.get("walk_forward_folds", [])]
    split = (str(bt.get("oos_split_label", "")), ledger.month_start_ms(*bt.get("oos_start_ym", [2025, 10])))
    rep = ledger.build_report(
        led["trades"], funding, start_ms=start_ms, end_ms=end_ms, folds=folds, split=split,
        maker=float(cfg.get("maker_fee", 0.0002)), taker=float(cfg.get("taker_fee", 0.0006)),
        slip_ticks=p.slippage_ticks, risk=p.risk_usdt, budget=p.margin_budget,
        interval_hours=p.funding_interval_hours,
    )
    equity = rep.pop("equity_curve")
    per_trade = rep.pop("per_trade_1x")
    one = rep["cost_sensitivity"]["1x"]

    chart_path = backtest.generate_chart(result)
    raw = dict(result.raw or {})
    engine_summary = _plain(raw.get("summary") or {})
    net_pnl = float(one["net_pnl_usdt"] or 0.0)
    max_dd_pct = (float(one["max_dd_usdt"]) / p.margin_budget * 100.0) if one["trades"] else 0.0
    report = {
        "summary": engine_summary,
        "stats": _plain(raw.get("stats") or {}),
        "config": _plain(raw.get("config") or {}),
        "metrics_note": (
            "Top-level metrics come from the Playbook trade ledger at 1x costs: Bitget maker fee on limit "
            "entries, taker fee on all exits, 1 tick slippage per side, historical Bitget funding. "
            "Engine-only figures are under summary/engine_*."
        ),
        "playbook_report": rep,
        "data_coverage": coverage,
        "data_sources": _data_sources(coverage, led),
        "symbols_skipped": skipped,
        "skips": led.get("skips", {}),
        "halt_events": led.get("halt_events", []),
        "net_pnl": round(net_pnl, 4),
        "total_return_pct": round(net_pnl / p.margin_budget * 100.0, 4),
        "starting_balance": p.margin_budget,
        "max_drawdown_pct": round(max_dd_pct, 4),
        "sharpe_ratio": one["sharpe"],
        "win_rate": one["win_rate"],
        "total_trades": one["trades"],
        "profit_factor": one["profit_factor"],
        "net_expectancy_r": one["net_expectancy_r"],
        "verdict": rep["verdict"],
        "period_start": rep["window"]["start"],
        "period_end": rep["window"]["end"],
        "timing_s": {"fetch": round(t_fetch, 1), "replay": round(t_replay, 1)},
    }
    (OUT / "backtest_report.json").write_text(json.dumps(_clean(report), default=str))
    (OUT / "trades_1x.json").write_text(json.dumps(_clean(per_trade), default=str))
    (OUT / "action_log.json").write_text(json.dumps(led.get("events", [])[-3000:], default=str))
    lines = ["timestamp,value,nav"] + [f"{e['timestamp']},{e['value']},{e['nav']}" for e in equity]
    (OUT / "equity_curve.csv").write_text("\n".join(lines) + "\n", encoding="utf-8")

    metrics = _clean({
        "total_return_pct": report["total_return_pct"],
        "net_pnl": report["net_pnl"],
        "starting_balance": p.margin_budget,
        "sharpe_ratio": one["sharpe"],
        "max_drawdown_pct": report["max_drawdown_pct"],
        "win_rate": one["win_rate"],
        "total_trades": one["trades"],
        "profit_factor": one["profit_factor"] if one["profit_factor"] != "inf" else None,
        "net_expectancy_r": one["net_expectancy_r"],
        "expectancy_r_0x": rep["cost_sensitivity"]["0x"]["net_expectancy_r"],
        "expectancy_r_2x": rep["cost_sensitivity"]["2x"]["net_expectancy_r"],
        "engine_total_return_pct": result.total_return_pct,
        "engine_fill_count": result.total_trades,
    })
    runtime.emit_signal(
        action="watch",
        symbol=loaded_syms[0],
        confidence=0.0,
        metrics=metrics,
        meta=_clean({
            "verdict": rep["verdict"],
            "chart_path": chart_path,
            "window": rep["window"],
            "walk_forward": [{k: w[k] for k in ("fold", "trades", "net_expectancy_r", "profit_factor")}
                             for w in rep["walk_forward"]],
            "oos": {k: rep["out_of_sample"][k] for k in ("trades", "net_expectancy_r", "profit_factor")},
            "cost_totals_1x": rep["cost_totals_1x"],
            "data_sources": _data_sources(coverage, led),
            "coverage": coverage,
            "symbols_skipped": skipped,
            "skips": led.get("skips", {}),
            "halt_events": len(led.get("halt_events", [])),
        }),
    )
