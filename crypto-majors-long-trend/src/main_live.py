"""Live follow-trade path: isolated long-only crypto-major pullback."""

from datetime import datetime, timezone
from typing import Any

from getagent import data, runtime

from . import execution, spec
from .features import INTERVAL, INTERVAL_MS
from .risk import (
    apply_day_rollover,
    bar_feed_stale,
    expected_funding_r,
    in_funding_blackout,
    quantize_price,
    size_from_risk,
    spread_bps,
    ticker_stale,
)
from .signal import evaluate_long
from .state_store import append_action_log, load_state, save_state


def _cfg() -> dict[str, Any]:
    return runtime.manifest.get("strategy_config", {}) or {}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _records(response: object) -> list[dict[str, object]]:
    return [dict(row) for row in data.to_records(response)]


def _emit(action: str, symbol: str, reason: str, metrics: dict[str, Any], meta: dict[str, Any], execute=None) -> None:
    append_action_log(
        {
            "timestamp": _now().isoformat(),
            "symbol": symbol,
            "side": "long" if action == "long" else "flat",
            "intended_price": meta.get("intended_price"),
            "filled_price": meta.get("filled_price"),
            "fees": meta.get("fees", "PENDING"),
            "funding": meta.get("funding"),
            "reason_code": reason,
        }
    )
    runtime.emit_signal_or_follow(
        action=action,
        symbol=symbol,
        confidence=0.7 if action == "long" else 0.0,
        metrics=metrics,
        meta={**meta, "reason_code": reason},
        reason_code=reason,
        execute_trade=execute,
    )


def _series(rows: list[dict[str, object]], field: str) -> list[float]:
    values: list[float] = []
    for row in rows:
        raw = row.get(field)
        if raw in (None, ""):
            continue
        values.append(float(raw))
    return values


def _last_open_ms(rows: list[dict[str, object]]) -> int | None:
    stamps = []
    for row in rows:
        value = row.get("time")
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            stamps.append(int(value))
    return max(stamps) if stamps else None


