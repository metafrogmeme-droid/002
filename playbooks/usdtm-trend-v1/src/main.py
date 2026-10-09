"""Entry point for the USDT-M Trend v1 Playbook.

Historical runs replay three 1H perpetual instruments through the
managed Nautilus engine (full window, walk-forward train/test split,
and 0x/2x fee sensitivity). Live runs execute the scan -> filter ->
trigger -> order -> manage -> exit -> log flow with every halt gate.
"""

import copy
import json
import math
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

from getagent import backtest, data, runtime

from .action_log import log_action
from .execution import cancel_stale_entries, open_long_with_tpsl, read_positions
from .indicators import TrendState, quantize_to_step
from .risk import (check_portfolio_guards, funding_blocks_long,
                   in_funding_blackout, leverage_for, position_qty,
                   stop_take_prices)

STATE_PATH = Path(".state/usdtm_trend_v1.json")
OUT_DIR = Path("/workspace/output")

FUNDING_TIMES_UTC = (0, 8, 16)


def _sanitize(value):
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def _sanitize_metrics(metrics):
    return {key: _sanitize(val) for key, val in metrics.items()}


def _cfg():
    return runtime.manifest.get("strategy_config", {}) or {}


# --------------------------------------------------------------------------
# Historical path
# --------------------------------------------------------------------------

MS_PER_HOUR = 3600 * 1000


def _fetch_symbol_window(symbol, start_ms, end_ms, interval="1h"):
    """Fetch one symbol over [start_ms, end_ms) in ~35-day chunks."""
    chunk = 35 * 24 * MS_PER_HOUR
    frames = []
    cursor = start_ms
    while cursor < end_ms:
        chunk_end = min(cursor + chunk, end_ms)
        bars = data.crypto.futures.kline(
            symbol=symbol,
            interval=interval,
            limit=1000,
            start_time=cursor,
            end_time=chunk_end,
            closed_only=True,
        )
        frame = backtest.prepare_frame(bars, datetime_index="date")
        if not frame.empty:
            frames.append(frame)
        cursor = chunk_end
    if not frames:
        return None
    import pandas as pd

    merged = pd.concat(frames)
    merged = merged[~merged.index.duplicated(keep="last")].sort_index()
    lo = pd.Timestamp(start_ms, unit="ms", tz="UTC")
    hi = pd.Timestamp(end_ms, unit="ms", tz="UTC")
    return merged[(merged.index >= lo) & (merged.index < hi)]


def _parse_window(spec):
    execution = (spec.get("execution") or {}) if isinstance(spec, dict) else {}
    start = execution.get("start") or "2023-10-01T00:00:00Z"
    end = execution.get("end") or "2025-10-01T00:00:00Z"

    def _ms(value):
        text = str(value).replace("Z", "+00:00")
        return int(datetime.fromisoformat(text).timestamp() * 1000)

    return _ms(start), _ms(end), str(start), str(end)


def _summary_metrics(result):
    summary = result.summary or {}
    try:
        net_pnl = float(summary.get("net_pnl", 0) or 0)
    except (TypeError, ValueError):
        net_pnl = 0.0
    return {
        "total_return_pct": _sanitize(result.total_return_pct),
        "net_pnl": net_pnl,
        "starting_balance": summary.get("starting_balance"),
        "sharpe_ratio": _sanitize(result.sharpe_ratio),
        "max_drawdown_pct": _sanitize(result.max_drawdown_pct),
        "win_rate": _sanitize(result.win_rate),
        "total_trades": result.total_trades,
        "profit_factor": _sanitize(result.profit_factor),
    }


def _atr_series(frame, period=14):
    """Wilder ATR series aligned to frame rows (floats, None until seeded)."""
    highs = [float(v) for v in frame["high"].tolist()]
    lows = [float(v) for v in frame["low"].tolist()]
    closes = [float(v) for v in frame["close"].tolist()]
    out = [None] * len(frame)
    atr = None
    prev_close = None
    for i in range(len(frame)):
        if prev_close is None:
            prev_close = closes[i]
            continue
        tr = max(highs[i] - lows[i], abs(highs[i] - prev_close), abs(lows[i] - prev_close))
        atr = tr if atr is None else (atr * (period - 1) + tr) / period
        out[i] = atr
        prev_close = closes[i]
    return out


