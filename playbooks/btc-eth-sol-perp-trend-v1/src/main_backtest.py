"""Historical replay entry point.

Flow: fetch 1H Bitget perp bars + funding (chunked, time-budgeted) -> build
replay frames with a `funding_rate` feature column -> Nautilus replay through
`getagent.backtest.run` -> read the real trade log written by the strategy ->
compute net-expectancy analytics (walk-forward, cost sensitivity) -> write the
platform output contract (backtest_report.json + equity_curve.csv) and emit the
signal with strategy-basis metrics.

This module never imports live trading code or `getagent.trade`.
"""

import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import pandas as pd

from getagent import backtest, data, runtime

from . import analytics as A
from . import features as F
from . import strategy as S

INTERVAL = "1h"
INTERVAL_MS = 3600 * 1000
KLINE_CHUNK_BARS = 1000
FUNDING_CHUNK_DAYS = 85
VENUE = "BITGET"
OUTPUT_DIR = Path("/workspace/output")
CACHE_DIR = S.CACHE_DIR

# Sandbox hard timeout is 180 s; keep the data phase well inside it so the
# replay + analytics phase always gets to run and report honestly.
KLINE_TIME_BUDGET_S = 95.0
FUNDING_TIME_BUDGET_S = 30.0


def _now() -> float:
    return datetime.now(timezone.utc).timestamp()


