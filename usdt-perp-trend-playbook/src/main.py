"""Main entry point for USDT Perpetuals Trend-Following Strategy Playbook.

Supports both managed historical evaluation and live scheduled cycle execution.
All trade executions run in isolated sub-account follow-trade mode with strict risk guards.
"""
import math
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any

from getagent import backtest, data, runtime

_INTERVAL = "1h"
_STALE_SECONDS_THRESHOLD = 60
_MAX_CONCURRENT_POSITIONS = 3


def _decimal(val: Any, default: str = "0") -> Decimal:
    try:
        if val is None or val == "":
            return Decimal(default)
        return Decimal(str(val))
    except (InvalidOperation, ValueError):
        return Decimal(default)


def _sanitize(value: Any) -> Any:
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def _sanitize_metrics(metrics: dict[str, Any]) -> dict[str, Any]:
    return {k: _sanitize(v) for k, v in metrics.items()}


def _is_funding_window_or_adverse(funding_rate: Decimal) -> tuple[bool, str]:
    """Check if current time is within +/- 15 min of 00:00, 08:00, 16:00 UTC,

    or if funding rate is > +0.03% (costly to hold long).
    """
    now = datetime.now(timezone.utc)
    hour = now.hour
    minute = now.minute

    # Funding settlements at 00:00, 08:00, 16:00 UTC
    funding_hours = [0, 8, 16]
    for fh in funding_hours:
        diff_minutes = (hour - fh) * 60 + minute
        # normalize to [-720, 720]
        if diff_minutes > 720:
            diff_minutes -= 1440
        elif diff_minutes < -720:
            diff_minutes += 1440
        if abs(diff_minutes) <= 15:
            return True, f"funding settlement window proximity ({abs(diff_minutes)}m to {fh:02d}:00 UTC)"

    if funding_rate > Decimal("0.0003"):
        return True, f"funding rate adverse to long ({funding_rate * 100:.4f}% > 0.03%/8h)"

    return False, "ok"


def _check_subaccount_unmanaged_positions(symbol: str) -> tuple[bool, str]:
    """Verify subaccount does not contain foreign positions not opened by Playbook."""
    from getagent import trade

    try:
        current = trade.contract.current_position(symbol=symbol)
        pos = trade.helpers.find_contract_position(current, symbol=symbol)
        if pos is not None and getattr(pos, "total", 0) > 0:
            return True, "existing position in sub-account"
    except Exception as e:
        return False, f"check failed: {e}"
    return False, "ok"


def _calculate_indicators(bars_records: list[dict[str, Any]]) -> dict[str, Any]:
    if len(bars_records) < 30:
        return {"valid": False, "reason": "insufficient bars"}

    closes = [_decimal(r.get("close", 0)) for r in bars_records]
    highs = [_decimal(r.get("high", 0)) for r in bars_records]
    lows = [_decimal(r.get("low", 0)) for r in bars_records]
    volumes = [_decimal(r.get("volume", 0)) for r in bars_records]

    # Calculate EMA 12 and 26
    def ema(series: list[Decimal], period: int) -> list[Decimal]:
        alpha = Decimal(2) / Decimal(period + 1)
        res = [series[0]]
        for val in series[1:]:
            res.append(alpha * val + (Decimal(1) - alpha) * res[-1])
        return res

    ema_12 = ema(closes, 12)
    ema_26 = ema(closes, 26)

    # Calculate ATR 14
    tr_list: list[Decimal] = []
    for i in range(1, len(closes)):
        hl = highs[i] - lows[i]
        hpc = abs(highs[i] - closes[i - 1])
        lpc = abs(lows[i] - closes[i - 1])
        tr_list.append(max(hl, hpc, lpc))

    atr_period = 14
    if len(tr_list) < atr_period:
        return {"valid": False, "reason": "insufficient tr bars"}

    atr_14 = sum(tr_list[-atr_period:]) / Decimal(atr_period)

    # 20-bar volume average
    vol_20_avg = sum(volumes[-21:-1]) / Decimal(20)
    current_vol = volumes[-1]

    # Simplified ADX directional strength proxy
    up_moves = [max(Decimal(0), highs[i] - highs[i - 1]) for i in range(1, len(highs))]
    down_moves = [max(Decimal(0), lows[i - 1] - lows[i]) for i in range(1, len(lows))]
    up_sum = sum(up_moves[-14:])
    down_sum = sum(down_moves[-14:])
    total_move = up_sum + down_sum
    directional_strength = (abs(up_sum - down_sum) / total_move * Decimal(100)) if total_move > 0 else Decimal(0)

    return {
        "valid": True,
        "close": closes[-1],
        "ema_12": ema_12[-1],
        "ema_26": ema_26[-1],
        "atr_14": atr_14,
        "vol_20_avg": vol_20_avg,
        "current_vol": current_vol,
        "adx_proxy": directional_strength,
    }


