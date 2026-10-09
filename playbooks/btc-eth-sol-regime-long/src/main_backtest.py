"""Historical replay for the BTC/ETH/SOL regime-filtered long Playbook (GetAgent engine).

Fetches Bitget 1H perpetual klines and funding through ``getagent.data`` in
chunks, runs the managed Nautilus replay on plain OHLCV (the strategy computes
signals with the same code as live), passes the fetched funding schedule in the
strategy config, and reports net metrics from the strategy ledger (engine PnL
incl. fees, minus funding and 1-tick slippage on taker exits).
Does not import live trading code.
"""
import copy
import json
import math
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from getagent import backtest, data, runtime

from .features import FundingLookup, compute_indicators, compute_signals

HOUR_MS = 3_600_000
DAY_MS = 86_400_000
OUT_DIR = Path("/workspace/output")
KLINE_CHUNK_MS = 1000 * HOUR_MS
FUNDING_CHUNK_MS = 89 * DAY_MS
WARMUP_DAYS = 40
FETCH_BUDGET_SECONDS = 120.0


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _to_ms(value: Any) -> int:
    ts = pd.Timestamp(value)
    if ts.tzinfo is None:
        ts = ts.tz_localize("UTC")
    return int(ts.timestamp() * 1000)


def _time_index(df: pd.DataFrame) -> pd.DatetimeIndex:
    for col in ("time", "date", "timestamp"):
        if col not in df.columns:
            continue
        s = df[col]
        if pd.api.types.is_numeric_dtype(s):
            return pd.DatetimeIndex(pd.to_datetime(s.astype("int64"), unit="ms", utc=True))
        return pd.DatetimeIndex(pd.to_datetime(s, utc=True))
    raise ValueError(f"no time column in {list(df.columns)}")


def _fetch_klines(symbol: str, start_ms: int, end_ms: int, deadline: datetime) -> pd.DataFrame:
    records: list[dict[str, Any]] = []
    cursor = start_ms
    while cursor < end_ms:
        if _now() > deadline:
            raise TimeoutError(f"kline fetch budget exceeded for {symbol}")
        stop = min(cursor + KLINE_CHUNK_MS, end_ms)
        bars = data.crypto.futures.kline(
            symbol=symbol, interval="1h", exchange="bitget", limit=1000,
            start_time=cursor, end_time=stop, closed_only=True,
        )
        records.extend(data.to_records(bars))
        cursor = stop
    if not records:
        raise RuntimeError(f"no bitget 1h klines returned for {symbol}")
    df = pd.DataFrame(records)
    df.index = _time_index(df)
    df = df[~df.index.duplicated(keep="last")].sort_index()
    df = df[(df.index >= pd.Timestamp(start_ms, unit="ms", tz="UTC"))
            & (df.index < pd.Timestamp(end_ms, unit="ms", tz="UTC"))]
    return df[["open", "high", "low", "close", "volume"]].astype(float)


def _fetch_funding_from(exchange: str, symbol: str, start_ms: int, end_ms: int, deadline: datetime) -> pd.Series:
    records: list[dict[str, Any]] = []
    cursor = start_ms
    while cursor < end_ms:
        if _now() > deadline:
            break
        stop = min(cursor + FUNDING_CHUNK_MS, end_ms)
        try:
            resp = data.crypto.futures.funding_rate(
                symbol=symbol, exchange=exchange, interval="4h", limit=1000,
                start_time=cursor, end_time=stop,
            )
            records.extend(data.to_records(resp))
        except Exception:
            pass
        cursor = stop
    if not records:
        return pd.Series(dtype=float)
    df = pd.DataFrame(records)
    if "funding_rate" not in df.columns:
        return pd.Series(dtype=float)
    idx = _time_index(df)
    s = pd.Series(pd.to_numeric(df["funding_rate"], errors="coerce").to_numpy(), index=idx).dropna()
    return s[~s.index.duplicated(keep="last")].sort_index()


def _fetch_funding(symbol: str, start_ms: int, end_ms: int, deadline: datetime) -> tuple[pd.Series, dict[str, Any]]:
    """Bitget funding first; Binance only for the part Bitget does not cover (proxy, reported)."""
    bitget = _fetch_funding_from("bitget", symbol, start_ms, end_ms, deadline)
    info: dict[str, Any] = {"bitget_rows": int(len(bitget)), "binance_proxy_rows": 0}
    first_bitget = int(bitget.index.min().timestamp() * 1000) if len(bitget) else end_ms
    if first_bitget > start_ms + 2 * DAY_MS:
        # Fallback reason: bitget funding history does not reach back to the replay start.
        proxy = _fetch_funding_from("binance", symbol, start_ms, first_bitget, deadline)
        info["binance_proxy_rows"] = int(len(proxy))
        if len(proxy):
            bitget = pd.concat([proxy[proxy.index < pd.Timestamp(first_bitget, unit="ms", tz="UTC")], bitget])
    info["first"] = bitget.index.min().isoformat() if len(bitget) else None
    info["last"] = bitget.index.max().isoformat() if len(bitget) else None
    return bitget.sort_index(), info


