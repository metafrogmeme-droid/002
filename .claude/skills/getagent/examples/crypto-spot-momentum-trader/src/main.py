"""Crypto spot momentum Playbook with historical and live paths."""
import math
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation

from getagent import backtest, data, runtime

_INTERVAL = "4h"
_INTERVAL_MS = 4 * 60 * 60 * 1000
# Refuse live decisions when the newest closed bar lags now by more than
# this many intervals — a stalled feed must not silently drive trades.
_MAX_STALE_INTERVALS = 2


def _decimal(value: object, default: str = "0") -> Decimal:
    try:
        return Decimal(str(value if value not in (None, "") else default))
    except (InvalidOperation, ValueError):
        return Decimal(default)


def _records(response: object) -> list[dict[str, object]]:
    return [dict(row) for row in data.to_records(response)]


def _sanitize(value: object) -> object:
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def _closes(rows: list[dict[str, object]]) -> list[Decimal]:
    values: list[Decimal] = []
    for row in rows:
        close = _decimal(row.get("close"), default="")
        if close > 0:
            values.append(close)
    return values


def _last_bar_open_ms(rows: list[dict[str, object]]) -> int | None:
    """Open time (ms epoch UTC) of the newest bar; `time` is the canonical column."""
    stamps = [
        int(value)
        for row in rows
        for value in (row.get("time"),)
        if isinstance(value, (int, float)) and not isinstance(value, bool)
    ]
    return max(stamps) if stamps else None


def _is_stale(last_bar_open_ms: int | None) -> bool:
    if last_bar_open_ms is None:
        return True
    now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
    last_close_ms = last_bar_open_ms + _INTERVAL_MS
    return now_ms - last_close_ms > _MAX_STALE_INTERVALS * _INTERVAL_MS


def _score_symbol(symbol: str, closes: list[Decimal]) -> dict[str, object] | None:
    if len(closes) < 3:
        return None
    first = closes[0]
    last = closes[-1]
    peak = max(closes)
    if first <= 0 or peak <= 0:
        return None
    momentum_pct = (last - first) / first * Decimal("100")
    drawdown_pct = (peak - last) / peak * Decimal("100")
    score = momentum_pct - drawdown_pct / Decimal("2")
    return {
        "symbol": symbol,
        "last_price": str(last),
        "momentum_pct": str(momentum_pct.quantize(Decimal("0.01"))),
        "drawdown_pct": str(drawdown_pct.quantize(Decimal("0.01"))),
        "score": score,
    }


def _choose_candidate(symbols: list[str], lookback_candles: int) -> dict[str, object] | None:
    candidates: list[dict[str, object]] = []
    for symbol in symbols:
        # closed_only=True (the default, spelled out here) keeps the
        # currently-forming candle out of the series: live decisions must
        # only ever see closed bars, or the signal repaints intra-bar.
        bars = data.crypto.spot.kline(
            symbol=symbol,
            interval=_INTERVAL,
            exchange="bitget",
            limit=lookback_candles,
            closed_only=True,
        )
        rows = _records(bars)
        candidate = _score_symbol(symbol, _closes(rows))
        if candidate is not None:
            candidate["last_bar_ts"] = _last_bar_open_ms(rows)
            candidates.append(candidate)
    if not candidates:
        return None
    return max(candidates, key=lambda item: item["score"])


def _execute_spot_buy(symbol: str, budget_usdt: str) -> dict[str, object]:
    from getagent import trade

    qty_plan = trade.helpers.compute_qty(
        symbol=symbol,
        market="spot",
        budget_amount=budget_usdt,
    )
    result = trade.spot.market_buy(symbol=symbol, qty=qty_plan.qty)
    if not trade.is_success(result):
        raise RuntimeError(f"spot market buy failed: {result}")
    return {"qty": str(qty_plan.qty), "result": result}


def _historical_frame(symbol: str) -> object:
    # closed_only also matters for replay: a trailing half-formed bar would
    # make the same backtest return different numbers on every run.
    bars = data.crypto.spot.kline(
        symbol=symbol,
        interval=_INTERVAL,
        exchange="bitget",
        days=90,
        limit=1000,
        closed_only=True,
    )
    return backtest.prepare_frame(bars, datetime_index="date")


