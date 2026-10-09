"""Live execution (runtime.is_live()).

Per scheduled run (hourly, just after the 1h bar closes):
  scan   -> fresh closed 1h bars, ticker, current funding for every symbol
  filter -> liquidity, staleness, circuit breakers, cluster slot, regime
  trigger-> strongest-ADX pullback candidate -> EntryPlan
  order  -> limit buy with attached TP/SL (isolated margin) inside the
            emit_signal_or_follow callback only
  manage -> cancel unfilled entries after max age, time-stop open positions,
            alert on positions this Playbook did not open (never touched)
  exit   -> TP / SL are exchange-side plan orders; time stop closes at market
  log    -> every action with timestamp, symbol, side, intended vs filled
            price, fees, funding, reason code -> /workspace/output/live_action_log.json

Persistent state lives in /workspace/.state/ (the only runner-synced path).
"""
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from getagent import data, runtime

from . import features
from .rules import EntryPlan, InstrumentRules, Reason, RiskState, build_entry_plan

STATE_PATH = Path("/workspace/.state/trend_pullback_state.json")
OUTPUT_DIR = Path("/workspace/output")
LOG: list[dict[str, Any]] = []


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #
def _now() -> datetime:
    return datetime.now(timezone.utc)


def _log(**entry: Any) -> None:
    entry.setdefault("ts", _now().isoformat())
    entry.setdefault("mode", "live")
    LOG.append(entry)


def _params() -> dict[str, Any]:
    cfg = dict(runtime.manifest.get("strategy_config", {}) or {})
    cfg["margin_budget"] = float(cfg.get("margin_budget", "500") or 500)
    return cfg


def _load_state() -> dict[str, Any]:
    if STATE_PATH.exists():
        try:
            return json.loads(STATE_PATH.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001 - corrupt state is reported, not silently trusted
            _log(action="STATE_CORRUPT", reason_code="STATE_RESET", symbol="", side="")
    return {"version": 1, "risk": {}, "slot": None, "foreign_alerts": []}


def _save_state(state: dict[str, Any]) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    state["last_run"] = _now().isoformat()
    STATE_PATH.write_text(json.dumps(state, default=str), encoding="utf-8")


def _records(payload: Any) -> list[dict[str, Any]]:
    """Normalise an SDK envelope / dict / list into a list of dict rows."""
    if payload is None:
        return []
    raw = getattr(payload, "raw", None)
    if raw is not None and not isinstance(payload, (dict, list)):
        payload = raw
    if isinstance(payload, list):
        return [r for r in payload if isinstance(r, dict)]
    if isinstance(payload, dict):
        for key in ("data", "result", "list", "fills", "orders", "entrustedList", "fillList", "positions"):
            inner = payload.get(key)
            if isinstance(inner, list):
                return [r for r in inner if isinstance(r, dict)]
            if isinstance(inner, dict):
                nested = _records(inner)
                if nested:
                    return nested
    return []


def _get(row: dict[str, Any], *keys: str, default: Any = None) -> Any:
    for key in keys:
        if key in row and row[key] not in (None, ""):
            return row[key]
    return default


def _float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _decimals(step: float) -> int:
    """Number of decimal places implied by a price/size step (0.001 -> 3)."""
    if step >= 1:
        return 0
    text = f"{step:.12f}".rstrip("0")
    return len(text.split(".")[1]) if "." in text else 0


# --------------------------------------------------------------------------- #
# exchange reads (allowed outside callbacks; mutations are not)
# --------------------------------------------------------------------------- #
def _read_exchange(symbols: list[str]) -> dict[str, Any]:
    out: dict[str, Any] = {"ok": False, "positions": {}, "pending": {}, "error": ""}
    try:
        from getagent import trade

        current = trade.contract.current_position()
        for rec in trade.helpers.contract_position_records(current):
            sym = str(_get(rec, "symbol", default="")).upper()
            size = _float(_get(rec, "total", "size", "available", "holdAmount", default=0))
            if sym and size > 0:
                out["positions"][sym] = rec
        for sym in symbols:
            pending = trade.contract.pending_orders(symbol=sym)
            out["pending"][sym] = _records(pending)
        out["ok"] = True
    except Exception as exc:  # noqa: BLE001 - signal-only subscriptions have no bound account
        out["error"] = str(exc)[:300]
    return out


def _fills_for(symbol: str, order_id: str = "") -> list[dict[str, Any]]:
    try:
        from getagent import trade

        return _records(trade.contract.fills(symbol=symbol, order_id=order_id, limit=100))
    except Exception:  # noqa: BLE001
        return []


def _pnl_from_fills(symbol: str, since: datetime) -> dict[str, Any]:
    """Best-effort realised PnL for the slot from exchange fills since ``since``."""
    fills = _fills_for(symbol)
    buy_notional = sell_notional = buy_qty = sell_qty = fees = 0.0
    last_sell_px = None
    for f in fills:
        ts_ms = _float(_get(f, "cTime", "ctime", "ts", "timestamp", default=0))
        if ts_ms and datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc) < since - timedelta(minutes=5):
            continue
        price = _float(_get(f, "price", "priceAvg", "fillPrice", default=0))
        qty = _float(_get(f, "baseVolume", "size", "fillSize", "qty", default=0))
        side = str(_get(f, "side", "tradeSide", default="")).lower()
        fee_entries = f.get("feeDetail") if isinstance(f.get("feeDetail"), list) else None
        if fee_entries:
            fees += sum(abs(_float(_get(x, "totalFee", "fee", default=0))) for x in fee_entries)
        else:
            fees += abs(_float(_get(f, "fee", "totalFee", default=0)))
        if "buy" in side or side == "open_long":
            buy_notional += price * qty
            buy_qty += qty
        elif "sell" in side or side == "close_long":
            sell_notional += price * qty
            sell_qty += qty
            last_sell_px = price
    known = buy_qty > 0 and sell_qty > 0
    realised = (sell_notional - buy_notional) - fees if known else 0.0
    return {
        "known": known,
        "realised": round(realised, 6),
        "fees": round(fees, 6),
        "avg_buy": round(buy_notional / buy_qty, 6) if buy_qty else None,
        "avg_sell": round(sell_notional / sell_qty, 6) if sell_qty else None,
        "last_sell_px": last_sell_px,
        "fills": len(fills),
    }