def _avg_r_from_raw(raw, frames, atr_mult=1.5):
    """Average R-multiple from closed positions; PENDING when not derivable."""
    try:
        reports = (raw or {}).get("reports") or {}
        positions = reports.get("positions")
        rows = None
        if isinstance(positions, list) and positions:
            rows = positions
        elif isinstance(positions, dict):
            for key in ("closed", "rows", "data"):
                if isinstance(positions.get(key), list) and positions[key]:
                    rows = positions[key]
                    break
        if not rows:
            return {"avg_R": "PENDING", "reason": "no closed-position rows in raw reports"}
        atr_cache = {}
        r_values = []
        for row in rows:
            if not isinstance(row, dict):
                continue
            pnl = None
            for k in ("realized_pnl", "realised_pnl", "pnl", "net_pnl", "profit"):
                if row.get(k) is not None:
                    try:
                        pnl = float(row[k])
                        break
                    except (TypeError, ValueError):
                        continue
            if pnl is None:
                continue
            symbol = str(row.get("symbol") or row.get("raw_symbol") or row.get("instrument") or "")
            symbol = symbol.split(".")[0].upper()
            frame = frames.get(symbol)
            if frame is None or frame.empty:
                continue
            entry_px = None
            for k in ("avg_px_open", "entry_price", "open_price", "entry_px", "price_open"):
                if row.get(k) is not None:
                    try:
                        entry_px = float(row[k])
                        break
                    except (TypeError, ValueError):
                        continue
            qty = None
            for k in ("quantity", "qty", "size", "amount"):
                if row.get(k) is not None:
                    try:
                        qty = float(row[k])
                        break
                    except (TypeError, ValueError):
                        continue
            if entry_px is None or not qty:
                continue
            if symbol not in atr_cache:
                atr_cache[symbol] = _atr_series(frame)
            atrs = atr_cache[symbol]
            entry_ts = None
            for k in ("ts_opened", "entry_time", "open_time", "ts_event", "timestamp"):
                if row.get(k) is not None:
                    entry_ts = row[k]
                    break
            idx = None
            if entry_ts is not None:
                try:
                    import pandas as pd

                    ts = pd.Timestamp(entry_ts, tz="UTC") if not isinstance(entry_ts, (int, float)) else pd.Timestamp(int(entry_ts), unit="ns", tz="UTC")
                    idx = frame.index.get_indexer([ts], method="nearest")[0]
                except (ValueError, TypeError, KeyError):
                    idx = None
            if idx is None or idx < 0 or atrs[idx] is None:
                continue
            risk = float(atr_mult) * float(atrs[idx]) * abs(qty)
            if risk > 0:
                r_values.append(pnl / risk)
        if not r_values:
            return {"avg_R": "PENDING", "reason": "position rows lacked entry/risk fields"}
        return {"avg_R": sum(r_values) / len(r_values), "r_trades": len(r_values)}
    except (ValueError, TypeError, KeyError, AttributeError) as exc:
        return {"avg_R": "PENDING", "reason": "R parse failed: %s" % (exc,)}


def _equity_points_from_raw(raw, summary, frames):
    """Real equity points: engine curve when present, else stepped trade PnL."""
    try:
        reports = (raw or {}).get("reports") or {}
        for key in ("equity_curve", "equity", "account_curve", "nav_curve"):
            series = reports.get(key)
            if isinstance(series, list) and series:
                points = []
                for row in series:
                    if isinstance(row, dict):
                        ts = row.get("timestamp") or row.get("time") or row.get("date")
                        val = row.get("value", row.get("equity", row.get("nav")))
                        if ts is not None and val is not None:
                            points.append((str(ts), float(val)))
                if points:
                    return points
        return []
    except (ValueError, TypeError):
        return []


def _run_one(ohlcv_data, spec, label):
    result = backtest.run(ohlcv_data=ohlcv_data, spec=spec)
    metrics = _summary_metrics(result)
    metrics["label"] = label
    return result, metrics


def _with_fee_scale(spec, scale):
    dup = copy.deepcopy(dict(spec))
    instruments = dup.get("instruments") or ([dup["instrument"]] if dup.get("instrument") else [])
    scaled = []
    for item in instruments:
        item = dict(item)
        for field in ("maker_fee", "taker_fee"):
            try:
                item[field] = str(float(item[field]) * scale)
            except (TypeError, ValueError, KeyError):
                continue
        scaled.append(item)
    if dup.get("instruments"):
        dup["instruments"] = scaled
    elif scaled:
        dup["instrument"] = scaled[0]
    return dup


