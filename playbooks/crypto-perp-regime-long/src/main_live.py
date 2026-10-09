"""Live (scheduled, follow-trade) entry.

Flow per cycle: scan -> filter -> trigger -> order -> manage -> exit -> log.
Fail-closed: any unreadable exchange/data state produces NO TRADE with a reason code.
All trade mutations run inside the execute_trade callback of runtime.emit_signal_or_follow.
This path is NOT exercised by the historical replay; first-run verification items are listed in the design doc.
"""
import json
from datetime import datetime, timezone
from pathlib import Path

from getagent import data, runtime

try:
    from . import rules
except ImportError:
    import rules

STATE_PATH = Path(".state/regime_long_state.json")
HOUR_MS = 3_600_000
SIGNAL_MAX_AGE_MIN = 20
SPEC_KEYS = ("tick", "step", "min_qty")


def _now_ms() -> int:
    return int(datetime.now(timezone.utc).timestamp() * 1000)


def _load_state() -> dict:
    if STATE_PATH.exists():
        return json.loads(STATE_PATH.read_text())
    return {"open": {}, "pending": {}, "last_bar": {}, "flat_equity": None, "day": None, "day_pnl": 0.0, "total_pnl": 0.0,
            "streak": 0, "closed": [], "log": [], "initialised": False}


def _save_state(state: dict) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    state["log"] = state["log"][-500:]
    state["closed"] = state["closed"][-200:]
    STATE_PATH.write_text(json.dumps(state, default=str))


def _records(obj):
    """Best-effort list-of-dicts extraction from SDK envelopes."""
    if isinstance(obj, list):
        return [r for r in obj if isinstance(r, dict)]
    if isinstance(obj, dict):
        for key in ("data", "list", "entrustedList", "orderList", "fillList", "positions", "result"):
            if key in obj:
                got = _records(obj[key])
                if got:
                    return got
    return []


def _first_float(obj, keys):
    if isinstance(obj, dict):
        for k in keys:
            if k in obj and obj[k] not in (None, ""):
                try:
                    return float(obj[k])
                except (TypeError, ValueError):
                    pass
        for v in obj.values():
            got = _first_float(v, keys)
            if got is not None:
                return got
    elif isinstance(obj, list):
        for v in obj:
            got = _first_float(v, keys)
            if got is not None:
                return got
    return None


def _equity(trade) -> float:
    res = trade.account.total_value()
    val = _first_float(res, ("usdtEquity", "accountEquity", "totalUsdt", "total_usdt", "totalAmount", "total", "equity"))
    if val is None:
        raise RuntimeError("equity unreadable from total_value()")
    return val


class Log:
    def __init__(self, state: dict) -> None:
        self.state = state

    def add(self, **row) -> None:
        row.setdefault("ts", datetime.now(timezone.utc).isoformat())
        self.state["log"].append(row)
        print(json.dumps(row, default=str))


def _watch(symbol: str, code: str, text: str, log: Log, **extra) -> None:
    log.add(symbol=symbol, action="no_trade", reason_code=code, **extra)
    runtime.emit_signal_or_follow(
        action="watch", symbol=symbol, confidence=0.0, metrics={}, meta={"reason_code": code, **extra},
        reason_code=code, reason_text=text,
    )