def _instrument_rules(symbol: str, params: dict[str, Any]) -> tuple[InstrumentRules, str]:
    """Live quantisation rules: Trade SDK contract rules, else authoring snapshot."""
    snapshot = (params.get("instrument_rules_snapshot") or {}).get(symbol) or {}
    try:
        from getagent import trade

        rules = trade.helpers.contract_rules(symbol)
        tick = _float(getattr(rules, "price_step", None), 0.0)
        size_step = _float(getattr(rules, "size_step", None) or getattr(rules, "qty_step", None), 0.0)
        min_qty = _float(getattr(rules, "min_qty", None) or getattr(rules, "min_size", None), 0.0)
        min_notional = _float(getattr(rules, "min_notional", None) or getattr(rules, "min_order_amount", None), 0.0)
        if tick > 0 and size_step > 0:
            return (
                InstrumentRules(
                    tick=tick,
                    size_step=size_step,
                    min_qty=min_qty or size_step,
                    min_notional=min_notional or _float(snapshot.get("min_notional"), 5.0),
                    price_precision=_decimals(tick),
                    size_precision=_decimals(size_step),
                ),
                "LIVE_CONTRACT_RULES",
            )
    except Exception:  # noqa: BLE001
        pass
    if not snapshot:
        raise RuntimeError(f"no instrument rules available for {symbol}")
    return (
        InstrumentRules(
            tick=_float(snapshot["tick"]),
            size_step=_float(snapshot["size_step"]),
            min_qty=_float(snapshot["min_qty"]),
            min_notional=_float(snapshot.get("min_notional"), 5.0),
            price_precision=int(snapshot["price_precision"]),
            size_precision=int(snapshot["size_precision"]),
        ),
        "RULES_FALLBACK_SNAPSHOT",
    )