def _run_historical():
    cfg = _cfg()
    symbols = cfg.get("trading_symbols") or ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
    spec = runtime.backtest_spec
    start_ms, end_ms, start_s, end_s = _parse_window(spec)

    frames = {}
    for symbol in symbols:
        frame = _fetch_symbol_window(symbol, start_ms, end_ms)
        if frame is None or frame.empty:
            runtime.emit_signal(
                action="watch",
                symbol=symbol,
                confidence=0.0,
                metrics={"rows": 0, "window": "%s/%s" % (start_s, end_s)},
                meta={"reason": "no historical bars returned; validation PENDING"},
            )
            return
        frames[symbol] = frame
    ohlcv = {"%s.BINANCE" % s: frames[s] for s in symbols}

    split_ms = int(datetime(2024, 10, 1, tzinfo=timezone.utc).timestamp() * 1000)
    import pandas as pd

    split_ts = pd.Timestamp(split_ms, unit="ms", tz="UTC")
    train = {k: f[f.index < split_ts] for k, f in ohlcv.items()}
    test = {k: f[f.index >= split_ts] for k, f in ohlcv.items()}

    runs = {}
    result_full, runs["full_1x"] = _run_one(ohlcv, spec, "full_1x")
    _, runs["train_1x"] = _run_one(train, spec, "train_1x")
    result_test, runs["test_1x"] = _run_one(test, spec, "test_1x")
    _, runs["full_0x"] = _run_one(ohlcv, _with_fee_scale(spec, 0.0), "full_0x")
    result_2x, runs["full_2x"] = _run_one(ohlcv, _with_fee_scale(spec, 2.0), "full_2x")

    avg_r = _avg_r_from_raw(result_test.raw, {"BTCUSDT": frames["BTCUSDT"]} if len(frames) == 1 else frames)
    runs["test_1x"]["avg_R"] = avg_r.get("avg_R")
    runs["test_1x"]["avg_R_note"] = avg_r.get("reason", "computed from closed positions")

    test_trades = runs["test_1x"].get("total_trades") or 0
    test_pf = runs["test_1x"].get("profit_factor")
    test_sharpe = runs["test_1x"].get("sharpe_ratio")
    verdict = "PENDING"
    if test_trades < 30:
        verdict = "PENDING_NO_VERDICT_UNDER_30_TRADES"
    elif (test_pf is not None and test_pf <= 1.1):
        verdict = "FAIL"
    elif (test_pf is not None and test_pf >= 1.3
          and test_sharpe is not None and test_sharpe >= 0.5):
        verdict = "PASS"
    else:
        verdict = "INCONCLUSIVE"
    expect_2x = None
    try:
        expect_2x = float((result_2x.summary or {}).get("net_pnl", 0) or 0)
    except (TypeError, ValueError):
        pass
    cost_flag = "PENDING"
    if expect_2x is not None:
        cost_flag = "REJECT" if expect_2x <= 0 else "TOLERATES_2X"

    raw = dict(result_full.raw or {})
    summary = result_full.summary or {}
    try:
        net_pnl = float(summary.get("net_pnl", 0) or 0)
    except (TypeError, ValueError):
        net_pnl = 0.0
    starting = summary.get("starting_balance") or 0
    try:
        starting_f = float(starting)
    except (TypeError, ValueError):
        starting_f = 0.0
    raw["net_pnl"] = round(net_pnl, 4)
    raw["starting_balance"] = starting_f
    raw["total_return_pct"] = round(net_pnl / starting_f * 100.0, 4) if starting_f else 0.0
    if isinstance(raw.get("reports"), dict):
        raw["reports"].pop("equity_curve", None)
    raw["usdtm_trend_v1"] = {
        "window": {"start": start_s, "end": end_s},
        "splits": runs,
        "walk_forward": {"train": "start->2024-10-01", "test": "2024-10-01->end"},
        "verdict_test_slice": verdict,
        "cost_sensitivity_2x": cost_flag,
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "backtest_report.json").write_text(json.dumps(raw, default=str))
    points = _equity_points_from_raw(result_full.raw, summary, frames)
    if points:
        base = points[0][1]
        lines = ["timestamp,value,nav"]
        for ts, val in points:
            nav = (val / base) if base else 1.0
            lines.append("%s,%s,%s" % (ts, val, nav))
        (OUT_DIR / "equity_curve.csv").write_text("\n".join(lines) + "\n")
    chart_path = backtest.generate_chart(result_full)

    metrics = _sanitize_metrics({
        "total_return_pct": runs["full_1x"].get("total_return_pct"),
        "net_pnl": runs["full_1x"].get("net_pnl"),
        "starting_balance": runs["full_1x"].get("starting_balance"),
        "sharpe_ratio": runs["full_1x"].get("sharpe_ratio"),
        "max_drawdown_pct": runs["full_1x"].get("max_drawdown_pct"),
        "win_rate": runs["full_1x"].get("win_rate"),
        "total_trades": runs["full_1x"].get("total_trades"),
        "profit_factor": runs["full_1x"].get("profit_factor"),
        "rows": sum(len(f) for f in frames.values()),
    })
    runtime.emit_signal(
        action="watch",
        symbol=",".join(symbols),
        confidence=_sanitize(runs["test_1x"].get("win_rate")) or 0.0,
        metrics=metrics,
        meta={
            "chart_path": chart_path,
            "splits": runs,
            "verdict_test_slice": verdict,
            "cost_sensitivity_2x": cost_flag,
            "strategy": "usdtm-trend-v1",
        },
    )


