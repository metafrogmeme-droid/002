"""Live (scheduled, follow-trade) entry for bitget-usdtm-trend-v1.

Cron runs every 15 minutes (UTC). Each run: read account state -> reconcile the
ledger -> manage resting entries and open positions (entry expiry, time stop)
-> apply halt gates -> scan symbols for a new closed 1h bar -> emit the signal
and, only inside the follow-trade callback, place the order.

Halting means "stop emitting new entries and alert". It never flattens
positions and never calls any Playbook enable/disable/stop API.
"""
from datetime import datetime, timezone
from typing import Any, Optional

from getagent import runtime

try:
    from . import features, ledger as ledger_mod, logic
except ImportError:  # loaded as a top-level module
    import features  # type: ignore[no-redef]
    import ledger as ledger_mod  # type: ignore[no-redef]
    import logic  # type: ignore[no-redef]

RC = logic.ReasonCode
HOUR_MS = logic.HOUR_MS


def _execution() -> Any:
    """Import the trade-touching module lazily so historical runs never load it."""
    try:
        from . import execution
    except ImportError:
        import execution  # type: ignore[no-redef]
    return execution


def _emit(action: str, symbol: str, reason: Any, metrics: dict[str, Any], meta: dict[str, Any],
          execute: Optional[Any] = None) -> None:
    runtime.emit_signal_or_follow(
        action=action, symbol=symbol, confidence=1.0 if execute is not None else 0.0,
        metrics=metrics, meta=meta, execute_trade=execute,
        reason_code=reason.value, reason_text=str(meta.get("text", reason.value)),
    )


def _alert(rl: Any, now_ms: int, symbol: str, reason: Any, text: str, **detail: Any) -> None:
    rl.add(now_ms, symbol, "alert", reason, text=text, **detail)
    _emit("watch", symbol, reason, {"alert": 1}, {"text": text, **detail})


def _estimate_funding(symbol: str, fill_ms: int, exit_ms: int, qty: float, px: float) -> Optional[float]:
    try:
        frame = features.fetch_funding(symbol, fill_ms - HOUR_MS, exit_ms + HOUR_MS)
    except Exception:  # noqa: BLE001 - estimate only; absence is logged as 'unavailable'
        return None
    if frame is None:
        return None
    total = 0.0
    for ts, rate in frame["funding_rate"].items():
        t = int(ts.timestamp() * 1000)
        if fill_ms < t <= exit_ms:
            total += float(rate) * qty * px
    return total


def _finalize_closed(rl: Any, led: Any, now_ms: int, symbol: str, rec: dict[str, Any],
                     fills: list[dict[str, Any]], spec: Any) -> None:
    since = int(rec.get("fill_ms") or rec.get("placed_ms") or 0)
    norm = [f for f in (logic.normalize_fill(r) for r in fills)
            if f["symbol"] == symbol and (f["ts_ms"] or 0) >= since]
    opens = [f for f in norm if not f["is_close"]]
    closes = [f for f in norm if f["is_close"]]
    plan = rec.get("plan", {})
    qty = sum(f["qty"] or 0.0 for f in closes)
    exit_px = (sum((f["price"] or 0.0) * (f["qty"] or 0.0) for f in closes) / qty) if qty else None
    entry_q = sum(f["qty"] or 0.0 for f in opens)
    entry_px = (sum((f["price"] or 0.0) * (f["qty"] or 0.0) for f in opens) / entry_q) if entry_q else plan.get("entry")
    fees = sum(f["fee"] for f in norm)
    profit = sum(f["profit"] or 0.0 for f in closes)
    exit_ms = max([f["ts_ms"] or 0 for f in closes] or [now_ms])
    reason = RC.EXIT_UNKNOWN
    if exit_px is not None:
        reason = logic.classify_exit(exit_px, float(plan.get("stop", 0)), float(plan.get("take_profit", 0)),
                                     float(spec.tick), bool(rec.get("time_stop_requested")))
    funding = None
    if closes:
        funding = _estimate_funding(symbol, int(rec.get("fill_ms") or since), exit_ms, qty or entry_q, float(entry_px or 0))
    intended = plan.get("stop") if reason == RC.EXIT_STOP_LOSS else plan.get("take_profit") if reason == RC.EXIT_TAKE_PROFIT else None
    rl.add(exit_ms or now_ms, symbol, "exit", reason, intended_price=intended, filled_price=exit_px,
           qty=qty or None, fee_usdt=fees, funding_usdt=funding, pnl_usdt=profit - fees,
           funding_source="estimated_from_funding_history" if funding is not None else "unavailable",
           entry_px=entry_px)
    led.data.setdefault("closed", []).append(
        {"symbol": symbol, "exit_ms": exit_ms, "reason": reason.value, "net_pnl": profit - fees})
    led.owned.pop(symbol, None)


