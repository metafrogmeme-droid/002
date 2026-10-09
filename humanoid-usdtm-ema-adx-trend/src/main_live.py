"""Live path: deterministic EMA-ADX long, optional AI veto, isolated limit+TPSL."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from getagent import data, runtime

from . import execution, features, risk

_INTERVAL_MS = 60 * 60 * 1000
_STATE_PATH = Path("/workspace/.state/playbook_state.json")
_LOG_PATH = Path("/workspace/.state/action_log.jsonl")


def _now_ms() -> int:
    return int(datetime.now(timezone.utc).timestamp() * 1000)


def _load_state() -> dict[str, Any]:
    if not _STATE_PATH.exists():
        return {
            "opened_symbols": [],
            "open_orders": {},
            "daily_realized": 0.0,
            "day": "",
            "playbook_realized": 0.0,
            "consecutive_losses": 0,
            "setup_bar": {},
        }
    return json.loads(_STATE_PATH.read_text(encoding="utf-8"))


def _save_state(state: dict[str, Any]) -> None:
    _STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    _STATE_PATH.write_text(json.dumps(state, default=str), encoding="utf-8")


def _log(row: dict[str, Any]) -> None:
    _LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with _LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, default=str) + "\n")


def _records(response: object) -> list[dict[str, Any]]:
    return [dict(row) for row in data.to_records(response)]


def _last_bar_open_ms(rows: list[dict[str, Any]]) -> int | None:
    stamps = [
        int(row["time"])
        for row in rows
        if isinstance(row.get("time"), (int, float)) and not isinstance(row.get("time"), bool)
    ]
    return max(stamps) if stamps else None


def _quote_stale(symbol: str, stale_ms: int) -> bool:
    from getagent import trade

    quote = trade.helpers.contract_price_quote(symbol)
    ts = None
    if hasattr(quote, "ts") and quote.ts:
        ts = int(quote.ts)
    elif isinstance(quote, dict):
        ts = quote.get("ts") or quote.get("timestamp")
    if ts is None:
        return False
    return _now_ms() - int(ts) > stale_ms


def _next_funding(symbol: str) -> float | None:
    payload = data.crypto.futures.funding_rate(
        symbol=symbol,
        exchange="bitget",
        interval="1h",
        limit=10,
    )
    rows = _records(payload)
    now = _now_ms()
    future = []
    for row in rows:
        raw = row.get("timestamp") or row.get("time") or row.get("date")
        try:
            if isinstance(raw, str) and raw.isdigit():
                ts = int(raw)
            elif isinstance(raw, str):
                ts = int(datetime.fromisoformat(raw.replace("Z", "+00:00")).timestamp() * 1000)
            else:
                ts = int(raw)
        except (TypeError, ValueError):
            continue
        rate = row.get("funding_rate")
        if rate in (None, ""):
            continue
        if ts >= now:
            future.append((ts, float(rate)))
    if not future:
        return None
    future.sort()
    return future[0][1]


def _ai_veto(symbol: str, snap: dict[str, Any]) -> str:
    """Return 'long', 'invalid', or 'unavailable'. Never invent a short."""
    try:
        from getagent import llm
    except Exception:
        return "unavailable"
    if not llm.is_available():
        return "unavailable"
    try:
        result = llm.complete(
            prompt=(
                f"A deterministic long setup exists for {symbol}. "
                "Reply LONG to confirm or INVALID to veto. Never output SHORT."
            ),
            system="You are a veto layer. Confirm or reject only. No new direction.",
            max_tokens=8,
            temperature=0,
        )
        text = (getattr(result, "content", "") or "").strip().upper()
        if "LONG" in text and "INVALID" not in text and "SHORT" not in text:
            return "long"
        return "invalid"
    except Exception:
        return "invalid"


def _bars(symbol: str, limit: int) -> list[dict[str, Any]]:
    payload = data.crypto.futures.kline(
        symbol=symbol,
        interval="1h",
        exchange="bitget",
        limit=limit,
        closed_only=True,
    )
    return _records(payload)


def run() -> None:
    cfg = risk.cfg(runtime.manifest)
    symbols = [str(item).upper() for item in (cfg.get("trading_symbols") or ["BTCUSDT"])]
    leverage = risk.cap_leverage(cfg.get("leverage"), 5)
    margin_budget = str(cfg.get("margin_budget") or "600")
    stale_ms = int(cfg.get("stale_quote_ms") or 60000)
    skip_rate = float(cfg.get("funding_skip_rate") or 0.0003)
    blackout = int(cfg.get("funding_blackout_minutes") or 15)
    ttl_hours = int(cfg.get("limit_ttl_hours") or 4)
    state = _load_state()
    today = datetime.now(timezone.utc).date().isoformat()
    if state.get("day") != today:
        state["day"] = today
        state["daily_realized"] = 0.0

    halt_reason = ""
    if int(state.get("consecutive_losses") or 0) >= int(cfg.get("max_consecutive_losses") or 5):
        halt_reason = "five_consecutive_losses"
    if float(state.get("playbook_realized") or 0) <= float(cfg.get("playbook_stop_usdt") or -40):
        halt_reason = "playbook_stop_loss"
    if float(state.get("daily_realized") or 0) <= float(cfg.get("daily_pause_usdt") or -30):
        halt_reason = halt_reason or "daily_pause"

    opened = set(state.get("opened_symbols") or [])
    aliens = []
    try:
        aliens = execution.alien_positions(opened_symbols=opened)
    except Exception as exc:
        aliens = [f"position_query_failed:{exc}"]
    if aliens:
        halt_reason = halt_reason or "alien_position"
        runtime.emit_signal_or_follow(
            action="watch",
            symbol=symbols[0],
            confidence=0.0,
            metrics={"alien_positions": len(aliens)},
            meta={"reason_code": "alien_position", "aliens": aliens},
            reason_code="alien_position",
            reason_text="Sub-account has a position this Playbook did not open; alert only, do not touch.",
        )
        _log(
            {
                "timestamp": _now_ms(),
                "symbol": "",
                "side": "",
                "intended_price": None,
                "filled_price": None,
                "fees": None,
                "funding": None,
                "reason_code": "alien_position",
                "detail": aliens,
            }
        )
        _save_state(state)
        return

    lookback = max(120, int(cfg.get("atr_percentile_lookback") or 500) + 40)
    chosen: dict[str, Any] | None = None
    chosen_symbol = symbols[0]
    for symbol in symbols:
        rows = _bars(symbol, lookback)
        last_open = _last_bar_open_ms(rows)
        now = _now_ms()
        bar_stale = last_open is None or now - (last_open + _INTERVAL_MS) > 2 * _INTERVAL_MS
        quote_stale = False
        try:
            quote_stale = _quote_stale(symbol, stale_ms)
        except Exception:
            quote_stale = False
        if bar_stale or quote_stale:
            halt_reason = "stale_market_data"
            chosen_symbol = symbol
            break
        pack = features.build_indicator_pack(rows, cfg)
        if pack is None:
            continue
        snap = features.latest_snapshot(pack)
        if snap is None:
            continue
        if risk.near_funding(int(snap["time"]), blackout):
            continue
        rate = _next_funding(symbol)
        if risk.funding_blocks_long(rate, skip_rate):
            continue
        if not features.setup_ready(snap, cfg):
            state.setdefault("setup_bar", {})[symbol] = None
            continue
        setup_idx = state.get("setup_bar", {}).get(symbol)
        if setup_idx is None:
            state.setdefault("setup_bar", {})[symbol] = snap["index"]
            setup_idx = snap["index"]
        if snap["index"] - int(setup_idx) > int(cfg.get("volume_confirm_bars") or 4):
            continue
        if not features.volume_confirms(snap, cfg):
            continue
        chosen = {"symbol": symbol, "snap": snap, "funding": rate}
        chosen_symbol = symbol
        break

    action = "hold"
    meta: dict[str, Any] = {"reason_code": halt_reason or "no_setup"}
    if halt_reason:
        action = "watch"
        meta["reason_code"] = halt_reason
    elif chosen is not None:
        ai = _ai_veto(chosen["symbol"], chosen["snap"])
        meta["ai_layer"] = ai
        if ai == "invalid":
            action = "watch"
            meta["reason_code"] = "ai_invalid_no_trade"
        else:
            action = "long"
            meta["reason_code"] = "ema_adx_long"
            if ai == "unavailable":
                meta["ai_note"] = "AI unavailable; deterministic long kept (AI does not invent direction)"

    def _trade() -> dict[str, Any]:
        if chosen is None:
            return {"status": "no_setup"}
        now = _now_ms()
        cancel_logs = execution.cancel_stale_limits(
            symbol=chosen["symbol"],
            now_ms=now,
            ttl_hours=ttl_hours,
            state=state,
        )
        snap = chosen["snap"]
        stop_dist = float(cfg.get("stop_atr_mult") or 1.5) * float(snap["atr"])
        qty = risk.position_qty(
            risk_usdt=float(cfg.get("risk_usdt") or 15),
            stop_distance=stop_dist,
            lot=0.0001,
        )
        result = execution.place_isolated_long(
            symbol=chosen["symbol"],
            limit_price=float(snap["close"]),
            qty=qty,
            leverage=leverage,
            sl_price=float(snap["close"]) - stop_dist,
            tp_price=float(snap["close"]) + float(cfg.get("first_tp_r") or 1.5) * stop_dist,
            margin_budget=margin_budget,
        )
        opened.add(chosen["symbol"])
        state["opened_symbols"] = sorted(opened)
        _log(
            {
                "timestamp": now,
                "symbol": chosen["symbol"],
                "side": "long",
                "intended_price": snap["close"],
                "filled_price": None,
                "fees": None,
                "funding": chosen.get("funding"),
                "reason_code": "limit_submitted",
                "result": result,
                "cancel_logs": cancel_logs,
            }
        )
        return result

    runtime.emit_signal_or_follow(
        action=action,
        symbol=chosen_symbol,
        confidence=0.7 if action == "long" else 0.0,
        metrics={
            "leverage": leverage,
            "activation_status": "inactive",
            "daily_realized": state.get("daily_realized"),
            "playbook_realized": state.get("playbook_realized"),
        },
        meta=meta,
        reason_code=str(meta.get("reason_code") or "hold"),
        execute_trade=_trade if action == "long" else None,
    )
    _save_state(state)
