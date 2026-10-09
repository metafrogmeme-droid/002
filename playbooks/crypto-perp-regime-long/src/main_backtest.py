"""Historical replay entry: Bitget USDT-futures 1H bars -> rules.py features -> Nautilus replay -> honest report."""
import json
import math
from pathlib import Path

from getagent import backtest, data, runtime

try:
    from . import rules
except ImportError:
    import rules

HOUR_MS = 3_600_000
CHUNK_BARS = 990
VENUE = "BITGET"


def _clean(v):
    if isinstance(v, float) and not math.isfinite(v):
        return None
    return v


def _fetch_bars(symbol: str, days: int):
    """Chunked kline pull (the endpoint caps 1000 bars per call)."""
    import pandas as pd

    end_ms = (int(pd.Timestamp.now(tz="UTC").timestamp() * 1000) // HOUR_MS) * HOUR_MS
    start_ms = end_ms - days * 24 * HOUR_MS
    frames = []
    cur_end = end_ms
    while cur_end > start_ms:
        cur_start = max(start_ms, cur_end - CHUNK_BARS * HOUR_MS)
        res = data.crypto.futures.kline(
            symbol=symbol,
            interval="1h",
            exchange="bitget",
            limit=1000,
            start_time=cur_start,
            end_time=cur_end,
            closed_only=True,
        )
        frame = backtest.prepare_frame(res, datetime_index="date")
        if not frame.empty:
            frames.append(frame)
        cur_end = cur_start
    if not frames:
        return None
    out = pd.concat(frames)
    out = out[~out.index.duplicated(keep="last")].sort_index()
    out = out[(out.index.astype("int64") // 1_000_000 >= start_ms) & (out.index.astype("int64") // 1_000_000 < end_ms)]
    return out[["open", "high", "low", "close", "volume"]].astype(float)


def _equity_rows(raw: dict, start_balance: float):
    """Real equity points from the replay's own positions report (no interpolation, no padding)."""
    reports = raw.get("reports", {}) if isinstance(raw, dict) else {}
    curve = reports.get("equity_curve")
    pts = []
    if isinstance(curve, list) and curve:
        for p in curve:
            if isinstance(p, dict):
                ts = p.get("timestamp") or p.get("time") or p.get("ts")
                val = p.get("value") if p.get("value") is not None else p.get("equity")
                if ts is not None and val is not None:
                    pts.append((str(ts), float(val)))
        if pts:
            return pts
    positions = reports.get("positions")
    if isinstance(positions, list):
        rows = []
        for p in positions:
            if not isinstance(p, dict):
                continue
            ts = p.get("ts_closed") or p.get("closed_time")
            pnl = p.get("realized_pnl")
            if ts is None or pnl is None:
                continue
            try:
                rows.append((str(ts), float(str(pnl).split()[0])))
            except ValueError:
                continue
        rows.sort()
        eq = start_balance
        for ts, pnl in rows:
            eq += pnl
            pts.append((ts, eq))
    return pts


def run() -> None:
    cfg_map = dict(runtime.manifest.get("strategy_config", {}) or {})
    cfg_map["margin_cap_usdt"] = cfg_map.get("margin_budget", cfg_map.get("margin_cap_usdt", 500))
    cfg = rules.Config.from_mapping(cfg_map)
    days = int(cfg_map.get("backtest_days", 730))
    spec = runtime.backtest_spec

    ohlcv = {}
    meta_rows = {}
    for sym in cfg.symbols:
        bars = _fetch_bars(sym, days)
        if bars is None or bars.empty:
            runtime.emit_signal(action="watch", symbol=sym, confidence=0.0, metrics={"rows": 0}, meta={"reason": f"no bars for {sym}"})
            return
        sig = rules.compute_signals(rules.compute_indicators(bars, cfg), cfg)
        ohlcv[f"{sym}.{VENUE}"] = bars
        meta_rows[sym] = dict(rows=len(bars), first=str(bars.index[0]), last=str(bars.index[-1]),
                              signals_seen=int(sig[["sig_trend", "sig_mr", "sig_break"]].sum().sum()))

    print(json.dumps({"stage": "author_replay", "rows": {k: len(v) for k, v in ohlcv.items()}, "cwd": str(Path.cwd())}))
    result = backtest.run(ohlcv_data=ohlcv, spec=spec)
    chart = backtest.generate_chart(result)
    summary = result.summary or {}
    start_balance = float(summary.get("starting_balance") or 0.0)
    net_pnl = float(summary.get("net_pnl", 0) or 0)

    raw = dict(result.raw) if isinstance(result.raw, dict) else {}
    margin_budget = float(cfg_map.get("margin_budget", 500))
    raw["net_pnl"] = round(net_pnl, 4)
    raw["total_return_pct"] = round(net_pnl / margin_budget * 100.0, 4) if margin_budget > 0 else None
    raw["starting_balance"] = start_balance
    raw.setdefault("reports", {}).pop("equity_curve", None)

    out_dir = Path("output")
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "backtest_report.json").write_text(json.dumps(raw, default=str))
    pts = _equity_rows(result.raw if isinstance(result.raw, dict) else {}, start_balance)
    lines = ["timestamp,value,nav"]
    for ts, val in pts:
        nav = val / start_balance if start_balance else 1.0
        lines.append(f"{ts},{val},{nav}")
    (out_dir / "equity_curve.csv").write_text("\n".join(lines) + "\n", encoding="utf-8")

    metrics = {
        "total_return_pct": _clean(result.total_return_pct),
        "net_pnl": net_pnl,
        "starting_balance": start_balance,
        "sharpe_ratio": _clean(result.sharpe_ratio),
        "max_drawdown_pct": _clean(result.max_drawdown_pct),
        "win_rate": _clean(result.win_rate),
        "total_trades": result.total_trades,
        "profit_factor": _clean(result.profit_factor),
        "funding_modelled_in_replay": False,
    }
    runtime.emit_signal(
        action="watch",
        symbol=cfg.symbols[0],
        confidence=_clean(result.win_rate) or 0.0,
        metrics=metrics,
        meta={"chart_path": chart, "data": meta_rows, "note": "replay excludes funding; see offline research for net-of-funding numbers"},
    )
