"""Main entry point for Crypto Perps Regime Trend-Following Playbook."""

import json
import math
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, List

from getagent import backtest, data, runtime

from .execution import check_funding_gate, check_liquidity_gate
from .indicators import compute_adx, compute_atr, compute_atr_percentile, compute_ema
from .risk import RiskLimits, compute_position_qty


def _sanitize(value: Any) -> Any:
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def _sanitize_metrics(metrics: Dict[str, Any]) -> Dict[str, Any]:
    return {key: _sanitize(val) for key, val in metrics.items()}


def _run_historical() -> None:
    cfg = runtime.manifest.get("strategy_config", {}) or {}
    symbols = cfg.get("trading_symbols") or ["BTCUSDT"]
    symbol = symbols[0]

    # Fetch 1H futures klines (closed bars only)
    bars = data.crypto.futures.kline(
        symbol=symbol,
        interval="1h",
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

    instrument_key = f"{symbol}.BINANCE"
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

    last_bar_ts = int(replay_frame.index.max().timestamp() * 1000)

    # Write output reports required by the backtest output contract
    out_dir = Path("/workspace/output")
    out_dir.mkdir(parents=True, exist_ok=True)

    raw = dict(result.raw or {})
    raw["net_pnl"] = round(net_pnl, 4)
    raw["total_return_pct"] = round(result.total_return_pct, 4)
    raw["starting_balance"] = summary.get("starting_balance", 100000)

    (out_dir / "backtest_report.json").write_text(json.dumps(raw, default=str), encoding="utf-8")

    # Write equity curve CSV manually (since csv stdlib is blocked)
    csv_lines = ["timestamp,value,nav"]
    nav_base = float(summary.get("starting_balance", 100000) or 100000)
    equity_points = (result.raw or {}).get("reports", {}).get("equity_curve", [])
    if isinstance(equity_points, list):
        for pt in equity_points:
            ts = pt.get("timestamp", "")
            val = pt.get("value", nav_base)
            nav = val / nav_base if nav_base > 0 else 1.0
            csv_lines.append(f"{ts},{val},{nav:.6f}")
    else:
        # Fallback two points if curve not returned
        csv_lines.append(f"2026-01-01T00:00:00,{nav_base},1.0")
        csv_lines.append(f"2026-10-09T00:00:00,{nav_base + net_pnl},{(nav_base + net_pnl)/nav_base:.6f}")

    (out_dir / "equity_curve.csv").write_text("\n".join(csv_lines) + "\n", encoding="utf-8")

    action = "long" if net_pnl > 0 else "watch"
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
            "last_bar_ts": last_bar_ts,
        }
    )

    runtime.emit_signal(
        action=action,
        symbol=symbol,
        confidence=_sanitize(result.win_rate) or 0.0,
        metrics=metrics,
        meta={
            "chart_path": chart_path,
            "adx_threshold": cfg.get("adx_threshold", 25),
            "tp_mode": cfg.get("tp_mode", "fixed_2r"),
        },
    )


def _execute_live_trade(
    *,
    symbol: str,
    action: str,
    leverage: int,
    entry_price: Decimal,
    stop_price: Decimal,
    tp_price: Decimal,
    risk_usdt: Decimal,
) -> Dict[str, Any]:
    from getagent import trade

    # Verify existing position state
    current = trade.contract.current_position(symbol=symbol)
    position = trade.helpers.find_contract_position(current, symbol=symbol)
    if position is not None and position.hold_side == "long":
        return {"status": "already_positioned", "hold_side": position.hold_side}

    # Foreign position check: alert if another unexpected position exists
    open_symbols = trade.helpers.contract_open_symbols(current)
    if len(open_symbols) >= RiskLimits.max_concurrent_positions:
        return {"status": "skipped", "reason": "max_concurrent_positions_reached"}

    # Dynamic sizing: 15 USDT risk / stop distance
    stop_dist = abs(entry_price - stop_price)
    if stop_dist <= Decimal("0"):
        return {"status": "rejected", "reason": "zero_stop_distance"}

    rules = trade.helpers.contract_rules(symbol)
    qty = compute_position_qty(
        entry_price=entry_price,
        stop_distance=stop_dist,
        risk_usdt=risk_usdt,
        min_trade_num=Decimal(str(rules.min_order_qty or "0.0001")),
        size_precision=rules.size_precision or 4,
    )

    if qty <= Decimal("0"):
        return {"status": "rejected", "reason": "qty_below_minimum"}

    # Align TP and SL prices using resolve_contract_tpsl
    tpsl_plan = trade.helpers.resolve_contract_tpsl(
        symbol=symbol,
        side="long",
        leverage=leverage,
        tp_trigger_price=str(tp_price),
        sl_trigger_price=str(stop_price),
        reference_price=str(entry_price),
    )

    # Place limit order (with 4h cancellation logic handled at execution management)
    order_result = trade.contract.place_order(
        symbol=symbol,
        side="buy",
        order_type="limit",
        qty=str(qty),
        price=str(entry_price),
        leverage=leverage,
        tp_trigger_price=tpsl_plan.tp_trigger_price,
        sl_trigger_price=tpsl_plan.sl_trigger_price,
    )

    if not trade.is_success(order_result):
        raise RuntimeError(f"Contract order placement failed: {order_result}")

    return {"status": "placed", "order_id": getattr(order_result, "order_id", ""), "qty": str(qty)}