def _reconcile(rl: Any, led: Any, now_ms: int, snap: dict[str, Any]) -> None:
    positions = {r["symbol"]: r for r in snap["positions"]}
    resting = {str(logic.pick(r, "symbol", default="")) for r in snap["orders"]}
    fills_norm = [logic.normalize_fill(f) for f in snap["fills"]]
    for symbol, rec in list(led.owned.items()):
        spec = logic.CONTRACT_SPECS.get(symbol)
        pos = positions.get(symbol)
        if spec is None:
            continue
        if rec.get("status") == "pending":
            if symbol in resting:
                continue
            if pos is not None:
                rec["status"] = "open"
                rec["fill_ms"] = pos["ctime_ms"] or now_ms
                rl.add(now_ms, symbol, "entry_fill", RC.ORDER_FILLED, intended_price=rec["plan"]["entry"],
                       filled_price=pos["open_px"], qty=pos["size"], margin_mode=pos["margin_mode"] or "unverified")
            elif any(f["symbol"] == symbol and (f["ts_ms"] or 0) >= int(rec.get("placed_ms", 0)) for f in fills_norm):
                rec["status"] = "open"
                rec["fill_ms"] = rec.get("placed_ms")
            else:
                rl.add(now_ms, symbol, "entry_ended", RC.ORDER_EXPIRED_UNFILLED, intended_price=rec["plan"]["entry"])
                led.owned.pop(symbol, None)
                continue
        if rec.get("status") == "open" and pos is None:
            _finalize_closed(rl, led, now_ms, symbol, rec, snap["fills"], spec)
        elif rec.get("status") == "open" and pos is not None:
            if pos["margin_mode"] and pos["margin_mode"] not in ("isolated", "isolation"):
                _alert(rl, now_ms, symbol, RC.HALT_MARGIN_MODE_MISMATCH,
                       "position margin mode is not isolated; entries halted, position untouched",
                       margin_mode=pos["margin_mode"])
                rec["margin_mode_alert"] = True


def _manage(rl: Any, led: Any, now_ms: int, p: Any) -> None:
    for symbol, rec in list(led.owned.items()):
        if rec.get("status") == "pending" and now_ms >= int(rec.get("expire_ms", 0)):
            cut = int(rec["expire_ms"]) < int(rec["placed_ms"]) + int(p.entry_expiry_hours * HOUR_MS)
            reason = RC.ORDER_CANCELLED_FUNDING_WINDOW if cut else RC.ORDER_EXPIRED_UNFILLED
            outcome: dict[str, Any] = {}

            def _cancel(sym: str = symbol, out: dict[str, Any] = outcome) -> dict[str, Any]:
                out.update(_execution().cancel_entry(sym))
                return out

            _emit("close", symbol, reason, {"cancel_unfilled_entry": 1},
                  {"text": "cancel unfilled entry order (no position involved)", "kind": "cancel_entry"}, _cancel)
            rl.add(now_ms, symbol, "cancel_entry", reason, intended_price=rec["plan"]["entry"], **outcome)
            if outcome.get("ok"):
                led.owned.pop(symbol, None)
        elif rec.get("status") == "open" and not rec.get("time_stop_requested"):
            age = now_ms - int(rec.get("fill_ms") or rec.get("placed_ms") or now_ms)
            if age >= int(p.time_stop_hours * HOUR_MS):
                outcome = {}

                def _close(sym: str = symbol, out: dict[str, Any] = outcome) -> dict[str, Any]:
                    out.update(_execution().time_stop_close(sym))
                    return out

                _emit("close", symbol, RC.EXIT_TIME_STOP, {"age_hours": age / HOUR_MS},
                      {"text": "time stop reached", "kind": "time_stop"}, _close)
                if outcome:
                    rec["time_stop_requested"] = True
                rl.add(now_ms, symbol, "time_stop_close", RC.EXIT_TIME_STOP, age_hours=age / HOUR_MS, **outcome)


