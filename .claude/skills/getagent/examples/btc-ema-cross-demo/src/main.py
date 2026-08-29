"""Entry point for the BTC EMA Crossover Demo Playbook.

For backtest_support: full playbooks, the platform injects the evaluation mode.
Historical runs use the managed replay engine; live runs emit the same EMA
decision before the managed runtime permits any follow-trade callback.
"""
import math
from decimal import Decimal
from typing import Any

from getagent import backtest, data, runtime


def _sanitize(value: Any) -> Any:
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def _sanitize_metrics(metrics: dict[str, Any]) -> dict[str, Any]:
    return {key: _sanitize(val) for key, val in metrics.items()}


def _run_historical() -> None:
    cfg = runtime.manifest.get("strategy_config", {}) or {}
    symbols = cfg.get("trading_symbols") or ["BTCUSDT"]
    symbol = symbols[0]

    # closed_only=True (the default, spelled out here) keeps the
    # currently-forming candle out of the replay frame; a half-formed tail
    # bar would make the same backtest return different numbers on every run.
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

    # Open time (ms epoch UTC) of the newest closed bar that fed this run,
    # so downstream consumers can audit which data the signal was based on.
    last_bar_ts = int(replay_frame.index.max().timestamp() * 1000)

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
            "fast_period": cfg.get("fast_period"),
            "slow_period": cfg.get("slow_period"),
        },
    )


def _ema(values: list[Decimal], period: int) -> Decimal:
    alpha = Decimal(2) / Decimal(period + 1)
    value = values[0]
    for item in values[1:]:
        value = alpha * item + (Decimal(1) - alpha) * value
    return value


def _execute_contract_signal(
    *,
    symbol: str,
    action: str,
    margin_budget: str,
    leverage: int,
) -> dict[str, Any]:
    from getagent import trade

    current = trade.contract.current_position(symbol=symbol)
    position = trade.helpers.find_contract_position(current, symbol=symbol)
    if position is not None and position.hold_side == action:
        return {"status": "already_positioned", "hold_side": position.hold_side}
    if position is not None:
        closed = trade.contract.close_position(symbol=symbol, hold_side=position.hold_side)
        if not trade.is_success(closed):
            raise RuntimeError(f"contract close failed: {closed}")

    qty_plan = trade.helpers.compute_qty(
        symbol=symbol,
        market="contract",
        budget_amount=margin_budget,
        leverage=leverage,
    )
    open_position = (
        trade.contract.open_long_market
        if action == "long"
        else trade.contract.open_short_market
    )
    result = open_position(symbol=symbol, qty=qty_plan.qty, leverage=leverage)
    if not trade.is_success(result):
        raise RuntimeError(f"contract open failed: {result}")
    return {"qty": str(qty_plan.qty), "result": result}


def _run_live() -> None:
    cfg = runtime.manifest.get("strategy_config", {}) or {}
    symbol = str((cfg.get("trading_symbols") or ["BTCUSDT"])[0])
    fast_period = int(cfg.get("fast_period", 12) or 12)
    slow_period = int(cfg.get("slow_period", 26) or 26)
    leverage = int(cfg.get("leverage", 3) or 3)
    margin_budget = str(cfg.get("margin_budget", "100") or "100")

    bars = data.crypto.futures.kline(
        symbol=symbol,
        interval="1h",
        exchange="bitget",
        limit=max(slow_period * 4, 100),
        closed_only=True,
    )
    closes = [
        Decimal(str(row["close"]))
        for row in data.to_records(bars)
        if row.get("close") not in (None, "")
    ]
    if len(closes) < slow_period + 2:
        runtime.emit_signal(
            action="hold",
            symbol=symbol,
            confidence=0.0,
            metrics={"rows": len(closes)},
            meta={"reason": "insufficient closed bars"},
        )
        return

    fast_now = _ema(closes, fast_period)
    slow_now = _ema(closes, slow_period)
    fast_previous = _ema(closes[:-1], fast_period)
    slow_previous = _ema(closes[:-1], slow_period)
    crossed_up = fast_previous <= slow_previous and fast_now > slow_now
    crossed_down = fast_previous >= slow_previous and fast_now < slow_now
    action = "long" if crossed_up else "short" if crossed_down else "hold"

    runtime.emit_signal_or_follow(
        action=action,
        symbol=symbol,
        confidence=0.75 if action != "hold" else 0.0,
        metrics={
            "rows": len(closes),
            "fast_ema": float(fast_now),
            "slow_ema": float(slow_now),
        },
        meta={"fast_period": fast_period, "slow_period": slow_period},
        execute_trade=lambda: _execute_contract_signal(
            symbol=symbol,
            action=action,
            margin_budget=margin_budget,
            leverage=leverage,
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