# --------------------------------------------------------------------------- #
# market scan
# --------------------------------------------------------------------------- #
def _scan_symbol(symbol: str, params: dict[str, Any], now: datetime) -> dict[str, Any]:
    exchange = str(params.get("data_exchange", "bitget"))
    out: dict[str, Any] = {"symbol": symbol, "block": Reason.OK, "notes": []}
    bars_raw = data.crypto.futures.kline(
        symbol=symbol, interval="1h", exchange=exchange, limit=1000, closed_only=True
    )
    bars = features._normalize_bars(features._frame_from_obb(bars_raw))  # noqa: SLF001 - shared helper
    if bars.empty or len(bars) < int(params["ema_slow_period"]) + 50:
        out["block"] = Reason.SIGNAL_INVALID
        out["notes"].append("insufficient bars")
        return out
    if not features.latest_closed_bar_is_fresh(bars.index, now):
        out["block"] = Reason.DATA_STALE
        out["notes"].append("bar feed stale")
        return out
    enriched = features.compute_indicators(bars, params)
    row = enriched.iloc[-1].to_dict()
    out["row"] = row
    out["last_bar_open"] = enriched.index[-1].isoformat()

    # Ticker: spread / 24h volume / quote age.
    spread_bps = None
    quote_volume = None
    try:
        ticker_df = features._frame_from_obb(  # noqa: SLF001
            data.crypto.futures.ticker(symbol=symbol, exchange=exchange)
        )
        if not ticker_df.empty:
            t = ticker_df.iloc[-1].to_dict()
            bid, ask = _float(t.get("bid")), _float(t.get("ask"))
            if bid > 0 and ask > 0:
                spread_bps = (ask - bid) / ((ask + bid) / 2) * 10_000
            quote_volume = _float(t.get("quote_volume"), 0.0) or None
            stamp = t.get("timestamp")
            if stamp not in (None, ""):
                try:
                    quote_time = pd.Timestamp(stamp)
                    if quote_time.tzinfo is None:
                        quote_time = quote_time.tz_localize("UTC")
                    age = (pd.Timestamp(now) - quote_time).total_seconds()
                    out["quote_age_seconds"] = round(age, 1)
                    if age > float(params["max_quote_age_seconds"]):
                        out["block"] = Reason.DATA_STALE
                        out["notes"].append("quote older than limit")
                        return out
                except Exception:  # noqa: BLE001
                    out["notes"].append("QUOTE_AGE_UNKNOWN")
            else:
                out["notes"].append("QUOTE_AGE_UNKNOWN")
    except Exception as exc:  # noqa: BLE001
        out["notes"].append(f"ticker unavailable: {str(exc)[:80]}")
    out["spread_bps"] = None if spread_bps is None else round(spread_bps, 3)
    out["quote_volume_24h"] = quote_volume
    if spread_bps is not None and spread_bps > float(params["max_spread_bps"]):
        out["block"] = Reason.LIQUIDITY_SPREAD
        return out
    if quote_volume is not None and quote_volume < float(params["min_24h_volume_usdt"]):
        out["block"] = Reason.LIQUIDITY_VOLUME
        return out
    if spread_bps is None:
        out["notes"].append("SPREAD_UNKNOWN")
    if quote_volume is None:
        out["notes"].append("VOLUME_UNKNOWN")

    # Current funding rate (latest row).
    funding_rate = None
    try:
        fr_df = features._frame_from_obb(  # noqa: SLF001
            data.crypto.futures.funding_rate(symbol=symbol, exchange=exchange, interval="1h", limit=3)
        )
        if not fr_df.empty and "funding_rate" in fr_df.columns:
            funding_rate = _float(fr_df["funding_rate"].dropna().iloc[-1]) if fr_df["funding_rate"].notna().any() else None
    except Exception:  # noqa: BLE001
        funding_rate = None
    out["funding_rate"] = funding_rate
    return out


# --------------------------------------------------------------------------- #
# trade mutations: only ever invoked through emit_signal_or_follow callbacks
# --------------------------------------------------------------------------- #
def _execute_cancel(symbol: str, order_id: str) -> dict[str, Any]:
    from getagent import trade

    pending = trade.contract.pending_orders(symbol=symbol)
    still_open = any(str(_get(o, "orderId", "order_id", default="")) == str(order_id) for o in _records(pending))
    if not still_open:
        return {"status": "not_pending"}
    result = trade.contract.cancel_order(symbol=symbol, order_id=str(order_id))
    if not trade.is_success(result):
        raise RuntimeError(f"cancel failed: {result}")
    after = trade.contract.pending_orders(symbol=symbol)
    verified = not any(str(_get(o, "orderId", "order_id", default="")) == str(order_id) for o in _records(after))
    return {"status": "cancelled", "verified": verified}