def _gate(rl: Any, led: Any, now_ms: int, snap: dict[str, Any], p: Any) -> Optional[Any]:
    """Return the reason new entries are blocked this run, or None. Never mutates."""
    foreign = sorted(r["symbol"] for r in snap["positions"] if r["symbol"] not in led.owned)
    if foreign:
        _alert(rl, now_ms, ",".join(foreign), RC.HALT_FOREIGN_POSITION,
               "position(s) not opened by this Playbook; not touching them, no new entries", symbols=foreign)
        return RC.HALT_FOREIGN_POSITION
    summary = logic.realised_summary(
        snap["fills"], owned_symbols=set(p.symbols), now_ms=now_ms,
        reset_after_ms=int(p.halt_reset_after_ts_ms),
    )
    if not summary["pnl_available"]:
        _alert(rl, now_ms, "*", RC.HALT_PNL_UNAVAILABLE, "closing fills carry no realised-PnL field; failing closed")
        return RC.HALT_PNL_UNAVAILABLE
    latch = led.data.get("latch")
    if latch and int(p.halt_reset_after_ts_ms) > int(latch.get("ts_ms", 0)):
        led.data["latch"] = latch = None
    if summary["day_pnl"] <= -p.hard_stop_usdt and not latch:
        led.data["latch"] = latch = {"reason": RC.HALT_DAILY_LOSS_STOP.value, "ts_ms": now_ms}
    if latch:
        _alert(rl, now_ms, "*", RC.HALT_DAILY_LOSS_STOP,
               "hard daily loss stop latched; no new entries until halt_reset_after_ts_ms is raised",
               day_pnl=summary["day_pnl"])
        return RC.HALT_DAILY_LOSS_STOP
    if summary["loss_streak"] >= p.max_consecutive_losses:
        _alert(rl, now_ms, "*", RC.HALT_CONSEC_LOSSES,
               "consecutive-loss halt; raise halt_reset_after_ts_ms to resume", streak=summary["loss_streak"])
        return RC.HALT_CONSEC_LOSSES
    if summary["day_pnl"] <= -p.daily_pause_usdt:
        _alert(rl, now_ms, "*", RC.PAUSE_DAILY_LOSS, "daily realised loss pause", day_pnl=summary["day_pnl"])
        return RC.PAUSE_DAILY_LOSS
    return None


def _features_for(symbol: str, latest_open: int, p: Any) -> Any:
    need = int(p.atr_pct_lookback_bars) + 110
    bars = features.fetch_klines(symbol, latest_open - need * HOUR_MS, latest_open + HOUR_MS)
    if bars.empty or int(bars.index.max().timestamp() * 1000) != latest_open:
        raise features.DataError(f"{symbol}: replay bars do not end at the expected latest closed bar")
    engine = logic.IndicatorEngine(
        ema_fast=p.ema_fast, ema_slow=p.ema_slow, adx_period=p.adx_period, atr_period=p.atr_period,
        atr_pct_lookback=p.atr_pct_lookback_bars, atr_pct_min_history=p.atr_pct_min_history_bars,
        volume_lookback=p.volume_lookback_bars,
    )
    feats = None
    for row in bars[["high", "low", "close", "volume"]].itertuples(index=False):
        feats = engine.update(float(row.high), float(row.low), float(row.close), float(row.volume))
    return feats


def _scan_entries(rl: Any, led: Any, now_ms: int, p: Any) -> None:
    for symbol in p.symbols:
        if symbol in led.owned:
            continue
        if len(led.owned) >= p.max_concurrent:
            rl.add(now_ms, symbol, "no_trade", RC.SKIP_MAX_CONCURRENT, echo=False)
            continue
        spec = logic.CONTRACT_SPECS[symbol]
        try:
            latest = features.latest_closed_bar_open_ms(symbol)
        except Exception as exc:  # noqa: BLE001
            _alert(rl, now_ms, symbol, RC.HALT_DATA_ERROR, "market data request failed; no entry", error=str(exc)[:200])
            continue
        status = logic.bar_freshness(now_ms, latest, int(p.stale_data_seconds))
        if status == "stale":
            _alert(rl, now_ms, symbol, RC.HALT_STALE_DATA, "latest closed bar older than the staleness limit; no entry",
                   latest_bar=logic.iso(latest) if latest else None)
            continue
        if status == "not_yet" or led.last_bar_ms.get(symbol) == latest:
            continue
        if now_ms - (latest + HOUR_MS) > int(p.entry_max_signal_age_minutes) * logic.MINUTE_MS:
            led.last_bar_ms[symbol] = latest
            rl.add(now_ms, symbol, "no_trade", RC.SKIP_SIGNAL_STALE, echo=False, bar=logic.iso(latest))
            continue
        try:
            feats = _features_for(symbol, latest, p)
        except Exception as exc:  # noqa: BLE001
            _alert(rl, now_ms, symbol, RC.HALT_DATA_ERROR, "could not build indicators; no entry", error=str(exc)[:200])
            continue
        led.last_bar_ms[symbol] = latest
        reason = logic.evaluate_signal(feats, p)
        if reason in (RC.NO_SIGNAL, RC.REGIME_WARMUP):
            rl.add(now_ms, symbol, "no_trade", reason, echo=False, bar=logic.iso(latest))
            continue
        if reason != RC.SIGNAL_LONG_ENTRY:
            rl.add(now_ms, symbol, "no_trade", reason, adx=feats.adx, atr_pct_rank=feats.atr_pct_rank, vol_ratio=feats.vol_ratio)
            continue
        _try_entry(rl, led, now_ms, p, symbol, spec, feats, latest)


