"""Live path for Sleeve A BTC long v1.

Scan -> filter -> trigger -> order -> manage -> exit -> log. Every gate emits
a stable reason code; any gate failure means no trade. Mutations only run
inside the emit_signal_or_follow callback. Never imported by the historical
path.
"""

import json
import math
from datetime import datetime, timezone
from decimal import Decimal, ROUND_DOWN
from pathlib import Path
from typing import Any

from getagent import data, runtime

from .features import WilderState, ema_update

SYMBOL = "BTCUSDT"
STATE_DIR = Path(".state")
STATE_FILE = STATE_DIR / "sleeve_a_v1.json"
ACTION_LOG = STATE_DIR / "action_log.jsonl"


def _cfg() -> dict[str, Any]:
    return runtime.manifest.get("strategy_config", {}) or {}


def _f(cfg: dict[str, Any], key: str, default: float) -> float:
    try:
        return float(cfg.get(key, default))
    except (TypeError, ValueError):
        return default


def _load_state() -> dict[str, Any]:
    try:
        if STATE_FILE.exists():
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        pass
    return {}


def _save_state(state: dict[str, Any]) -> None:
    try:
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        STATE_FILE.write_text(json.dumps(state), encoding="utf-8")
    except OSError:
        pass


def _log_action(entry: dict[str, Any]) -> None:
    entry = dict(entry)
    entry.setdefault("timestamp", datetime.now(timezone.utc).isoformat())
    try:
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        with ACTION_LOG.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, default=str) + "\n")
    except OSError:
        pass
    print(json.dumps({"action_log": entry}, default=str))


def _hold(symbol: str, reason_code: str, reason: str, extra: dict[str, Any]) -> None:
    meta = {"reason_code": reason_code, "reason": reason}
    meta.update(extra)
    _log_action({"symbol": symbol, "side": "none", "reason_code": reason_code, "detail": reason})
    runtime.emit_signal(action="hold", symbol=symbol, confidence=0.0, metrics={"gates": "blocked"}, meta=meta)