def run() -> None:
    from getagent import trade

    mf = dict(runtime.manifest.get("strategy_config", {}) or {})
    mf["margin_cap_usdt"] = mf.get("margin_budget", mf.get("margin_cap_usdt", 500))
    cfg = rules.Config.from_mapping(mf)
    specs = mf.get("contract_specs", {})
    armed = bool(mf.get("live_armed", False))
    funding_interval_h = int(mf.get("funding_interval_hours", 8))
    state = _load_state()
    log = Log(state)
    now_ms = _now_ms()
    day = now_ms // (24 * HOUR_MS)

    try:
        positions = _records(trade.contract.current_position())
        pend_orders = _records(trade.contract.pending_orders())
        equity = _equity(trade)
    except Exception as exc:  # noqa: BLE001 - fail closed on any exchange read problem
        _watch("", rules.REASON["HALT_STALE"], f"exchange state unreadable: {exc}", log)
        _save_state(state)
        return

    held = {str(p.get("symbol")): p for p in positions if _first_float(p, ("total", "available", "size")) not in (None, 0.0)}
    pend_ids = {str(o.get("orderId")): o for o in pend_orders}

    if not state["initialised"]:
        state["flat_equity"] = equity if not held else None
        state["initialised"] = True
        state["day"] = day
    if state["day"] != day:
        state["day"], state["day_pnl"] = day, 0.0

    # ---- manage: reconcile pending orders and positions this Playbook opened
    for sym, pend in list(state["pending"].items()):
        if pend["order_id"] in pend_ids:
            near_window = rules.in_funding_window(now_ms + cfg.funding_blackout_min * 60_000, cfg.funding_blackout_min) or rules.in_funding_window(now_ms, cfg.funding_blackout_min)
            if now_ms >= pend["expire_ms"] or near_window:
                why = rules.REASON["FUNDING_WINDOW"] if near_window and now_ms < pend["expire_ms"] else "entry_unfilled_after_4h"
                runtime.emit_signal_or_follow(
                    action="close", symbol=sym, confidence=1.0, metrics={}, meta={"reason_code": why, "order_id": pend["order_id"]},
                    reason_code=why, reason_text="cancel resting entry",
                    execute_trade=lambda s=sym, oid=pend["order_id"]: trade.contract.cancel_order(symbol=s, order_id=oid),
                )
                log.add(symbol=sym, side="long", action="cancel_entry", reason_code=why, intended_price=pend["limit"])
                state["pending"].pop(sym, None)
        elif sym in held:
            avg = _first_float(held[sym], ("openPriceAvg", "averageOpenPrice", "openPrice"))
            state["open"][sym] = {**pend, "fill_ms": now_ms, "fill_price": avg}
            state["pending"].pop(sym, None)
            log.add(symbol=sym, side="long", action="entry_filled", intended_price=pend["limit"], filled_price=avg, reason_code=pend["reason"])
        else:
            log.add(symbol=sym, side="long", action="entry_gone_unfilled", reason_code="cancelled_or_rejected", intended_price=pend["limit"])
            state["pending"].pop(sym, None)

    for sym, op in list(state["open"].items()):
        if sym not in held:
            state["open"].pop(sym, None)
            continue
        if now_ms >= op["fill_ms"] + op["hold_h"] * HOUR_MS:
            runtime.emit_signal_or_follow(
                action="close", symbol=sym, confidence=1.0, metrics={}, meta={"reason_code": "time_stop"},
                reason_code="time_stop", reason_text="time stop reached",
                execute_trade=lambda s=sym: trade.contract.close_position(symbol=s, hold_side="long"),
            )
            log.add(symbol=sym, side="long", action="exit_time_stop", reason_code="time_stop", intended_price=None)

    # ---- realised ledger from equity at flat moments (includes fees + funding)
    flat_now = not held and not state["pending"]
    if flat_now and state["flat_equity"] is not None and not state["open"]:
        delta = equity - state["flat_equity"]
        if abs(delta) > 1e-9 and state.get("had_trade"):
            state["day_pnl"] += delta
            state["total_pnl"] += delta
            state["streak"] = state["streak"] + 1 if delta < 0 else 0
            state["closed"].append({"ts": now_ms, "pnl": delta})
            log.add(symbol="", action="trade_closed", reason_code="ledger", realised_net=delta)
            state["had_trade"] = False
        state["flat_equity"] = equity
    elif flat_now and state["flat_equity"] is None:
        state["flat_equity"] = equity

    # ---- risk / halt gates
    foreign = tuple(s for s in held if s not in state["open"] and s not in state["pending"])
    rstate = rules.RiskState(
        realised_today=state["day_pnl"], realised_total=state["total_pnl"], consecutive_losses=state["streak"],
        open_symbols=tuple(set(state["open"]) | set(state["pending"])), foreign_positions=foreign,
    )
    gate = rules.risk_gate(rstate, cfg)
    if gate:
        _watch("", gate, f"entries blocked: {gate}", log, foreign=list(foreign))
        _save_state(state)
        return
    if not armed:
        _watch("", "not_armed_validation_rejected", "live_armed is false: v1 failed its pre-registered cost-sensitivity rule", log)
        _save_state(state)
        return
    if rstate.open_symbols:
        runtime.emit_signal_or_follow(action="hold", symbol=",".join(rstate.open_symbols), confidence=0.0, metrics={}, meta={}, reason_code=rules.REASON["CLUSTER"], reason_text="cluster occupied")
        _save_state(state)
        return

    # ---- scan -> filter -> trigger -> order
    for sym in cfg.symbols:
        try:
            bars = data.crypto.futures.kline(symbol=sym, interval="1h", exchange="bitget", limit=1000, closed_only=True)
            df = data.to_dataframe(bars)
            df = df.rename(columns=str.lower)
            if "time" in df.columns:
                import pandas as pd
                df.index = pd.to_datetime(df["time"], unit="ms", utc=True)
            df = df[["open", "high", "low", "close", "volume"]].astype(float).sort_index()
            last_open_ms = int(df.index[-1].value // 1_000_000)
            age_min = (now_ms - (last_open_ms + HOUR_MS)) / 60_000
            if age_min > SIGNAL_MAX_AGE_MIN:
                _watch(sym, rules.REASON["HALT_STALE"], f"last closed bar is {age_min:.0f} min old", log)
                continue
            if state["last_bar"].get(sym) == last_open_ms:
                continue
            ind = rules.compute_indicators(df, cfg)
            sig = rules.compute_signals(ind, cfg)
            row = sig.iloc[-1]
            if not bool(row["valid"]):
                _watch(sym, rules.REASON["SIGNAL_INVALID"], "insufficient/invalid history", log)
                continue
            module = "trend" if row["sig_trend"] else "break" if row["sig_break"] else "mr" if row["sig_mr"] else None
            state["last_bar"][sym] = last_open_ms
            if module is None:
                log.add(symbol=sym, action="no_signal", reason_code=rules.REASON["NO_SIGNAL"])
                continue

            tick_q = data.crypto.futures.ticker(symbol=sym, exchange="bitget")
            t = data.to_records(tick_q)[0]
            bid, ask, qv = float(t["bid"]), float(t["ask"]), float(t.get("quote_volume") or 0.0)
            spread_bps = (ask - bid) / ((ask + bid) / 2) * 1e4
            if spread_bps > cfg.max_spread_bps:
                _watch(sym, rules.REASON["SPREAD"], f"spread {spread_bps:.2f} bps", log, spread_bps=spread_bps)
                continue
            if qv < cfg.min_volume_24h_usdt:
                _watch(sym, rules.REASON["VOLUME"], f"24h volume {qv:.0f}", log, quote_volume=qv)
                continue
            mark = data.to_records(data.crypto.futures.mark_price(symbol=sym, exchange="bitget"))[0]
            nft = int(mark["next_funding_time"])
            if (nft // HOUR_MS) % funding_interval_h != 0:
                _watch(sym, rules.REASON["HALT_STALE"], "funding schedule differs from spec", log)
                continue
            if rules.in_funding_window(now_ms, cfg.funding_blackout_min) or rules.in_funding_window(now_ms + HOUR_MS, cfg.funding_blackout_min):
                _watch(sym, rules.REASON["FUNDING_WINDOW"], "inside funding settlement window", log)
                continue
            sp = specs[sym]
            rules_live = trade.helpers.contract_rules(sym)
            step_live = getattr(rules_live, "price_step", None)
            if step_live is not None and abs(float(step_live) - sp["tick"]) > 1e-12:
                _watch(sym, rules.REASON["SIGNAL_INVALID"], "tick size differs from spec", log)
                continue
            plan = rules.build_plan(
                module=module, close=float(row["close"]), atr=float(row["atr"]), decision_ts_ms=now_ms, cfg=cfg,
                tick=sp["tick"], size_step=sp["step"], min_qty=sp["min_qty"], min_notional=float(mf.get("min_notional_usdt", 5.0)),
                funding_rate=float(mark.get("last_funding_rate") or 0.0),
            )
            if not plan.ok:
                _watch(sym, plan.reason, f"plan rejected: {plan.reason}", log, **plan.details)
                continue

            def _place(p=plan, s=sym, mod=module):
                trade.contract.change_leverage(symbol=s, leverage=cfg.leverage)
                res = trade.contract.place_order(
                    symbol=s, side="buy", order_type="limit", qty=str(p.qty), price=str(p.limit_price),
                    margin_mode="isolated", trade_side="open", tp_trigger_price=str(p.tp_price), sl_trigger_price=str(p.stop_price),
                )
                if not trade.is_success(res):
                    raise RuntimeError(f"place_order failed: {res}")
                oid = None
                for key in ("orderId", "order_id"):
                    oid = oid or (res.get(key) if isinstance(res, dict) else None)
                    if oid is None and isinstance(res, dict) and isinstance(res.get("data"), dict):
                        oid = res["data"].get(key)
                if oid is None:
                    raise RuntimeError("order id missing in place_order response")
                state["pending"][s] = {"order_id": str(oid), "limit": p.limit_price, "stop": p.stop_price, "tp": p.tp_price, "qty": p.qty,
                                       "hold_h": p.time_stop_hours, "module": mod, "reason": p.reason,
                                       "expire_ms": now_ms + cfg.entry_cancel_hours * HOUR_MS}
                state["had_trade"] = True
                state["flat_equity"] = state["flat_equity"] if state["flat_equity"] is not None else equity
                return res

            runtime.emit_signal_or_follow(
                action="long", symbol=sym, confidence=0.5,
                metrics={"qty": plan.qty, "notional_usdt": plan.notional, "margin_usdt": plan.margin, "risk_usdt": plan.risk_usdt,
                         "min_open_notional_usdt": 5.0, "sizing_ok": True, "spread_bps": spread_bps},
                meta={"module": module, "limit": plan.limit_price, "stop": plan.stop_price, "tp": plan.tp_price, "reason_code": plan.reason},
                reason_code=plan.reason, reason_text=f"{module} long limit, stop 1.5 ATR, TP 2R",
                execute_trade=_place,
            )
            log.add(symbol=sym, side="long", action="entry_order", intended_price=plan.limit_price, filled_price=None, fees=None,
                    funding=None, reason_code=plan.reason, stop=plan.stop_price, tp=plan.tp_price, qty=plan.qty)
            break
        except Exception as exc:  # noqa: BLE001 - fail closed per symbol
            _watch(sym, rules.REASON["SIGNAL_INVALID"], f"cycle error: {exc}", log)
    _save_state(state)