# --------------------------------------------------------------------------
# Live path
# --------------------------------------------------------------------------

def _read_state():
    try:
        if STATE_PATH.exists():
            return json.loads(STATE_PATH.read_text())
    except (ValueError, OSError):
        pass
    return {}


def _write_state(state):
    try:
        STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
        STATE_PATH.write_text(json.dumps(state, default=str))
    except OSError:
        pass


def _to_records(response):
    try:
        return [dict(r) for r in data.to_records(response)]
    except (ValueError, TypeError, AttributeError):
        return []


def _latest_funding(symbol):
    rows = _to_records(data.crypto.futures.funding_rate(symbol=symbol, exchange="bitget", interval="4h", limit=5))
    if not rows:
        rows = _to_records(data.crypto.futures.funding_rate(symbol=symbol, interval="4h", limit=5))
    if not rows:
        return {"ok": False, "rate": None}
    last = rows[-1]
    for key in ("funding_rate", "fr_close", "estimated_rate"):
        if last.get(key) is not None:
            try:
                return {"ok": True, "rate": float(last[key])}
            except (TypeError, ValueError):
                continue
    return {"ok": False, "rate": None}


def _scan_symbol(symbol, cfg, now):
    """Run scan -> filter -> trigger for one symbol. Returns decision dict."""
    bars_needed = max(int(cfg.get("ema_slow", 50)) * 4, 260)
    bars = data.crypto.futures.kline(
        symbol=symbol, interval="1h", exchange="bitget",
        limit=min(bars_needed, 1000), closed_only=False,
    )
    records = _to_records(bars)
    if len(records) < 60:
        return {"action": "watch", "reason": "NO_TRADE_INSUFFICIENT_BARS", "rows": len(records)}

    last_open_ms = None
    for row in reversed(records):
        raw_time = row.get("time", row.get("date", row.get("timestamp")))
        try:
            import pandas as pd

            last_open_ms = int(pd.Timestamp(raw_time, tz="UTC").timestamp() * 1000)
            break
        except (ValueError, TypeError):
            continue
    now_ms = int(now.timestamp() * 1000)
    if last_open_ms is not None and now_ms - (last_open_ms + MS_PER_HOUR) > 60 * 1000:
        return {"action": "watch", "reason": "NO_TRADE_STALE_DATA", "rows": len(records)}

    state = TrendState(
        ema_fast=int(cfg.get("ema_fast", 20)),
        ema_slow=int(cfg.get("ema_slow", 50)),
        adx_period=int(cfg.get("adx_period", 14)),
        atr_period=int(cfg.get("atr_period", 14)),
        volume_lookback=int(cfg.get("volume_lookback", 20)),
    )
    prev_diff = None
    last = None
    prev = None
    for row in records:
        try:
            snap = state.update(row["high"], row["low"], row["close"], row.get("volume", 0))
        except (KeyError, TypeError, ValueError):
            return {"action": "watch", "reason": "NO_TRADE_AI_INVALID", "rows": len(records)}
        if snap["ema_fast"] is None or snap["ema_slow"] is None:
            continue
        prev = last
        last = snap
        if last is not None and prev is not None:
            prev_diff = prev["ema_fast"] - prev["ema_slow"]
    if last is None or prev_diff is None or not last["ready"]:
        return {"action": "watch", "reason": "NO_TRADE_INDICATOR_WARMUP", "rows": len(records)}
    for key in ("ema_fast", "ema_slow", "adx", "atr", "atr_pct_rank", "volume_ratio", "close"):
        if last.get(key) is None:
            return {"action": "watch", "reason": "NO_TRADE_AI_INVALID", "rows": len(records)}

    diff = last["ema_fast"] - last["ema_slow"]
    if not (prev_diff <= 0.0 < diff):
        return {"action": "watch", "reason": "NO_TRADE_NO_CROSS", "rows": len(records)}
    if last["adx"] <= float(cfg.get("adx_threshold", 20)):
        return {"action": "watch", "reason": "NO_TRADE_REGIME_ADX", "rows": len(records)}
    if last["atr_pct_rank"] < 0.10:
        return {"action": "watch", "reason": "NO_TRADE_REGIME_ATR_DEAD", "rows": len(records)}
    if last["volume_ratio"] < float(cfg.get("volume_mult", 1.5)):
        return {"action": "watch", "reason": "NO_TRADE_VOLUME", "rows": len(records)}

    entry = Decimal(str(last["close"]))
    atr = Decimal(str(last["atr"]))
    st = stop_take_prices(entry, atr, cfg.get("atr_stop_mult", 1.5), cfg.get("tp_r_mult", 2.0), side="long")
    if not st["ok"]:
        return {"action": "watch", "reason": "NO_TRADE_SIZING", "rows": len(records)}
    sized = position_qty(cfg.get("risk_per_trade_usdt", 15), st["risk_dist"])
    if not sized["ok"]:
        return {"action": "watch", "reason": "NO_TRADE_SIZING", "rows": len(records)}
    notional = Decimal(sized["qty"]) * entry
    if notional < Decimal("5"):
        return {"action": "watch", "reason": "NO_TRADE_MIN_NOTIONAL", "rows": len(records)}
    lev = leverage_for(notional, cfg.get("margin_budget", 300), cap=cfg.get("leverage", 5))
    return {
        "action": "long", "reason": "ENTER_LONG_LIMIT",
        "entry": entry, "stop": st["stop"], "take": st["take"],
        "qty": sized["qty"], "leverage": lev.get("leverage", 1),
        "notional": notional, "rows": len(records),
        "adx": last["adx"], "volume_ratio": last["volume_ratio"],
    }