def _execute_close(symbol: str) -> dict[str, Any]:
    from getagent import trade

    current = trade.contract.current_position(symbol=symbol)
    position = trade.helpers.find_contract_position(current, symbol=symbol, hold_side="long")
    if position is None:
        return {"status": "flat"}
    result = trade.contract.close_position(symbol=symbol, hold_side="long")
    if not trade.is_success(result):
        raise RuntimeError(f"close failed: {result}")
    after = trade.contract.current_position(symbol=symbol)
    remaining = trade.helpers.find_contract_position(after, symbol=symbol, hold_side="long")
    return {"status": "closed", "verified": remaining is None}


def _execute_entry(plan: EntryPlan, slot_ref: dict[str, Any]) -> dict[str, Any]:
    from getagent import trade

    symbol = plan.symbol
    lever = trade.contract.change_leverage(symbol=symbol, leverage=plan.leverage)
    if not trade.is_success(lever):
        raise RuntimeError(f"leverage change failed: {lever}")
    qty_plan = trade.helpers.compute_qty(
        symbol=symbol,
        market="contract",
        budget_amount=f"{plan.margin:.4f}",
        leverage=plan.leverage,
        price=f"{plan.limit_price}",
    )
    qty = qty_plan.qty
    tpsl = trade.helpers.resolve_contract_tpsl(
        symbol=symbol,
        side="long",
        leverage=plan.leverage,
        tp_trigger_price=f"{plan.tp_price}",
        sl_trigger_price=f"{plan.stop_price}",
        reference_price=f"{plan.limit_price}",
    )
    result = trade.contract.place_order(
        symbol=symbol,
        side="buy",
        order_type="limit",
        qty=qty,
        price=f"{plan.limit_price}",
        margin_mode="isolated",
        tp_trigger_price=tpsl.tp_trigger_price,
        sl_trigger_price=tpsl.sl_trigger_price,
    )
    if not trade.is_success(result):
        raise RuntimeError(f"entry order failed: {result}")
    raw = getattr(result, "raw", result)
    order_id = getattr(result, "order_id", None)
    if not order_id and isinstance(raw, dict):
        order_id = _get(raw, "orderId", "order_id") or _get(raw.get("data") or {}, "orderId", "order_id")
    slot_ref.update({
        "state": "pending",
        "symbol": symbol,
        "order_id": str(order_id or ""),
        "placed_at": _now().isoformat(),
        "qty": str(qty),
        "tp": str(tpsl.tp_trigger_price),
        "sl": str(tpsl.sl_trigger_price),
    })
    return {"order_id": str(order_id or ""), "qty": str(qty), "tp": str(tpsl.tp_trigger_price), "sl": str(tpsl.sl_trigger_price)}