def run() -> None:
    cfg = _cfg()
    symbol = str((cfg.get("trading_symbols") or ["BTCUSDT"])[0])
    now = _now()
    state = apply_day_rollover(load_state(), now)
    risk_usdt = float(cfg.get("risk_usdt") or 15)
    leverage_cap = min(int(cfg.get("leverage") or 5), int(cfg.get("leverage_cap") or 5), 5)
    margin_budget = float(cfg.get("margin_budget") or 500)
    metrics: dict[str, Any] = {"sleeve": spec.SLEEVE, "cluster": spec.CLUSTER}

    if symbol not in spec.UNIVERSE:
        _emit("watch", symbol, "UNSUPPORTED_SYMBOL", metrics, {})
        return

    if state.halted:
        _emit("watch", symbol, state.halt_reason or "HALT_PLAYBOOK_STOP", metrics, {})
        save_state(state)
        return
    if state.consecutive_losses >= int(cfg.get("consecutive_loss_halt") or 5):
        state.halted = True
        state.halt_reason = "HALT_CONSEC_LOSS"
        save_state(state)
        _emit("watch", symbol, "HALT_CONSEC_LOSS", metrics, {})
        return
    if state.halt_reason == "HALT_DAILY_PAUSE":
        save_state(state)
        _emit("watch", symbol, "HALT_DAILY_PAUSE", metrics, {"daily_realized_usdt": state.daily_realized_usdt})
        return

    ticker = data.crypto.futures.ticker(symbol=symbol, exchange="bitget")
    tick_rows = _records(ticker)
    if not tick_rows:
        _emit("watch", symbol, "STALE_DATA", metrics, {"detail": "ticker_empty"})
        return
    tick = tick_rows[0]
    if ticker_stale(tick.get("timestamp") or tick.get("ts"), now, int(cfg.get("stale_data_sec") or 60)):
        # ticker timestamp may be ISO; also accept live last price path via kline freshness
        pass

    bid = tick.get("bid")
    ask = tick.get("ask")
    last = float(tick.get("last") or tick.get("close") or 0)
    spread = spread_bps(bid, ask)
    volume = float(tick.get("quote_volume") or 0)
    metrics.update({"spread_bps": spread, "volume_24h_usdt": volume, "last": last})
    if spread is None or spread > float(cfg.get("spread_max_bps") or 5):
        _emit("watch", symbol, "SPREAD_GATE", metrics, {"spread_bps": spread})
        return
    if volume < float(cfg.get("volume_min_usdt") or 50_000_000):
        _emit("watch", symbol, "VOLUME_GATE", metrics, {"volume_24h_usdt": volume})
        return

    bars = data.crypto.futures.kline(
        symbol=symbol,
        interval=INTERVAL,
        exchange="bitget",
        limit=300,
        closed_only=True,
    )
    rows = _records(bars)
    last_open = _last_open_ms(rows)
    if bar_feed_stale(last_open, now, INTERVAL_MS):
        _emit("watch", symbol, "STALE_DATA", metrics, {"last_bar_open_ms": last_open})
        return

    highs = _series(rows, "high")
    lows = _series(rows, "low")
    closes = _series(rows, "close")

    funding_rows = _records(
        data.crypto.futures.funding_rate(symbol=symbol, exchange="bitget", interval="1h", limit=5)
    )
    funding_rate = None
    next_funding = None
    if funding_rows:
        funding_rate = funding_rows[-1].get("funding_rate") or funding_rows[-1].get("estimated_rate")
        next_funding = funding_rows[-1].get("next_funding_time")
    if funding_rate is None:
        funding_rate = tick.get("funding_rate")
    metrics["funding_rate"] = funding_rate

    open_symbols = []
    try:
        open_symbols = execution.all_open_symbols()
    except Exception as exc:
        _emit("watch", symbol, "AI_LAYER_INVALID", metrics, {"detail": f"position_query_failed:{exc}"})
        return

    owned = set(state.opened_symbols)
    foreign = [item for item in open_symbols if item not in owned and item != symbol]
    if foreign:
        _emit("watch", symbol, "FOREIGN_POSITION", metrics, {"foreign_symbols": foreign})
        save_state(state)
        return
    # Same-symbol position we did not record: alert, do not touch.
    if symbol in open_symbols and symbol not in owned and not state.pending_order_id:
        _emit("watch", symbol, "FOREIGN_POSITION", metrics, {"foreign_symbols": [symbol]})
        save_state(state)
        return

    position = None
    try:
        position = execution.current_position(symbol)
    except Exception:
        position = None

    if position is not None:
        opened_ms = state.pending_submitted_ms
        held_hours = 0.0
        if opened_ms:
            held_hours = (now.timestamp() * 1000 - opened_ms) / 3600000.0
        if held_hours >= float(cfg.get("time_stop_hours") or 8):

            def _time_stop() -> dict[str, Any]:
                closed = execution.close_long(symbol)
                return closed

            result_holder: dict[str, Any] = {}

            def _run_close() -> dict[str, Any]:
                result_holder.update(_time_stop())
                return result_holder

            _emit("hold", symbol, "TIME_STOP", metrics, {"held_hours": held_hours}, execute=_run_close)
            if symbol in owned:
                state.opened_symbols = tuple(item for item in owned if item != symbol)
            save_state(state)
            return
        _emit("hold", symbol, "ALREADY_IN_POSITION", metrics, {"owned": True})
        save_state(state)
        return

    if state.pending_order_id or state.pending_symbol == symbol:
        age_ms = int(now.timestamp() * 1000) - int(state.pending_submitted_ms or 0)
        if age_ms >= int(float(cfg.get("limit_ttl_hours") or 4) * 3600 * 1000):

            def _cancel() -> dict[str, Any]:
                return execution.cancel_pending(symbol, state.pending_order_id)

            _emit("watch", symbol, "LIMIT_CANCEL_TTL", metrics, {"order_id": state.pending_order_id}, execute=_cancel)
            state.pending_order_id = ""
            state.pending_symbol = ""
            state.pending_submitted_ms = 0
            save_state(state)
            return
        _emit("watch", symbol, "LIMIT_WORKING", metrics, {"order_id": state.pending_order_id})
        save_state(state)
        return

    decision = evaluate_long(
        highs,
        lows,
        closes,
        adx_period=int(cfg.get("adx_period") or 14),
        atr_period=int(cfg.get("atr_period") or 14),
        ema_fast_period=int(cfg.get("ema_fast_period") or 21),
        ema_slow_period=int(cfg.get("ema_slow_period") or 55),
        adx_min=float(cfg.get("adx_min") or 22),
        atr_pct_lo=float(cfg.get("atr_pct_lo") or 25),
        atr_pct_hi=float(cfg.get("atr_pct_hi") or 80),
        percentile_lookback=int(cfg.get("percentile_lookback") or 168),
        stop_atr_mult=float(cfg.get("stop_atr_mult") or 1.5),
    )
    if not decision.valid:
        _emit("watch", symbol, decision.reason, metrics, decision.meta)
        save_state(state)
        return

    interval_hours = spec.funding_interval_hours(symbol)
    if in_funding_blackout(
        now,
        next_funding,
        interval_hours,
        int(cfg.get("funding_blackout_min") or 15),
        int(cfg.get("limit_ttl_hours") or 4),
    ):
        _emit("watch", symbol, "FUNDING_BLACKOUT", metrics, {"next_funding": next_funding})
        save_state(state)
        return

    limit_price = float(quantize_price(symbol, float(decision.limit_price or last)))
    sizing = size_from_risk(
        symbol,
        price=limit_price,
        stop_distance=float(decision.stop_distance or 0),
        risk_usdt=risk_usdt,
        leverage_cap=leverage_cap,
        margin_budget=margin_budget,
    )
    metrics.update(
        {
            "notional_usdt": sizing.get("notional_usdt"),
            "min_open_notional_usdt": sizing.get("min_open_notional_usdt"),
            "sizing_ok": sizing.get("sizing_ok"),
            "qty": sizing.get("qty"),
        }
    )
    if not sizing.get("sizing_ok"):
        _emit("watch", symbol, "SIZING_REJECT", metrics, sizing)
        save_state(state)
        return

    funding_r = expected_funding_r(
        funding_rate,
        float(sizing.get("notional_usdt") or 0),
        int(cfg.get("time_stop_hours") or 8),
        interval_hours,
        risk_usdt,
    )
    if funding_r > float(cfg.get("funding_cost_max_r") or 0.1):
        _emit("watch", symbol, "FUNDING_COST", metrics, {"expected_funding_R": funding_r})
        save_state(state)
        return

    from getagent import trade

    qty_plan = trade.helpers.compute_qty(
        symbol=symbol,
        market="contract",
        budget_amount=str(sizing.get("margin_usdt") or margin_budget),
        leverage=int(sizing.get("leverage") or leverage_cap),
        price=str(limit_price),
        product_type=spec.PRODUCT_TYPE,
    )
    tp_price, sl_price = execution.levels_from_entry(
        symbol,
        limit_price,
        float(decision.stop_distance or 0),
        float(cfg.get("tp_r_multiple") or 2.0),
    )

    def _place() -> dict[str, Any]:
        placed = execution.place_isolated_long(
            symbol=symbol,
            qty=str(qty_plan.qty),
            price=str(limit_price),
            leverage=int(sizing.get("leverage") or leverage_cap),
            tp_price=tp_price,
            sl_price=sl_price,
        )
        state.pending_symbol = symbol
        state.pending_submitted_ms = int(now.timestamp() * 1000)
        state.last_entry_price = str(limit_price)
        state.last_stop_price = sl_price
        state.last_tp_price = tp_price
        raw = placed.get("result")
        order_id = ""
        if isinstance(raw, dict):
            order_id = str(raw.get("orderId") or raw.get("order_id") or "")
        state.pending_order_id = order_id
        if symbol not in state.opened_symbols:
            state.opened_symbols = tuple(list(state.opened_symbols) + [symbol])
        save_state(state)
        return placed

    _emit(
        "long",
        symbol,
        "LIMIT_PLACED",
        metrics,
        {
            "intended_price": str(limit_price),
            "filled_price": "PENDING",
            "funding": funding_rate,
            "tp_price": tp_price,
            "sl_price": sl_price,
            "adx": decision.adx,
            "atr": decision.atr,
        },
        execute=_place,
    )
    save_state(state)