def _run_live():
    from getagent import trade

    cfg = _cfg()
    symbols = cfg.get("trading_symbols") or ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
    now = datetime.now(timezone.utc)
    state = _read_state()
    today = now.strftime("%Y-%m-%d")
    day_state = state.get(today, {"equity_open": None, "consec_losses": 0})
    equity_now = None
    try:
        total = trade.account.total_value()
        equity_now = total
    except (ValueError, TypeError, AttributeError):
        equity_now = None
    _ = equity_now

    try:
        positions = read_positions(symbols)
    except RuntimeError as exc:
        log_action("watch", "-", "flat", "-", "-", "0", "0", "NO_TRADE_POSITION_QUERY_FAIL",
                   {"note": str(exc)})
        runtime.emit_signal(action="watch", symbol=",".join(symbols), confidence=0.0,
                            metrics={"rows": 0},
                            meta={"reason": "position query failed; fail closed"})
        return

    foreign = [s for s in positions["open_symbols"] if s not in symbols]
    shorts = [r for r in positions["records"]
              if str(r.get("hold_side", "")).lower() == "short" and float(r.get("size", 0) or 0) != 0]
    if foreign or shorts:
        log_action("watch", ",".join(foreign + [str(r.get("symbol")) for r in shorts]),
                   "flat", "-", "-", "0", "0", "HALT_FOREIGN_POSITION",
                   {"note": "alert only; Playbook did not open these; no orders touched"})
        runtime.emit_signal_or_follow(
            action="watch", symbol=",".join(symbols), confidence=0.0,
            metrics={"rows": 0}, meta={"reason": "foreign position halt"},
            reason_code="HALT_FOREIGN_POSITION",
        )
        return

    my_open = [s for s in positions["open_symbols"] if s in symbols]
    if len(my_open) >= int(cfg.get("max_positions", 3)):
        runtime.emit_signal(action="watch", symbol=",".join(symbols), confidence=0.0,
                            metrics={"rows": 0, "open_positions": len(my_open)},
                            meta={"reason": "max concurrent positions reached"})
        return

    try:
        cancel_stale_entries(symbols[0], older_than_hours=float(cfg.get("entry_ttl_hours", 4)))
    except RuntimeError:
        pass

    for symbol in symbols:
        if symbol in my_open:
            log_action("watch", symbol, "flat", "-", "-", "0", "0", "NO_TRADE_SYMBOL_OCCUPIED")
            continue
        if in_funding_blackout(now, blackout_minutes=int(cfg.get("funding_blackout_min", 15))):
            log_action("watch", symbol, "flat", "-", "-", "0", "0", "NO_TRADE_FUNDING_BLACKOUT")
            runtime.emit_signal(action="watch", symbol=symbol, confidence=0.0,
                                metrics={"rows": 0}, meta={"reason": "funding blackout"})
            continue
        funding = _latest_funding(symbol)
        if not funding["ok"]:
            log_action("watch", symbol, "flat", "-", "-", "0", "0", "NO_TRADE_FUNDING_UNKNOWN")
            runtime.emit_signal(action="watch", symbol=symbol, confidence=0.0,
                                metrics={"rows": 0}, meta={"reason": "funding unknown; fail closed"})
            continue
        gate = funding_blocks_long(funding["rate"], cfg.get("funding_guard_pct", 0.03))
        if gate["block"]:
            log_action("watch", symbol, "flat", "-", "-", "0", "0", "NO_TRADE_FUNDING_GUARD",
                       {"funding_pct": gate.get("rate_pct")})
            runtime.emit_signal(action="watch", symbol=symbol, confidence=0.0,
                                metrics={"rows": 0, "funding_pct": gate.get("rate_pct")},
                                meta={"reason": "funding guard"})
            continue
        decision = _scan_symbol(symbol, cfg, now)
        if decision["action"] != "long":
            log_action("watch", symbol, "flat", "-", "-", "0", "0", decision["reason"],
                       {"rows": decision.get("rows", 0)})
            runtime.emit_signal(action="watch", symbol=symbol, confidence=0.0,
                                metrics={"rows": decision.get("rows", 0)},
                                meta={"reason": decision["reason"]})
            continue

        limit_px = decision["entry"]
        tp_px = decision["take"]
        sl_px = decision["stop"]
        try:
            rules = trade.helpers.contract_rules(symbol)
            step = getattr(rules, "price_step", None) or "0.01"
            limit_px = quantize_to_step(limit_px, step)
            tp_px = quantize_to_step(tp_px, step)
            sl_px = quantize_to_step(sl_px, step)
        except (ValueError, TypeError, AttributeError):
            pass

        def _execute(sym=symbol, dec=decision, lim=limit_px, tp=tp_px, sl=sl_px):
            result = open_long_with_tpsl(sym, dec["qty"], lim, tp, sl, dec["leverage"])
            log_action("long", sym, "long", lim, "PENDING_FILL", "PENDING", "0",
                       "ENTER_LONG_LIMIT",
                       {"qty": dec["qty"], "leverage": dec["leverage"],
                        "tp": str(tp), "sl": str(sl)})
            return {"status": "submitted", "result": str(result)}

        runtime.emit_signal_or_follow(
            action="long", symbol=symbol, confidence=0.6,
            metrics={"rows": decision["rows"], "adx": decision.get("adx"),
                     "volume_ratio": decision.get("volume_ratio"),
                     "notional_usdt": str(decision["notional"])},
            meta={"reason": "ema cross + regime + volume; limit entry with attached TPSL",
                  "qty": decision["qty"], "limit_price": str(limit_px),
                  "tp": str(tp_px), "sl": str(sl_px)},
            execute_trade=_execute,
            reason_code="ENTER_LONG_LIMIT",
        )


def run():
    if runtime.is_historical():
        _run_historical()
        return
    if runtime.is_live():
        _run_live()
        return
    raise ValueError("unsupported evaluation_mode=%r" % (runtime.evaluation_mode,))


if __name__ == "__main__":
    run()