def _try_entry(rl: Any, led: Any, now_ms: int, p: Any, symbol: str, spec: Any, feats: Any, latest: int) -> None:
    def skip(why: Any, **detail: Any) -> None:
        rl.add(now_ms, symbol, "no_trade", why, intended_price=feats.close, **detail)

    if logic.in_funding_window(now_ms, int(p.funding_window_minutes), p.funding_hours_utc):
        return skip(RC.NO_TRADE_FUNDING_WINDOW)
    try:
        mark = features.mark_snapshot(symbol)
    except Exception as exc:  # noqa: BLE001
        return skip(RC.SKIP_FUNDING_UNAVAILABLE, error=str(exc)[:200])
    rate = mark.get("last_funding_rate")
    if rate is None:
        return skip(RC.SKIP_FUNDING_UNAVAILABLE)
    if logic.funding_adverse(rate, "long", p.funding_adverse_max):
        return skip(RC.SKIP_FUNDING_RATE_ADVERSE, funding_rate=rate)
    ok, why = _execution().verify_rules(symbol, spec)
    if not ok:
        return skip(RC.SKIP_CONFIG_MISMATCH, detail_text=why)
    open_notional = sum(float(r.get("plan", {}).get("notional", 0.0)) for r in led.owned.values())
    plan, reason = logic.plan_long_entry(
        close=feats.close, atr=feats.atr, spec=spec, p=p, equity=p.equity_basis, open_notional=open_notional,
    )
    if plan is None:
        return skip(reason, atr=feats.atr)

    expire_ms = logic.entry_expiry_ms(now_ms, p)
    outcome: dict[str, Any] = {}

    def _place() -> dict[str, Any]:
        outcome.update(_execution().place_entry(symbol, plan, int(p.leverage_cap)))
        return outcome

    metrics = {"adx": feats.adx, "atr": feats.atr, "atr_pct_rank": feats.atr_pct_rank, "vol_ratio": feats.vol_ratio,
               "qty": float(plan.qty), "risk_at_stop_usdt": plan.risk_at_stop_usdt, "required_leverage": plan.required_leverage}
    meta = {"text": "long entry: trend-structure trigger inside regime filter", "entry": str(plan.entry),
            "stop": str(plan.stop), "take_profit": str(plan.take_profit), "bar": logic.iso(latest),
            "funding_rate": rate, "param_hash": logic.param_hash(p)}
    _emit("long", symbol, RC.SIGNAL_LONG_ENTRY, metrics, meta, _place)
    if outcome.get("ok"):
        led.owned[symbol] = {
            "status": "pending", "order_id": outcome.get("order_id", ""), "placed_ms": now_ms, "expire_ms": expire_ms,
            "plan": {"entry": float(plan.entry), "stop": float(plan.stop), "take_profit": float(plan.take_profit),
                     "qty": float(plan.qty), "notional": plan.notional, "risk": plan.risk_at_stop_usdt},
        }
        rl.add(now_ms, symbol, "place_entry", RC.ORDER_PLACED, intended_price=plan.entry, qty=plan.qty,
               stop=str(plan.stop), take_profit=str(plan.take_profit), sl_attached=outcome.get("sl_attached"),
               expire=logic.iso(expire_ms), funding_rate=rate)
    elif outcome:
        rl.add(now_ms, symbol, "order_failed", RC(outcome.get("reason", RC.ORDER_REJECTED.value)), intended_price=plan.entry,
               detail_text=str(outcome.get("detail", ""))[:300])
    else:
        rl.add(now_ms, symbol, "signal_only", RC.SIGNAL_LONG_ENTRY, intended_price=plan.entry, qty=plan.qty,
               note="subscription is not follow_trade; no order placed")


def run() -> None:
    now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
    p = logic.load_params(dict(runtime.manifest.get("strategy_config", {}) or {}))
    rl = ledger_mod.RunLog()
    led = ledger_mod.Ledger.load()
    try:
        try:
            snap = _execution().read_snapshot()
        except Exception as exc:  # noqa: BLE001
            _alert(rl, now_ms, "*", RC.HALT_DATA_ERROR, "account snapshot failed; nothing evaluated", error=str(exc)[:200])
            return
        _reconcile(rl, led, now_ms, snap)
        _manage(rl, led, now_ms, p)
        gate = _gate(rl, led, now_ms, snap, p)
        if gate is None:
            _scan_entries(rl, led, now_ms, p)
        if not led.save() and (led.owned or snap["positions"]):
            rl.add(now_ms, "*", "alert", RC.HALT_STATE_UNAVAILABLE, text="could not persist .state ledger")
    finally:
        led.save()
        rl.flush()
        _emit("watch", p.symbols[0], RC.NO_SIGNAL, {"records": len(rl.records)},
              {"text": "run summary", "reason_counts": rl.counts, "ledger_loaded": led.loaded})


if __name__ == "__main__":
    run()