def _metrics(trades: list[dict[str, Any]], start_ms: int, end_ms: int, budget: float, risk: float) -> dict[str, Any]:
    t = pd.DataFrame(trades)
    out: dict[str, Any] = {"total_trades": int(len(t))}
    if t.empty:
        return out
    t = t.sort_values("exit_ms")
    wins = t[t["net_pnl"] > 0]
    losses = t[t["net_pnl"] <= 0]
    gl = float(-losses["net_pnl"].sum())
    cum = t["net_pnl"].cumsum().to_numpy()
    peak = pd.Series([0.0, *cum]).cummax().to_numpy()[1:]
    max_dd = float((peak - cum).max())
    days = pd.RangeIndex(start_ms // DAY_MS, end_ms // DAY_MS)
    daily = t.groupby(t["exit_ms"] // DAY_MS)["net_pnl"].sum().reindex(days, fill_value=0.0) / budget
    sd = float(daily.std(ddof=1))
    net = float(t["net_pnl"].sum())
    out.update({
        "win_rate": float(len(wins) / len(t)),
        "avg_r_gross": float(t["r_gross"].mean()),
        "net_expectancy_r": float(t["r_net"].mean()),
        "profit_factor": float(wins["net_pnl"].sum() / gl) if gl > 0 else None,
        "net_pnl": net,
        "gross_pnl": float(t["gross_pnl"].sum()),
        "fees_usdt": float(t["fees"].sum()),
        "funding_usdt": float(t["funding"].sum()),
        "slippage_usdt": float(t["slippage"].sum()),
        "max_drawdown_usdt": max_dd,
        "max_drawdown_r": max_dd / risk,
        "max_drawdown_pct": max_dd / budget * 100.0,
        "sharpe_ratio": float(daily.mean() / sd * math.sqrt(365)) if sd > 0 else None,
        "total_return_pct": net / budget * 100.0,
        "exit_reasons": t["exit_reason"].value_counts().to_dict(),
        "verdict_allowed": bool(len(t) >= 30),
    })
    return out


def _clean(value: Any) -> Any:
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if isinstance(value, dict):
        return {str(k): _clean(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_clean(v) for v in value]
    return value


def run() -> None:
    started = _now()
    deadline = started + timedelta(seconds=FETCH_BUDGET_SECONDS)
    cfg = dict(runtime.manifest.get("strategy_config", {}) or {})
    symbols = [str(s) for s in (cfg.get("trading_symbols") or ["BTCUSDT", "ETHUSDT", "SOLUSDT"])]
    spec = copy.deepcopy(dict(runtime.backtest_spec))
    execution = dict(spec.get("execution") or {})
    start_ms = _to_ms(execution.get("start", "2024-10-01T00:00:00Z"))
    end_ms = _to_ms(execution.get("end", "2026-10-01T00:00:00Z"))
    fetch_start = start_ms - WARMUP_DAYS * DAY_MS
    budget = float(cfg.get("margin_budget", "1500"))
    risk = float(cfg.get("risk_per_trade_usdt", 15.0))

    ohlcv: dict[str, pd.DataFrame] = {}
    coverage: dict[str, Any] = {}
    funding_payload: dict[str, Any] = {}
    venue = str((spec.get("venue") or {}).get("name", "BITGET"))
    for sym in symbols:
        bars = _fetch_klines(sym, fetch_start, end_ms, deadline)
        funding, finfo = _fetch_funding(sym, fetch_start, end_ms, deadline)
        lookup = FundingLookup([int(ts.value // 1_000_000) for ts in funding.index], funding.tolist(),
                               float((cfg.get("funding_interval_hours") or {}).get(sym, 8)))
        if len(lookup):
            funding_payload[sym] = lookup.to_dict()
        sig = compute_signals(compute_indicators(bars, cfg), cfg)
        window = sig[(sig.index >= pd.Timestamp(start_ms, unit="ms", tz="UTC"))]
        coverage[sym] = {
            "rows": int(len(bars)), "first_bar": bars.index.min().isoformat(),
            "last_bar": bars.index.max().isoformat(), "funding": finfo,
            "funding_known_share_in_window": lookup.known_share(start_ms, end_ms),
            "signals_long_in_window": int(window["signal_long"].sum()),
        }
        ohlcv[f"{sym}.{venue}"] = backtest.prepare_frame(bars[["open", "high", "low", "close", "volume"]].copy())
    fetch_seconds = (_now() - started).total_seconds()

    strat_cfg = dict((spec.get("strategy") or {}).get("config") or {})
    for key in ("base_strategy", "ema_fast", "ema_slow", "adx_period", "atr_period", "adx_trend_min",
                "adx_range_max", "atr_rank_window", "atr_rank_min", "atr_rank_max", "volume_avg_period",
                "volume_mult", "breakout_lookback",
                "risk_per_trade_usdt", "max_leverage", "max_concurrent", "stop_atr_mult", "tp_r_multiple",
                "time_stop_hours", "entry_ttl_hours", "daily_pause_usdt", "daily_stop_usdt",
                "max_consecutive_losses", "funding_block_minutes", "funding_max_against_8h", "allow_short"):
        if cfg.get(key) is not None:
            strat_cfg[key] = cfg[key]
    strat_cfg["funding_json"] = json.dumps(funding_payload)
    strat_cfg["margin_budget"] = str(cfg.get("margin_budget", "1500"))
    strat_cfg["signal_start_ms"] = start_ms
    strat_cfg["ledger_path"] = str(OUT_DIR / "replay_ledger.json")
    strat_cfg["bar_types"] = [f"{sym}.{venue}-1-HOUR-LAST-EXTERNAL" for sym in symbols]
    spec.setdefault("strategy", {})["config"] = strat_cfg

    result = backtest.run(ohlcv_data=ohlcv, spec=spec)
    replay_seconds = (_now() - started).total_seconds() - fetch_seconds

    ledger_path = OUT_DIR / "replay_ledger.json"
    ledger = json.loads(ledger_path.read_text()) if ledger_path.exists() else {"trades": []}
    trades = [t for t in ledger.get("trades", []) if int(t.get("signal_close_ms", 0)) < end_ms]
    m = _metrics(trades, start_ms, end_ms, budget, risk)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    raw = dict(result.raw or {})
    reports = dict(raw.get("reports") or {})
    reports.pop("equity_curve", None)
    raw["reports"] = reports
    raw["net_pnl"] = round(float(m.get("net_pnl", 0.0)), 4)
    raw["total_return_pct"] = round(float(m.get("total_return_pct", 0.0)), 4)
    raw["starting_balance"] = budget
    raw["strategy_metrics"] = _clean(m)
    raw["data_coverage"] = coverage
    raw["engine_label"] = "GETAGENT-NAUTILUS-ENGINE"
    (OUT_DIR / "backtest_report.json").write_text(json.dumps(_clean(raw), default=str))

    lines = ["timestamp,value,nav", f"{pd.Timestamp(start_ms, unit='ms', tz='UTC').isoformat()},{budget},1.0"]
    equity = budget
    for t in sorted(trades, key=lambda x: x["exit_ms"]):
        equity += float(t["net_pnl"])
        ts = datetime.fromtimestamp(int(t["exit_ms"]) / 1000.0, tz=timezone.utc).isoformat()
        lines.append(f"{ts},{round(equity, 4)},{round(equity / budget, 6)}")
    (OUT_DIR / "equity_curve.csv").write_text("\n".join(lines) + "\n", encoding="utf-8")

    chart_path = backtest.generate_chart(result)
    metrics = _clean({
        "total_return_pct": m.get("total_return_pct"),
        "net_pnl": m.get("net_pnl"),
        "starting_balance": budget,
        "sharpe_ratio": m.get("sharpe_ratio"),
        "max_drawdown_pct": m.get("max_drawdown_pct"),
        "win_rate": m.get("win_rate"),
        "total_trades": m.get("total_trades"),
        "profit_factor": m.get("profit_factor"),
        "net_expectancy_r": m.get("net_expectancy_r"),
        "avg_r_gross": m.get("avg_r_gross"),
        "max_drawdown_r": m.get("max_drawdown_r"),
        "fees_usdt": m.get("fees_usdt"),
        "funding_usdt": m.get("funding_usdt"),
        "slippage_usdt": m.get("slippage_usdt"),
        "engine_total_trades": result.total_trades,
        "engine_position_count": result.position_count,
        "engine_account_return_pct": result.total_return_pct,
        "fetch_seconds": round(fetch_seconds, 1),
        "replay_seconds": round(replay_seconds, 1),
        "metrics_basis": "strategy",
    })
    runtime.emit_signal(
        action="watch",
        symbol=symbols[0],
        confidence=float(m.get("win_rate") or 0.0),
        metrics=metrics,
        meta=_clean({
            "engine": "GETAGENT-NAUTILUS-ENGINE",
            "window": [pd.Timestamp(start_ms, unit="ms", tz="UTC").isoformat(),
                       pd.Timestamp(end_ms, unit="ms", tz="UTC").isoformat()],
            "chart_path": chart_path,
            "events": ledger.get("events"),
            "skips": ledger.get("skips"),
            "exit_reasons": m.get("exit_reasons"),
            "coverage": coverage,
            "adx_trend_min": cfg.get("adx_trend_min"),
            "unknown_funding_policy": strat_cfg.get("unknown_funding_policy", "block"),
            "signal_evaluations": ledger.get("signal_evaluations"),
        }),
    )