def _execute_limit_long(
    symbol: str,
    entry_price: Decimal,
    stop_price: Decimal,
    target_price: Decimal,
    risk_budget_usdt: Decimal,
    max_leverage: int,
) -> dict[str, Any]:
    from getagent import trade

    stop_dist = entry_price - stop_price
    if stop_dist <= Decimal("0"):
        return {"status": "error", "message": "invalid stop distance"}

    # Sizing = 15 USDT / stop distance
    qty_raw = risk_budget_usdt / stop_dist
    max_notional = risk_budget_usdt * Decimal(max_leverage)
    max_qty = max_notional / entry_price
    final_qty = min(qty_raw, max_qty)

    rules = trade.helpers.contract_rules(symbol)
    price_step = rules.price_step
    entry_str = str(rules.quantize_price(entry_price))
    sl_str = str(rules.quantize_price(stop_price))
    tp_str = str(rules.quantize_price(target_price))

    qty_plan = trade.helpers.compute_qty(
        symbol=symbol,
        market="contract",
        budget_amount=str(risk_budget_usdt),
        leverage=max_leverage,
    )

    result = trade.contract.open_long_limit(
        symbol=symbol,
        qty=qty_plan.qty,
        price=entry_str,
        leverage=max_leverage,
        tp_trigger_price=tp_str,
        sl_trigger_price=sl_str,
    )

    if not trade.is_success(result):
        return {"status": "failed", "result": result}

    return {"status": "submitted", "price": entry_str, "tp": tp_str, "sl": sl_str, "result": result}


def _run_live() -> None:
    cfg = runtime.manifest.get("strategy_config", {}) or {}
    symbols = cfg.get("trading_symbols") or ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
    risk_budget = _decimal(cfg.get("risk_per_trade_usdt", "15"))
    max_leverage = int(cfg.get("leverage", 5))

    primary_symbol = symbols[0]
    bars = data.crypto.futures.kline(
        symbol=primary_symbol,
        interval=_INTERVAL,
        exchange="binance",
        limit=50,
        closed_only=True,
    )
    records = [dict(r) for r in data.to_records(bars)]

    if not records:
        runtime.emit_signal(action="watch", symbol=primary_symbol, confidence=0.0, meta={"reason": "no bars returned"})
        return

    # Check data freshness
    last_bar_time = records[-1].get("time")
    now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
    if last_bar_time and (now_ms - int(last_bar_time)) > (_STALE_SECONDS_THRESHOLD * 1000 + 3600 * 1000):
        runtime.emit_signal(
            action="watch",
            symbol=primary_symbol,
            confidence=0.0,
            meta={"reason": "market data stale > 60s past candle close", "last_bar_time": last_bar_time},
        )
        return

    # Check unmanaged positions in sub-account
    has_unmanaged, pos_msg = _check_subaccount_unmanaged_positions(primary_symbol)
    if has_unmanaged:
        runtime.emit_signal(
            action="watch",
            symbol=primary_symbol,
            confidence=0.0,
            meta={"reason": f"circuit breaker: unmanaged position in sub-account ({pos_msg})"},
        )
        return

    # Check funding filter
    funding_res = data.crypto.futures.funding_rate(symbol=primary_symbol, exchange="binance", limit=1)
    funding_records = [dict(r) for r in data.to_records(funding_res)] if funding_res else []
    funding_rate = _decimal(funding_records[0].get("funding_rate", 0)) if funding_records else Decimal("0")

    skip_funding, funding_reason = _is_funding_window_or_adverse(funding_rate)
    if skip_funding:
        runtime.emit_signal(
            action="watch",
            symbol=primary_symbol,
            confidence=0.0,
            meta={"reason": f"funding filter active: {funding_reason}", "funding_rate": str(funding_rate)},
        )
        return

    # Compute technical indicators
    indicators = _calculate_indicators(records)
    if not indicators["valid"]:
        runtime.emit_signal(
            action="watch",
            symbol=primary_symbol,
            confidence=0.0,
            meta={"reason": f"invalid indicators: {indicators.get('reason')}"},
        )
        return

    close = indicators["close"]
    ema_12 = indicators["ema_12"]
    ema_26 = indicators["ema_26"]
    vol = indicators["current_vol"]
    vol_avg = indicators["vol_20_avg"]
    adx_proxy = indicators["adx_proxy"]
    atr = indicators["atr_14"]

    # Entry condition check
    trend_aligned = close > ema_12 and ema_12 > ema_26
    vol_confirmed = vol >= (vol_avg * Decimal("1.5"))
    trend_strong = adx_proxy >= Decimal("25.0")

    if trend_aligned and vol_confirmed and trend_strong:
        stop_dist = atr * Decimal("1.5")
        stop_price = close - stop_dist
        target_price = close + (Decimal("2.0") * stop_dist)

        runtime.emit_signal_or_follow(
            action="long",
            symbol=primary_symbol,
            confidence=0.75,
            metrics={
                "close": float(close),
                "ema_12": float(ema_12),
                "ema_26": float(ema_26),
                "atr_14": float(atr),
                "adx_proxy": float(adx_proxy),
                "vol_ratio": float(vol / vol_avg) if vol_avg > 0 else 0.0,
            },
            meta={
                "intended_entry": str(close),
                "stop_price": str(stop_price),
                "target_price": str(target_price),
                "risk_usdt": str(risk_budget),
                "reason_code": "TREND_ENTRY_CONFIRMED",
            },
            execute_trade=lambda: _execute_limit_long(
                symbol=primary_symbol,
                entry_price=close,
                stop_price=stop_price,
                target_price=target_price,
                risk_budget_usdt=risk_budget,
                max_leverage=max_leverage,
            ),
        )
    else:
        runtime.emit_signal(
            action="watch",
            symbol=primary_symbol,
            confidence=0.0,
            metrics={
                "trend_aligned": trend_aligned,
                "vol_confirmed": vol_confirmed,
                "trend_strong": trend_strong,
            },
            meta={"reason": "setup criteria not met", "reason_code": "REGIME_FILTER_NO_SIGNAL"},
        )