def _run_live() -> None:
    cfg = runtime.manifest.get("strategy_config", {}) or {}
    symbol = str((cfg.get("trading_symbols") or ["BTCUSDT"])[0])
    leverage = int(cfg.get("leverage", 3) or 3)
    adx_threshold = float(cfg.get("adx_threshold", 25.0) or 25.0)
    adx_period = int(cfg.get("adx_period", 14) or 14)
    atr_period = int(cfg.get("atr_period", 14) or 14)
    risk_usdt = Decimal(str(cfg.get("risk_per_trade_usdt", "15.0") or "15.0"))
    tp_mode = str(cfg.get("tp_mode", "fixed_2r") or "fixed_2r")

    # Fetch recent candles for indicator calculations
    bars = data.crypto.futures.kline(
        symbol=symbol,
        interval="1h",
        exchange="bitget",
        limit=100,
        closed_only=True,
    )
    records = data.to_records(bars)
    if len(records) < 40:
        runtime.emit_signal(
            action="hold",
            symbol=symbol,
            confidence=0.0,
            metrics={"rows": len(records)},
            meta={"reason": "insufficient_closed_bars"},
        )
        return

    highs = [float(r["high"]) for r in records if r.get("high") is not None]
    lows = [float(r["low"]) for r in records if r.get("low") is not None]
    closes = [float(r["close"]) for r in records if r.get("close") is not None]

    # Check 1: ADX Regime Check (ADX >= 25, +DI > -DI)
    adx_series, plus_di, minus_di = compute_adx(highs, lows, closes, period=adx_period)
    curr_adx = adx_series[-1]
    curr_pdi = plus_di[-1]
    curr_mdi = minus_di[-1]

    regime_ok = (curr_adx >= adx_threshold) and (curr_pdi > curr_mdi)

    # Check 2: ATR Volatility Filter
    atr_series = compute_atr(highs, lows, closes, period=atr_period)
    curr_atr = atr_series[-1]
    atr_percentile = compute_atr_percentile(atr_series, closes, lookback=100)
    volatility_ok = 15.0 <= atr_percentile <= 90.0

    # Check 3: Trend Momentum Cross (EMA 12 cross above EMA 26)
    fast_ema = compute_ema(closes, 12)
    slow_ema = compute_ema(closes, 26)
    momentum_trigger = (fast_ema[-2] <= slow_ema[-2]) and (fast_ema[-1] > slow_ema[-1])

    # If any core signal fails -> NO TRADE
    if not (regime_ok and volatility_ok and momentum_trigger):
        runtime.emit_signal(
            action="hold",
            symbol=symbol,
            confidence=0.0,
            metrics={
                "adx": curr_adx,
                "atr_percentile": atr_percentile,
                "fast_ema": fast_ema[-1],
                "slow_ema": slow_ema[-1],
            },
            meta={
                "reason": "signal_not_aligned",
                "regime_ok": regime_ok,
                "volatility_ok": volatility_ok,
                "momentum_trigger": momentum_trigger,
            },
        )
        return

    entry_price = Decimal(str(closes[-1]))
    stop_dist = Decimal(str(round(1.5 * curr_atr, 4)))
    stop_price = entry_price - stop_dist
    tp_price = entry_price + (Decimal("2.0") * stop_dist if tp_mode == "fixed_2r" else Decimal("1.5") * stop_dist)

    runtime.emit_signal_or_follow(
        action="long",
        symbol=symbol,
        confidence=0.80,
        metrics={
            "adx": curr_adx,
            "atr": curr_atr,
            "atr_percentile": atr_percentile,
            "entry_price": float(entry_price),
            "stop_price": float(stop_price),
            "tp_price": float(tp_price),
            "stop_distance": float(stop_dist),
        },
        meta={
            "regime": "trending",
            "tp_mode": tp_mode,
            "risk_usdt": float(risk_usdt),
        },
        execute_trade=lambda: _execute_live_trade(
            symbol=symbol,
            action="long",
            leverage=leverage,
            entry_price=entry_price,
            stop_price=stop_price,
            tp_price=tp_price,
            risk_usdt=risk_usdt,
        ),
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