def _backtest_metrics(result: object, rows: int) -> dict[str, object]:
    return {
        "total_return_pct": _sanitize(getattr(result, "total_return_pct", None)),
        "sharpe_ratio": _sanitize(getattr(result, "sharpe_ratio", None)),
        "max_drawdown_pct": _sanitize(getattr(result, "max_drawdown_pct", None)),
        "win_rate": _sanitize(getattr(result, "win_rate", None)),
        "total_trades": getattr(result, "total_trades", 0),
        "profit_factor": _sanitize(getattr(result, "profit_factor", None)),
        "rows": rows,
    }


def _emit_backtest_signal(symbol: str, result: object, rows: int) -> None:
    chart_path = backtest.generate_chart(result)
    total_trades = int(getattr(result, "total_trades", 0) or 0)
    runtime.emit_signal(
        action="long" if total_trades > 0 else "watch",
        symbol=symbol,
        confidence=_sanitize(getattr(result, "win_rate", 0.0)) or 0.0,
        metrics=_backtest_metrics(result, rows),
        meta={"chart_path": chart_path},
    )


def _run_historical() -> None:
    cfg = runtime.manifest.get("strategy_config", {}) or {}
    symbol = str((cfg.get("trading_symbols") or ["BGBUSDT"])[0])
    replay_frame = _historical_frame(symbol)
    if replay_frame.empty:
        runtime.emit_signal(action="watch", symbol=symbol, confidence=0.0, metrics={"rows": 0})
        return
    result = backtest.run(ohlcv_data={f"{symbol}.BITGET": replay_frame}, spec=runtime.backtest_spec)
    _emit_backtest_signal(symbol, result, len(replay_frame))


def _live_config() -> tuple[list[str], int, str, Decimal, Decimal, bool]:
    from getagent import trade

    cfg = runtime.manifest.get("strategy_config", {}) or {}
    symbols = list(cfg.get("trading_symbols") or runtime.manifest.get("trading_symbols") or [])
    symbols = trade.helpers.normalize_trading_symbols(symbols or ["BGBUSDT"])
    return (
        symbols,
        int(cfg.get("lookback_candles", 36) or 36),
        str(cfg.get("budget_usdt", "25") or "25"),
        _decimal(cfg.get("min_momentum_pct"), default="1.0"),
        _decimal(cfg.get("max_drawdown_pct"), default="8.0"),
        bool(cfg.get("force_live_long_for_testing", False)),
    )


def _run_live() -> None:
    symbols, lookback_candles, budget_usdt, min_momentum, max_drawdown, force_long = _live_config()

    decision = _choose_candidate(symbols, max(12, min(lookback_candles, 90)))
    if decision is None:
        decision = {
            "symbol": symbols[0],
            "last_price": "",
            "momentum_pct": "0",
            "drawdown_pct": "0",
            "score": Decimal("0"),
            "last_bar_ts": None,
        }

    last_bar_ts = decision.get("last_bar_ts")
    stale = _is_stale(last_bar_ts if isinstance(last_bar_ts, int) else None)

    momentum = _decimal(decision["momentum_pct"])
    drawdown = _decimal(decision["drawdown_pct"])
    action = "long" if force_long or (momentum >= min_momentum and drawdown <= max_drawdown) else "hold"
    if stale:
        # Newest closed bar is too old — refuse to make a trading decision
        # on stale data, regardless of what the score says.
        action = "hold"
    confidence = 0.0 if stale else 0.95 if force_long else 0.72 if action == "long" else 0.35

    meta: dict[str, object] = {"decision": {k: v for k, v in decision.items() if k != "score"}}
    if stale:
        meta["reason"] = "stale market data: newest closed bar exceeds freshness window"

    runtime.emit_signal_or_follow(
        action=action,
        symbol=str(decision["symbol"]),
        confidence=confidence,
        metrics={
            "momentum_pct": float(momentum),
            "drawdown_pct": float(drawdown),
            "budget_usdt": float(_decimal(budget_usdt, default="0")),
            "force_live_long_for_testing": force_long,
            "last_bar_ts": last_bar_ts if isinstance(last_bar_ts, int) else None,
            "data_stale": stale,
        },
        meta=meta,
        execute_trade=lambda: _execute_spot_buy(str(decision["symbol"]), budget_usdt),
    )


def run() -> None:
    if runtime.is_historical():
        _run_historical()
        return
    if runtime.is_live():
        _run_live()
        return
    raise ValueError(f"unsupported evaluation_mode={runtime.evaluation_mode!r}")


if __name__ == "__main__":
    run()