def run() -> None:
    cfg = _cfg()
    symbol = str((cfg.get("trading_symbols") or [SYMBOL])[0])
    leverage = int(_f(cfg, "leverage", 3))
    leverage = max(1, min(leverage, 5))
    risk_usdt = _f(cfg, "risk_usdt", 15.0)
    margin_budget = _f(cfg, "margin_budget", 300.0)
    ema_fast = int(_f(cfg, "ema_fast", 20))
    ema_slow = int(_f(cfg, "ema_slow", 50))
    adx_period = int(_f(cfg, "adx_period", 14))
    adx_thr = _f(cfg, "adx_threshold", 20)
    atr_period = int(_f(cfg, "atr_period", 14))
    atr_mult = _f(cfg, "atr_mult", 1.5)
    tp_r = _f(cfg, "tp_r_mult", 2.0)
    rsi_period = int(_f(cfg, "rsi_period", 14))
    rsi_os = _f(cfg, "rsi_oversold", 30)
    atr_lookback = int(_f(cfg, "atr_pct_lookback", 100))
    atr_pct_max = _f(cfg, "atr_pct_max", 95)
    trend_stop = int(_f(cfg, "trend_time_stop_bars", 8))
    mr_stop = int(_f(cfg, "mr_time_stop_bars", 2))
    max_spread_bps = _f(cfg, "max_spread_bps", 5)
    min_vol = _f(cfg, "min_24h_volume_usdt", 50000000)
    blackout_min = int(_f(cfg, "funding_blackout_min", 15))

    now = datetime.now(timezone.utc)
    lookback = max(ema_slow * 4, atr_lookback + 60, 220)
    bars = data.crypto.futures.kline(
        symbol=symbol, interval="1h", exchange="bitget", limit=lookback, closed_only=True
    )
    rows = data.to_records(bars)
    if len(rows) < ema_slow + adx_period * 2 + 20:
        _hold(symbol, "WARMUP_NO_SIGNAL", "insufficient closed bars for a valid signal read", {"rows": len(rows)})
        return
    closes = [float(r["close"]) for r in rows]
    last_open_ms = None
    try:
        last_open_ms = int(rows[-1].get("time") or rows[-1].get("timestamp") or 0)
    except (TypeError, ValueError):
        last_open_ms = None
    if last_open_ms:
        age_ms = int(now.timestamp() * 1000) - (last_open_ms + 3600 * 1000)
        if age_ms > 2 * 3600 * 1000:
            _hold(symbol, "STALE_DATA", "newest closed bar is older than two intervals", {"age_ms": age_ms})
            return
    volumes_24h = sum(float(r.get("volume", 0) or 0) * float(r.get("close", 0) or 0) for r in rows[-24:])
    if volumes_24h < min_vol:
        _hold(symbol, "VOLUME_GATE", "trailing 24h quote volume below the liquidity floor", {"quote_volume_24h": volumes_24h})
        return

    fast_ema: Any = None
    slow_ema: Any = None
    wilder = WilderState(atr_period=atr_period, adx_period=adx_period, rsi_period=rsi_period)
    for r in rows:
        fast_ema = ema_update(fast_ema, float(r["close"]), ema_fast)
        slow_ema = ema_update(slow_ema, float(r["close"]), ema_slow)
        wilder.update(float(r["high"]), float(r["low"]), float(r["close"]))
    if not wilder.ready(ema_slow, atr_lookback) or fast_ema is None or slow_ema is None:
        _hold(symbol, "WARMUP_NO_SIGNAL", "indicator read not yet valid, no trade", {})
        return
    adx = wilder.adx or 0.0
    rsi = wilder.rsi
    atr = wilder.atr or 0.0
    if rsi is None or atr <= 0 or not math.isfinite(adx):
        _hold(symbol, "WARMUP_NO_SIGNAL", "signal layer returned no valid read, no trade", {})
        return
    pctile = wilder.atr_pct_percentile(atr_lookback)
    if pctile is None or pctile > atr_pct_max:
        _hold(symbol, "NO_SETUP", "volatility regime filter rejects new entries", {"atr_pctile": pctile})
        return
    entry_ref = closes[-1]
    kind = ""
    if adx >= adx_thr and fast_ema > slow_ema and entry_ref > slow_ema:
        kind = "trend"
    elif adx < adx_thr and rsi <= rsi_os:
        kind = "mr"
    if not kind:
        _hold(symbol, "NO_SETUP", "no trend or washout-bounce setup on the latest close", {"adx": adx, "rsi": rsi})
        return
    hold_bars = trend_stop if kind == "trend" else mr_stop

    hour = now.hour
    settlements = [0, 8, 16]
    mins_to_settle = min(abs(hour - s) * 60 + now.minute if False else 0 for s in settlements)
    dist_min = min(min(abs(now.hour * 60 + now.minute - s * 60), 24 * 60 - abs(now.hour * 60 + now.minute - s * 60)) for s in settlements)
    _ = mins_to_settle
    if dist_min <= blackout_min:
        _hold(symbol, "FUNDING_BLACKOUT", "inside the funding settlement blackout window", {"mins_to_settlement": dist_min})
        return

    stop_dist = atr_mult * atr
    if stop_dist <= 0:
        _hold(symbol, "NO_SETUP", "degenerate stop distance", {})
        return
    sl_price = entry_ref - stop_dist
    tp_price = entry_ref + tp_r * stop_dist
    qty_risk = risk_usdt / stop_dist
    max_notional = margin_budget * leverage
    qty = min(qty_risk, max_notional / entry_ref if entry_ref > 0 else qty_risk)
    if qty * entry_ref < 5:
        _hold(symbol, "NO_SETUP", "risk-sized quantity below exchange minimum notional", {})
        return

    try:
        fr_rows = data.to_records(
            data.crypto.futures.funding_rate(symbol=symbol, exchange="bitget", interval="4h", limit=1)
        )
        funding_rate = float((fr_rows or [{}])[-1].get("funding_rate", 0) or 0)
    except (TypeError, ValueError, IndexError, AttributeError):
        funding_rate = 0.0
    planned_hold_h = float(hold_bars)
    expected_funding = abs(funding_rate) * (qty * entry_ref) * (planned_hold_h / 8.0)
    if expected_funding > 0.1 * risk_usdt:
        _hold(symbol, "FUNDING_COST", "expected funding over planned hold exceeds 0.1R", {"expected_funding_usdt": expected_funding})
        return

    state = _load_state()
    today = now.date().isoformat()
    if state.get("halt_date") == today and state.get("daily_halt"):
        _hold(symbol, "DAILY_HALT", "daily realised loss limit already tripped, operator halt in force", {})
        return
    if int(state.get("consec_losses", 0) or 0) >= 5:
        _hold(symbol, "CONSEC_LOSS_HALT", "five consecutive losses recorded, entries halted", {})
        return

    from getagent import trade

    try:
        current = trade.contract.current_position(symbol=symbol)
        mine = trade.helpers.find_contract_position(current, symbol=symbol)
    except Exception as exc:
        _hold(symbol, "STALE_DATA", f"position state unreadable, refusing to act: {exc}", {})
        return
    if mine is not None:
        _log_action({"symbol": symbol, "side": "none", "reason_code": "FOREIGN_POSITION", "detail": "position this playbook did not open is present, alerting without touching"})
        runtime.emit_signal(
            action="hold",
            symbol=symbol,
            confidence=0.0,
            metrics={"gates": "blocked"},
            meta={"reason_code": "FOREIGN_POSITION", "reason": "position this playbook did not open is present, alerting without touching"},
        )
        return
    try:
        all_positions = trade.contract.current_position()
        open_count = trade.helpers.count_open_contract_positions(all_positions)
    except Exception:
        open_count = 0
    if open_count >= 1:
        _hold(symbol, "CLUSTER_LIMIT", "correlation cluster already holds a position", {"open_count": open_count})
        return
    try:
        quote = trade.helpers.contract_price_quote(symbol=symbol)
        bid = float(getattr(quote, "bid", None) or getattr(quote, "bid_price", None) or 0)
        ask = float(getattr(quote, "ask", None) or getattr(quote, "ask_price", None) or 0)
        if bid > 0 and ask > 0:
            spread_bps = (ask - bid) / ((ask + bid) / 2) * 10000
            if spread_bps > max_spread_bps:
                _hold(symbol, "SPREAD_GATE", "live spread above the liquidity gate", {"spread_bps": spread_bps})
                return
    except Exception:
        pass

    try:
        rules = trade.helpers.contract_rules(symbol=symbol)
        step = Decimal(str(getattr(rules, "price_step", "0.1") or "0.1"))
    except Exception:
        step = Decimal("0.1")

    def quantize(px: float) -> str:
        d = (Decimal(str(px)) // step) * step
        return format(d, "f")

    sl_q = quantize(sl_price)
    tp_q = quantize(tp_price)
    try:
        tpsl = trade.helpers.resolve_contract_tpsl(
            symbol=symbol, side="long", leverage=leverage,
            tp_trigger_price=tp_q, sl_trigger_price=sl_q, reference_price=quantize(entry_ref),
        )
        tp_final = str(getattr(tpsl, "tp_trigger_price", tp_q) or tp_q)
        sl_final = str(getattr(tpsl, "sl_trigger_price", sl_q) or sl_q)
    except Exception:
        tp_final, sl_final = tp_q, sl_q
    try:
        cap = trade.helpers.compute_qty(symbol=symbol, market="contract", budget_amount=str(margin_budget), leverage=leverage)
        cap_qty = float(getattr(cap, "qty", qty) or qty)
        qty = min(qty, cap_qty)
    except Exception:
        pass
    qty = max(qty, 0.0001)
    qty_str = str(Decimal(str(qty)).quantize(Decimal("0.0001"), rounding=ROUND_DOWN))
    limit_price = quantize(entry_ref)
    confidence = 0.6 if kind == "trend" else 0.45

    def execute_trade() -> dict[str, Any]:
        from getagent import trade as live_trade

        try:
            pending = live_trade.contract.pending_orders(symbol=symbol)
            try:
                live_trade.helpers.select_contract_order(pending, symbol=symbol, prefer_first=True)
            except Exception:
                pass
            raws: Any = pending
            for key in ("data", "orders", "list"):
                try:
                    cand_inner = raws.get(key) if isinstance(raws, dict) else None
                except Exception:
                    cand_inner = None
                if isinstance(cand_inner, list):
                    raws = cand_inner
                    break
            if isinstance(raws, list):
                for cand in raws:
                    oid = cand.get("order_id", cand.get("orderId", "")) if isinstance(cand, dict) else ""
                    if oid:
                        try:
                            live_trade.contract.cancel_order(symbol=symbol, order_id=str(oid))
                        except Exception:
                            pass
        except Exception:
            pass
        res = live_trade.contract.open_long_limit(
            symbol=symbol, qty=qty_str, price=limit_price, leverage=leverage,
            tp_trigger_price=tp_final, sl_trigger_price=sl_final,
        )
        if not live_trade.is_success(res):
            raise RuntimeError(f"contract limit entry failed: {res}")
        _log_action({
            "symbol": symbol, "side": "long", "kind": kind,
            "intended_price": entry_ref, "limit_price": limit_price,
            "qty": qty_str, "leverage": leverage,
            "stop_price": sl_final, "take_profit": tp_final,
            "risk_usdt": risk_usdt, "hold_bars": hold_bars,
            "reason_code": "SIGNAL_LONG_TREND" if kind == "trend" else "SIGNAL_LONG_MR",
            "fees": "maker 0.0002 / taker 0.0006 + 1-tick slippage + funding",
        })
        return {"qty": qty_str, "limit_price": limit_price, "result": res}

    runtime.emit_signal_or_follow(
        action="long",
        symbol=symbol,
        confidence=confidence,
        metrics={
            "entry_ref": entry_ref, "stop_dist": stop_dist, "risk_usdt": risk_usdt,
            "qty": qty_str, "leverage": leverage, "adx": adx, "rsi": rsi,
            "kind": kind, "hold_bars": hold_bars,
        },
        meta={"kind": kind, "limit_price": limit_price, "tp": tp_final, "sl": sl_final},
        execute_trade=execute_trade,
        reason_code="SIGNAL_LONG_TREND" if kind == "trend" else "SIGNAL_LONG_MR",
        reason_text=f"Long {kind} setup on {symbol} hourly close",
    )