def _sanitize(value: Any) -> Any:
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, dict):
        return {k: _sanitize(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_sanitize(v) for v in value]
    return value


def _to_frame(response: Any) -> pd.DataFrame:
    """Normalise an SDK response into a UTC DatetimeIndex frame (lowercase columns)."""
    try:
        df = data.to_dataframe(response)
    except Exception:
        return pd.DataFrame()
    if df is None or len(df) == 0:
        return pd.DataFrame()
    df = df.copy()
    df.columns = [str(c).lower() for c in df.columns]
    if not isinstance(df.index, pd.DatetimeIndex):
        if "time" in df.columns and pd.api.types.is_numeric_dtype(df["time"]):
            idx = pd.to_datetime(df["time"].astype("int64"), unit="ms", utc=True)
        elif "time" in df.columns:
            idx = pd.to_datetime(df["time"], utc=True)
        elif "timestamp" in df.columns:
            idx = pd.to_datetime(df["timestamp"], utc=True)
        elif "date" in df.columns:
            idx = pd.to_datetime(df["date"], utc=True)
        else:
            return pd.DataFrame()
        df.index = pd.DatetimeIndex(idx)
    elif df.index.tz is None:
        df.index = df.index.tz_localize("UTC")
    else:
        df.index = df.index.tz_convert("UTC")
    df = df[~df.index.duplicated(keep="last")].sort_index()
    return df


def _fetch_klines(symbol: str, start_ms: int, end_ms: int, deadline: float, probe: dict[str, Any]) -> pd.DataFrame:
    chunks: list[pd.DataFrame] = []
    cursor_end = end_ms
    calls = 0
    truncated = False
    while cursor_end > start_ms:
        if _now() > deadline:
            truncated = True
            break
        chunk_start = max(start_ms, cursor_end - KLINE_CHUNK_BARS * INTERVAL_MS)
        calls += 1
        resp = data.crypto.futures.kline(
            symbol=symbol,
            interval=INTERVAL,
            exchange="bitget",
            limit=KLINE_CHUNK_BARS,
            start_time=chunk_start,
            end_time=cursor_end,
            closed_only=True,
        )
        df = _to_frame(resp)
        if df.empty:
            probe.setdefault("empty_chunks", []).append([chunk_start, cursor_end])
            if chunk_start <= start_ms:
                break
            cursor_end = chunk_start
            continue
        chunks.append(df)
        earliest = int(df.index.min().value // 1_000_000)
        next_end = min(chunk_start, earliest) - 1
        if next_end >= cursor_end:
            break
        cursor_end = next_end
    probe["kline_calls"] = calls
    probe["kline_truncated_by_time_budget"] = truncated
    if not chunks:
        return pd.DataFrame()
    frame = pd.concat(chunks).sort_index()
    frame = frame[~frame.index.duplicated(keep="last")]
    start_ts = pd.Timestamp(start_ms, unit="ms", tz="UTC")
    end_ts = pd.Timestamp(end_ms, unit="ms", tz="UTC")
    frame = frame[(frame.index >= start_ts) & (frame.index < end_ts)]
    keep = [c for c in ("open", "high", "low", "close", "volume") if c in frame.columns]
    frame = frame[keep].astype(float)
    return frame


def _fetch_funding(symbol: str, start_ms: int, end_ms: int, deadline: float, probe: dict[str, Any]) -> pd.Series:
    """Fetch funding history (4h aggregation; settlements are 8h). Tries the
    exchange-native pair first, then the base-asset form documented for the
    upstream funding feed. Returns a UTC-indexed Series of decimal rates."""
    base = symbol[:-4] if symbol.endswith("USDT") else symbol
    chosen: Optional[str] = None
    series_parts: list[pd.Series] = []
    calls = 0
    for candidate in (symbol, base):
        cursor_end = end_ms
        parts: list[pd.Series] = []
        truncated = False
        while cursor_end > start_ms:
            if _now() > deadline:
                truncated = True
                break
            chunk_start = max(start_ms, cursor_end - FUNDING_CHUNK_DAYS * 86400 * 1000)
            calls += 1
            resp = data.crypto.futures.funding_rate(
                symbol=candidate,
                exchange="bitget",
                interval="4h",
                limit=1000,
                start_time=chunk_start,
                end_time=cursor_end,
            )
            df = _to_frame(resp)
            if df.empty or "funding_rate" not in df.columns:
                break
            parts.append(pd.to_numeric(df["funding_rate"], errors="coerce").dropna())
            earliest = int(df.index.min().value // 1_000_000)
            next_end = min(chunk_start, earliest) - 1
            if next_end >= cursor_end:
                break
            cursor_end = next_end
        if parts:
            chosen = candidate
            series_parts = parts
            probe["funding_truncated_by_time_budget"] = truncated
            break
    probe["funding_calls"] = calls
    probe["funding_symbol_used"] = chosen
    if not series_parts:
        return pd.Series(dtype=float)
    series = pd.concat(series_parts).sort_index()
    series = series[~series.index.duplicated(keep="last")]
    series.name = "funding_rate"
    return series


def _attach_funding(bars: pd.DataFrame, funding: pd.Series, probe: dict[str, Any]) -> pd.DataFrame:
    if funding.empty:
        bars = bars.copy()
        bars["funding_rate"] = float("nan")
        probe["funding_join"] = "none"
        return bars
    funding_df = funding.to_frame()
    try:
        frame = backtest.build_feature_frame(
            bars,
            features=[
                backtest.FeatureSource(
                    data=funding_df,
                    include_columns=("funding_rate",),
                    mode="asof",
                    direction="backward",
                )
            ],
        )
        probe["funding_join"] = "backtest.build_feature_frame(asof)"
    except Exception as exc:  # fall back to an equivalent explicit as-of join
        probe["funding_join"] = f"pandas.merge_asof fallback ({type(exc).__name__})"
        left = bars.reset_index().rename(columns={bars.index.name or "index": "time"})
        right = funding_df.reset_index().rename(columns={funding_df.index.name or "index": "time"})
        merged = pd.merge_asof(left.sort_values("time"), right.sort_values("time"), on="time", direction="backward")
        frame = merged.set_index("time")
    if "funding_rate" not in frame.columns:
        frame["funding_rate"] = float("nan")
    for col in ("open", "high", "low", "close", "volume"):
        if col not in frame.columns and col in bars.columns:
            frame[col] = bars[col].values
    frame.index = pd.DatetimeIndex(frame.index).tz_convert("UTC") if frame.index.tz is not None else pd.DatetimeIndex(frame.index).tz_localize("UTC")
    coverage = float(frame["funding_rate"].notna().mean()) if len(frame) else 0.0
    probe["funding_coverage_ratio"] = coverage
    return frame


def _spec_copy() -> dict[str, Any]:
    spec = runtime.backtest_spec
    try:
        payload = json.loads(json.dumps(dict(spec), default=str))
    except TypeError:
        payload = {k: spec[k] for k in spec}
    return payload


def _output_dirs() -> list[Path]:
    # The Runner documents /workspace/output/, but the sandbox resolves report
    # artifacts relative to the package directory; write both when they differ.
    dirs = [OUTPUT_DIR]
    local = Path.cwd() / "output"
    if local.resolve() != OUTPUT_DIR.resolve():
        dirs.append(local)
    return dirs


def _load_trade_log() -> dict[str, Any]:
    if S.LAST_RUN:
        return dict(S.LAST_RUN)
    path = OUTPUT_DIR / "trade_log.json"
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}
    return {}


def _emit_no_data(symbols: list[str], probe: dict[str, Any], reason: str) -> None:
    runtime.emit_signal(
        action="watch",
        symbol=symbols[0] if symbols else "",
        confidence=0.0,
        metrics={"total_trades": 0, "rows": 0},
        meta={"reason": reason, "probe": _sanitize(probe)},
    )


def run() -> None:
    t0 = _now()
    cfg = dict(runtime.manifest.get("strategy_config", {}) or {})
    params = F.StrategyParams.from_config(cfg)
    symbols = [str(s).upper() for s in (cfg.get("trading_symbols") or runtime.manifest.get("trading_symbols") or [])]
    margin_budget = float(cfg.get("margin_budget", params.margin_budget) or params.margin_budget)
    params.margin_budget = margin_budget
    lookback_days = int(cfg.get("backtest_lookback_days", 730) or 730)
    train_months = int(cfg.get("walk_forward_train_months", 12) or 12)
    test_months = int(cfg.get("walk_forward_test_months", 3) or 3)

    end_ms = int(_now() // 3600) * 3600 * 1000
    window_start_ms = end_ms - lookback_days * 86400 * 1000
    warmup_ms = (params.warmup_bars() + 24) * INTERVAL_MS
    fetch_start_ms = window_start_ms - warmup_ms

    probes: dict[str, dict[str, Any]] = {}
    frames: dict[str, pd.DataFrame] = {}
    kline_deadline = t0 + KLINE_TIME_BUDGET_S
    per_symbol_budget = KLINE_TIME_BUDGET_S / max(1, len(symbols))
    for i, symbol in enumerate(symbols):
        probe: dict[str, Any] = {}
        deadline = min(kline_deadline, t0 + per_symbol_budget * (i + 1))
        bars = _fetch_klines(symbol, fetch_start_ms, end_ms, deadline, probe)
        probe["kline_rows"] = int(len(bars))
        probe["kline_first"] = bars.index.min().isoformat() if len(bars) else None
        probe["kline_last"] = bars.index.max().isoformat() if len(bars) else None
        probe["kline_coverage_days"] = round((bars.index.max() - bars.index.min()).total_seconds() / 86400, 2) if len(bars) > 1 else 0
        probes[symbol] = probe
        if bars.empty:
            continue
        frames[symbol] = bars

    if not frames:
        _emit_no_data(symbols, probes, "managed kline path returned no rows for every symbol")
        return

    funding_deadline = _now() + FUNDING_TIME_BUDGET_S
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    replay: dict[str, pd.DataFrame] = {}
    first_open_ns: Optional[int] = None
    for symbol, bars in frames.items():
        probe = probes[symbol]
        funding = _fetch_funding(symbol, fetch_start_ms, end_ms, funding_deadline, probe)
        probe["funding_rows"] = int(len(funding))
        probe["funding_first"] = funding.index.min().isoformat() if len(funding) else None
        probe["funding_last"] = funding.index.max().isoformat() if len(funding) else None
        frame = _attach_funding(bars, funding, probe)
        if not funding.empty:
            cache = {str(int(ts.value // 1_000_000_000)): float(v) for ts, v in funding.items()}
            (CACHE_DIR / f"funding_{symbol}.json").write_text(json.dumps(cache), encoding="utf-8")
        replay[f"{symbol}.{VENUE}"] = frame
        sym_first = int(frame.index.min().value)
        first_open_ns = sym_first if first_open_ns is None else min(first_open_ns, sym_first)

    degraded = [s for s, p in probes.items() if s in frames and (p.get("funding_rows", 0) == 0)]
    if degraded:
        _emit_no_data(
            symbols,
            probes,
            f"funding_rate feature unavailable for {degraded}; refusing to run a replay with silently disabled funding costs",
        )
        return

    spec = _spec_copy()
    loaded_ids = set(replay)
    if isinstance(spec.get("instruments"), list):
        spec["instruments"] = [inst for inst in spec["instruments"] if str(inst.get("id")) in loaded_ids]
    strategy_cfg = spec.setdefault("strategy", {}).setdefault("config", {}) or {}
    strategy_cfg["params_json"] = json.dumps(params.__dict__)
    strategy_cfg["first_bar_open_ns"] = int(first_open_ns or 0)
    spec["strategy"]["config"] = strategy_cfg

    data_phase_s = _now() - t0
    result = backtest.run(ohlcv_data=replay, spec=spec)
    replay_phase_s = _now() - t0 - data_phase_s

    log = _load_trade_log()
    trades: list[dict[str, Any]] = list(log.get("trades", []) or [])
    stats: dict[str, Any] = dict(log.get("stats", {}) or {})
    first_eligible = stats.get("first_eligible_close_ts")
    last_close = stats.get("last_bar_close_ts")
    window_start_ts = int(first_eligible or (window_start_ms // 1000))
    window_end_ts = int(last_close or (end_ms // 1000))

    full = A.summarize(trades, margin_budget=margin_budget, window_start_ts=window_start_ts, window_end_ts=window_end_ts)
    wf = A.walk_forward(
        trades,
        start_ts=window_start_ts,
        end_ts=window_end_ts,
        margin_budget=margin_budget,
        train_months=train_months,
        test_months=test_months,
    )
    costs = A.cost_sensitivity(trades, margin_budget=margin_budget, start_ts=window_start_ts, end_ts=window_end_ts)
    curve = A.equity_curve(trades, starting_value=margin_budget, first_ts=window_start_ts, last_ts=window_end_ts)

    summary = dict(result.summary or {})
    engine_net = float(summary.get("net_pnl", 0) or 0)
    starting_balance = summary.get("starting_balance")
    net_pnl = float(full["net_pnl_usdt"])
    chart_path = backtest.generate_chart(result)

    analytics_block = _sanitize(
        {
            "params": params.__dict__,
            "window": {
                "requested_lookback_days": lookback_days,
                "first_eligible": A._iso(window_start_ts),
                "end": A._iso(window_end_ts),
                "effective_days": round((window_end_ts - window_start_ts) / 86400, 2),
            },
            "data_probe": probes,
            "timing_s": {"data_phase": round(data_phase_s, 2), "replay_phase": round(replay_phase_s, 2)},
            "strategy_stats": stats,
            "halt_events": log.get("halt_events", []),
            "open_at_end": log.get("open_at_end", []),
            "full_window_1x_costs": full,
            "walk_forward": wf,
            "cost_sensitivity": costs,
            "forward_criteria": A.FORWARD_CRITERIA,
            "engine_summary": summary,
            "engine_metrics": {
                "total_return_pct_account": result.total_return_pct,
                "sharpe_ratio": result.sharpe_ratio,
                "max_drawdown_pct_account": result.max_drawdown_pct,
                "win_rate": result.win_rate,
                "total_trades_fills": result.total_trades,
                "position_count": result.position_count,
                "profit_factor": result.profit_factor,
                "net_pnl_fees_only": engine_net,
            },
            "cost_model": {
                "fees": "engine commissions per fill (maker/taker from backtest.yaml)",
                "slippage": f"{params.slippage_ticks} tick(s) per taker fill (stop-loss / time-stop / daily-stop exits)",
                "funding": "rate x qty x close at every 00/08/16 UTC settlement while in position (longs pay positive)",
            },
        }
    )

    raw = dict(result.raw or {})
    reports = raw.get("reports")
    if isinstance(reports, dict):
        reports = dict(reports)
        reports.pop("equity_curve", None)
        raw["reports"] = reports
    raw["net_pnl"] = round(net_pnl, 4)
    raw["total_return_pct"] = round(net_pnl / margin_budget * 100.0, 4)
    raw["max_drawdown_pct"] = round(float(full["max_drawdown_pct_of_budget"]), 4)
    raw["starting_balance"] = starting_balance
    raw["margin_budget"] = margin_budget
    raw["metrics_basis"] = "strategy"
    raw["account_total_return_pct"] = round(net_pnl / starting_balance * 100.0, 6)
    # Same closed-trade drawdown expressed against the venue starting balance, so a
    # platform-side rescale (x starting_balance / margin_budget) lands on the strategy figure.
    raw["account_max_drawdown_pct"] = round(float(full["max_drawdown_usdt"]) / starting_balance * 100.0, 6)
    raw["engine_total_return_pct"] = result.total_return_pct
    raw["engine_max_drawdown_pct"] = result.max_drawdown_pct
    raw["engine_net_pnl_fees_only"] = engine_net
    raw["total_trades"] = full["trades"]
    raw["win_rate"] = full["win_rate"]
    raw["profit_factor"] = full["profit_factor"]
    raw["sharpe_ratio"] = full["sharpe_daily_annualized"]
    raw["playbook_analytics"] = analytics_block
    raw["period_start"] = A._iso(window_start_ts)
    raw["period_end"] = A._iso(window_end_ts)

    csv_lines = ["timestamp,value,nav"]
    for point in curve:
        csv_lines.append(f"{point.get('timestamp', '')},{point.get('value', '')},{point.get('nav', '')}")
    files = {
        "backtest_report.json": json.dumps(_sanitize(raw), default=str),
        "equity_curve.csv": "\n".join(csv_lines) + "\n",
        "backtest_summary.json": json.dumps(analytics_block, default=str),
        "trades.json": json.dumps(_sanitize(trades[:5000]), default=str),
    }
    for out_dir in _output_dirs():
        try:
            out_dir.mkdir(parents=True, exist_ok=True)
            for name, text in files.items():
                (out_dir / name).write_text(text, encoding="utf-8")
        except OSError:
            continue

    metrics = _sanitize(
        {
            "metrics_basis": "strategy",
            "total_return_pct": net_pnl / margin_budget * 100.0,
            "net_pnl": net_pnl,
            "starting_balance": starting_balance,
            "margin_budget": margin_budget,
            "sharpe_ratio": full["sharpe_daily_annualized"] if full["trades"] > 0 else None,
            "max_drawdown_pct": full["max_drawdown_pct_of_budget"],
            "win_rate": full["win_rate"],
            "total_trades": full["trades"],
            "profit_factor": full["profit_factor"],
            "expectancy_r": full["expectancy_r"],
            "verdict": full["verdict"],
            "cost_sensitivity_decision": costs["decision"],
            "walk_forward_oos_trades": wf["oos_aggregate"]["trades"],
            "walk_forward_oos_expectancy_r": wf["oos_aggregate"]["expectancy_r"],
            "account_total_return_pct": net_pnl / starting_balance * 100.0,
            "account_max_drawdown_pct": float(full["max_drawdown_usdt"]) / starting_balance * 100.0,
            "max_drawdown_usdt": full["max_drawdown_usdt"],
            "engine_total_return_pct": result.total_return_pct,
            "engine_max_drawdown_pct": result.max_drawdown_pct,
            "engine_net_pnl_fees_only": engine_net,
            "rows": int(sum(len(f) for f in replay.values())),
            "symbols_loaded": len(replay),
        }
    )
    runtime.emit_signal(
        action="long" if (full["trades"] >= A.MIN_TRADES_FOR_VERDICT and (full["expectancy_r"] or 0) > 0) else "watch",
        symbol=symbols[0],
        confidence=float(full["win_rate"] or 0.0),
        metrics=metrics,
        meta={
            "chart_path": chart_path,
            "report": "output/backtest_report.json",
            "equity_curve": "output/equity_curve.csv",
            "forward_criteria": A.FORWARD_CRITERIA["rule"],
            "halt_events": len(log.get("halt_events", []) or []),
            "data_probe": _sanitize(probes),
        },
    )