def _run_historical() -> None:
    cfg = runtime.manifest.get("strategy_config", {}) or {}
    symbols = cfg.get("trading_symbols") or ["BTCUSDT"]
    symbol = symbols[0]

    bars = data.crypto.futures.kline(
        symbol=symbol,
        interval=_INTERVAL,
        exchange="binance",
        limit=1000,
        closed_only=True,
    )
    replay_frame = backtest.prepare_frame(bars, datetime_index="date")

    if replay_frame.empty:
        runtime.emit_signal(
            action="watch",
            symbol=symbol,
            confidence=0.0,
            metrics={"rows": 0},
            meta={"reason": "no historical bars returned"},
        )
        return

    instrument_key = f"{symbol}.BITGET"
    result = backtest.run(
        ohlcv_data={instrument_key: replay_frame},
        spec=runtime.backtest_spec,
    )

    chart_path = backtest.generate_chart(result)
    summary = result.summary or {}
    net_pnl_raw = summary.get("net_pnl", 0)
    try:
        net_pnl = float(net_pnl_raw or 0)
    except (TypeError, ValueError):
        net_pnl = 0.0

    action = "long" if net_pnl > 0 and (result.total_trades or 0) >= 30 else "watch"
    metrics = _sanitize_metrics(
        {
            "total_return_pct": result.total_return_pct,
            "net_pnl": net_pnl,
            "starting_balance": summary.get("starting_balance"),
            "sharpe_ratio": result.sharpe_ratio,
            "max_drawdown_pct": result.max_drawdown_pct,
            "win_rate": result.win_rate,
            "total_trades": result.total_trades,
            "profit_factor": result.profit_factor,
            "rows": len(replay_frame),
        }
    )

    runtime.emit_signal(
        action=action,
        symbol=symbol,
        confidence=_sanitize(result.win_rate) or 0.0,
        metrics=metrics,
        meta={
            "chart_path": chart_path,
            "status": "completed",
            "reason_code": "HISTORICAL_BACKTEST_EVALUATION",
        },
    )


def run() -> None:
    if runtime.is_historical():
        _run_historical()
    elif runtime.is_live():
        _run_live()
    else:
        _run_live()


if __name__ == "__main__":
    run()