# --------------------------------------------------------------------------- #
# main
# --------------------------------------------------------------------------- #
def run() -> None:
    now = _now()
    params = _params()
    symbols = [str(s).upper() for s in (params.get("trading_symbols") or ["BTCUSDT"])]
    state = _load_state()
    risk = RiskState.from_dict(state.get("risk"))
    risk.roll_day(now)
    slot: dict[str, Any] | None = state.get("slot")
    follow = runtime.is_follow_trade()
    exch = _read_exchange(symbols) if follow else {"ok": False, "positions": {}, "pending": {}, "error": "not follow_trade"}

    # ---- foreign positions: alert, never touch, block cluster entries -------
    foreign = [s for s in exch["positions"] if not (slot and slot.get("symbol") == s)]
    for sym in foreign:
        rec = exch["positions"][sym]
        _log(action=Reason.FOREIGN_POSITION, symbol=sym, side=str(_get(rec, "holdSide", "hold_side", default="")),
             intended_price=None, filled_price=_float(_get(rec, "openPriceAvg", "averageOpenPrice", "open_price", default=0)) or None,
             qty=_float(_get(rec, "total", "size", default=0)), fees=None, funding=None, reason_code=Reason.FOREIGN_POSITION)
        runtime.emit_signal_or_follow(
            action="watch", symbol=sym, confidence=0.0,
            metrics={"foreign_position": 1},
            meta={"reason": "position not opened by this Playbook; left untouched"},
            reason_code=Reason.FOREIGN_POSITION,
            reason_text="Position not opened by this Playbook was found; it is left untouched and new entries are blocked.",
        )

    # ---- manage existing slot -----------------------------------------------
    if slot and exch["ok"]:
        sym = slot["symbol"]
        plan_d = slot.get("plan") or {}
        if slot["state"] == "pending":
            order_id = str(slot.get("order_id", ""))
            pending_ids = {str(_get(o, "orderId", "order_id", default="")) for o in exch["pending"].get(sym, [])}
            placed_at = datetime.fromisoformat(slot["placed_at"])
            if order_id and order_id in pending_ids:
                if now - placed_at >= timedelta(hours=float(params["entry_max_age_hours"])):
                    outcome = runtime.emit_signal_or_follow(
                        action="close", symbol=sym, confidence=0.0,
                        metrics={"order_age_hours": round((now - placed_at).total_seconds() / 3600, 2)},
                        meta={"order_id": order_id, "intended_price": plan_d.get("limit_price")},
                        reason_code=Reason.ENTRY_EXPIRED,
                        reason_text="Unfilled limit entry exceeded its maximum age and is cancelled.",
                        execute_trade=lambda: _execute_cancel(sym, order_id),
                    )
                    _log(action=Reason.ENTRY_EXPIRED, symbol=sym, side="buy", intended_price=plan_d.get("limit_price"),
                         filled_price=None, qty=plan_d.get("qty"), fees=0.0, funding=0.0,
                         reason_code=Reason.ENTRY_EXPIRED, result=str(getattr(outcome, "trade_result", None))[:200])
                    slot = None
            elif sym in exch["positions"]:
                rec = exch["positions"][sym]
                fill_px = _float(_get(rec, "openPriceAvg", "averageOpenPrice", "open_price", default=0)) or plan_d.get("limit_price")
                fills = _fills_for(sym, order_id) if order_id else []
                fill_ts = None
                fee = 0.0
                for f in fills:
                    ts_ms = _float(_get(f, "cTime", "ctime", "ts", default=0))
                    if ts_ms:
                        fill_ts = datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc)
                    fee += abs(_float(_get(f, "fee", "totalFee", default=0)))
                slot.update({
                    "state": "open",
                    "fill_price": fill_px,
                    "fill_time": (fill_ts or now).isoformat(),
                    "fill_time_source": "fills" if fill_ts else "run_time_upper_bound",
                    "entry_fees": round(fee, 6),
                })
                _log(action=Reason.ENTRY_FILLED, symbol=sym, side="buy", intended_price=plan_d.get("limit_price"),
                     filled_price=fill_px, qty=_float(_get(rec, "total", "size", default=0)), fees=round(fee, 6),
                     funding=0.0, reason_code=Reason.ENTRY_FILLED)
            else:
                pnl = _pnl_from_fills(sym, placed_at)
                if pnl["known"]:
                    events = risk.register_close(now, pnl["realised"], params)
                    exit_reason = Reason.STOP_HIT
                    if pnl["last_sell_px"] is not None and plan_d.get("tp_price") and plan_d.get("stop_price"):
                        exit_reason = Reason.TP_HIT if abs(pnl["last_sell_px"] - float(plan_d["tp_price"])) < abs(pnl["last_sell_px"] - float(plan_d["stop_price"])) else Reason.STOP_HIT
                    _log(action=exit_reason, symbol=sym, side="sell", intended_price=None, filled_price=pnl["avg_sell"],
                         qty=None, fees=pnl["fees"], funding="PENDING(exchange statement)", reason_code=";".join([exit_reason, *events]),
                         realized_pnl=pnl["realised"])
                else:
                    _log(action="SLOT_RESOLVED_EXTERNALLY", symbol=sym, side="", intended_price=plan_d.get("limit_price"),
                         filled_price=None, qty=None, fees=None, funding=None, reason_code="PNL_UNKNOWN")
                slot = None
        elif slot["state"] == "open":
            fill_time = datetime.fromisoformat(slot["fill_time"])
            if sym in exch["positions"]:
                if now - fill_time >= timedelta(hours=float(params["time_stop_hours"])):
                    outcome = runtime.emit_signal_or_follow(
                        action="close", symbol=sym, confidence=1.0,
                        metrics={"held_hours": round((now - fill_time).total_seconds() / 3600, 2)},
                        meta={"fill_price": slot.get("fill_price")},
                        reason_code=Reason.TIME_STOP,
                        reason_text="Maximum holding time reached; position closed at market.",
                        execute_trade=lambda: _execute_close(sym),
                    )
                    pnl = _pnl_from_fills(sym, fill_time - timedelta(hours=6))
                    realised = pnl["realised"] if pnl["known"] else 0.0
                    events = risk.register_close(now, realised, params) if pnl["known"] else []
                    _log(action=Reason.TIME_STOP, symbol=sym, side="sell", intended_price=None,
                         filled_price=pnl["avg_sell"], qty=None, fees=pnl["fees"], funding="PENDING(exchange statement)",
                         reason_code=";".join([Reason.TIME_STOP, *events]) if events else Reason.TIME_STOP,
                         realized_pnl=realised if pnl["known"] else "PNL_UNKNOWN",
                         result=str(getattr(outcome, "trade_result", None))[:200])
                    slot = None
            else:
                pnl = _pnl_from_fills(sym, fill_time - timedelta(hours=6))
                if pnl["known"]:
                    events = risk.register_close(now, pnl["realised"], params)
                    exit_reason = Reason.STOP_HIT
                    if pnl["last_sell_px"] is not None and plan_d.get("tp_price") and plan_d.get("stop_price"):
                        exit_reason = Reason.TP_HIT if abs(pnl["last_sell_px"] - float(plan_d["tp_price"])) < abs(pnl["last_sell_px"] - float(plan_d["stop_price"])) else Reason.STOP_HIT
                    _log(action=exit_reason, symbol=sym, side="sell",
                         intended_price=plan_d.get("tp_price") if exit_reason == Reason.TP_HIT else plan_d.get("stop_price"),
                         filled_price=pnl["avg_sell"], qty=None, fees=pnl["fees"], funding="PENDING(exchange statement)",
                         reason_code=";".join([exit_reason, *events]) if events else exit_reason, realized_pnl=pnl["realised"])
                else:
                    _log(action="POSITION_CLOSED_EXTERNALLY", symbol=sym, side="sell", intended_price=None,
                         filled_price=None, qty=None, fees=None, funding=None, reason_code="PNL_UNKNOWN")
                slot = None
    # ---- daily hard stop: the Playbook cannot stop itself; alert the user ----
    if risk.daily_realised <= -abs(float(params["daily_stop_usdt"])) and state.get("hard_stop_alert_day") != risk.day_key:
        state["hard_stop_alert_day"] = risk.day_key
        runtime.emit_signal_or_follow(
            action="watch", symbol=symbols[0], confidence=0.0,
            metrics={"daily_realised": round(risk.daily_realised, 4)},
            meta={"instruction": "Daily hard stop reached. Stop this Playbook from the GetAgent page; entries are blocked until the next UTC day."},
            reason_code=Reason.HARD_STOP,
            reason_text="Daily realised loss reached the hard stop; no further entries today.",
        )
        _log(action=Reason.HARD_STOP, symbol="", side="", intended_price=None, filled_price=None, qty=None,
             fees=None, funding=None, reason_code=Reason.HARD_STOP, daily_realised=round(risk.daily_realised, 4))

    # ---- entry evaluation ----------------------------------------------------
    block = Reason.OK
    if slot is not None:
        block = Reason.SLOT_OCCUPIED
    elif foreign:
        block = Reason.FOREIGN_POSITION
    else:
        block = risk.entry_block_reason(now, params)

    scans: dict[str, dict[str, Any]] = {}
    best: EntryPlan | None = None
    best_scan: dict[str, Any] | None = None
    skip_reasons: dict[str, str] = {}
    if block == Reason.OK:
        for sym in symbols:
            try:
                scan = _scan_symbol(sym, params, now)
            except Exception as exc:  # noqa: BLE001 - AI/signal layer failure -> no trade
                scan = {"symbol": sym, "block": Reason.SIGNAL_INVALID, "notes": [str(exc)[:120]]}
            scans[sym] = scan
            if scan["block"] != Reason.OK:
                skip_reasons[sym] = scan["block"]
                continue
            try:
                rules, rules_source = _instrument_rules(sym, params)
            except Exception as exc:  # noqa: BLE001
                skip_reasons[sym] = f"{Reason.SIZING_FAIL}:{str(exc)[:60]}"
                continue
            scan["rules_source"] = rules_source
            plan, reason = build_entry_plan(
                symbol=sym, row=scan["row"], params=params, rules=rules, decision_time=now,
                funding_rate=scan.get("funding_rate"), funding_known=scan.get("funding_rate") is not None,
            )
            if plan is None:
                skip_reasons[sym] = reason
                continue
            if best is None or plan.adx > best.adx:
                best, best_scan = plan, scan

    if block == Reason.OK and best is not None:
        slot_ref: dict[str, Any] = {}
        plan = best
        outcome = runtime.emit_signal_or_follow(
            action="long", symbol=plan.symbol, confidence=min(1.0, plan.adx / 50.0),
            metrics={
                "limit_price": plan.limit_price, "stop_price": plan.stop_price, "tp_price": plan.tp_price,
                "qty": plan.qty, "notional_usdt": plan.notional, "margin_usdt": plan.margin,
                "risk_usdt": plan.risk_usdt, "leverage": plan.leverage, "adx": round(plan.adx, 2),
                "atr": round(plan.atr, 6), "expected_funding_usdt": plan.expected_funding_usdt,
                "spread_bps": (best_scan or {}).get("spread_bps"), "quote_volume_24h": (best_scan or {}).get("quote_volume_24h"),
                "sizing_ok": True, "min_open_notional_usdt": 5.0,
            },
            meta={"reasons": plan.reasons, "scan_notes": (best_scan or {}).get("notes"), "last_bar_open": (best_scan or {}).get("last_bar_open")},
            reason_code=Reason.ENTRY_PLACED,
            reason_text="Trend regime active; resting a pullback limit buy with attached stop and target.",
            execute_trade=lambda: _execute_entry(plan, slot_ref),
        )
        executed = bool(slot_ref.get("order_id"))
        if executed:
            slot_ref["plan"] = {
                "limit_price": plan.limit_price, "stop_price": plan.stop_price, "tp_price": plan.tp_price,
                "qty": plan.qty, "risk_usdt": plan.risk_usdt, "notional": plan.notional, "margin": plan.margin,
            }
            slot = slot_ref
        _log(action=Reason.ENTRY_PLACED if executed else "SIGNAL_ONLY", symbol=plan.symbol, side="buy",
             intended_price=plan.limit_price, filled_price=None, qty=plan.qty, fees=0.0,
             funding=plan.expected_funding_usdt, reason_code=";".join(plan.reasons),
             stop=plan.stop_price, take_profit=plan.tp_price, follow_trade=follow,
             result=str(getattr(outcome, "trade_result", None))[:200] if executed else ("not executed" if follow else Reason.NOT_FOLLOW_TRADE))
    else:
        reason = block if block != Reason.OK else (sorted(skip_reasons.values())[0] if skip_reasons else Reason.SIGNAL_INVALID)
        runtime.emit_signal_or_follow(
            action="hold", symbol=symbols[0], confidence=0.0,
            metrics={"candidates": len(symbols), "blocked": 1},
            meta={"block": block, "skip_reasons": skip_reasons,
                  "scans": {s: {k: v for k, v in sc.items() if k != "row"} for s, sc in scans.items()},
                  "risk_state": risk.to_dict()},
            reason_code=reason,
            reason_text="No trade: " + reason,
        )
        _log(action="NO_TRADE", symbol="", side="", intended_price=None, filled_price=None, qty=None,
             fees=0.0, funding=0.0, reason_code=reason, skip_reasons=skip_reasons)

    state["risk"] = risk.to_dict()
    state["slot"] = slot
    state["foreign_alerts"] = foreign
    state["exchange_read_error"] = exch.get("error", "")
    _save_state(state)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "live_action_log.json").write_text(json.dumps(LOG, default=str), encoding="utf-8")
