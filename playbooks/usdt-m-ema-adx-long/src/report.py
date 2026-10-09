"""Turn closed trades into the validation numbers the report is allowed to quote.

Missing funding on any trade makes net expectancy PENDING. This module never
fills that gap with a zero or a guessed rate.
"""

from typing import Sequence

try:
    from .risk import ClosedTrade, expectancy_r
except ImportError:
    from risk import ClosedTrade, expectancy_r


def _mean(values: Sequence[float]) -> float | None:
    if not values:
        return None
    return sum(values) / len(values)


def profit_factor(nets: Sequence[float]) -> float | None:
    gains = sum(value for value in nets if value > 0)
    losses = sum(value for value in nets if value < 0)
    if losses == 0:
        return None if gains == 0 else None
    return gains / abs(losses)


def max_drawdown_pct(nets: Sequence[float], start_equity: float) -> float | None:
    if start_equity <= 0:
        return None
    equity = start_equity
    peak = start_equity
    worst = 0.0
    for net in nets:
        equity += net
        peak = max(peak, equity)
        if peak > 0:
            worst = max(worst, (peak - equity) / peak)
    return 100.0 * worst


def summarize(trades: Sequence[ClosedTrade], cost_multiplier: float, start_equity: float) -> dict[str, float | int | str | None]:
    nets: list[float] = []
    pending = False
    for trade in trades:
        net = trade.net(cost_multiplier)
        if net is None:
            pending = True
            break
        nets.append(net)
    if pending:
        return {
            "trades": len(trades),
            "win_rate": None,
            "avg_r": None,
            "expectancy_r": None,
            "profit_factor": None,
            "max_drawdown_pct": None,
            "status": "PENDING",
            "pending_reason": "at least one closed trade has unknown funding",
        }
    if not nets:
        return {
            "trades": 0,
            "win_rate": None,
            "avg_r": None,
            "expectancy_r": None,
            "profit_factor": None,
            "max_drawdown_pct": None,
            "status": "NO_TRADES",
            "pending_reason": None,
        }
    wins = sum(1 for value in nets if value > 0)
    r_values = []
    for trade, net in zip(trades, nets):
        if trade.risk_usdt <= 0:
            return {
                "trades": len(trades),
                "win_rate": None,
                "avg_r": None,
                "expectancy_r": None,
                "profit_factor": None,
                "max_drawdown_pct": None,
                "status": "PENDING",
                "pending_reason": "closed trade is missing a positive risk unit",
            }
        r_values.append(net / trade.risk_usdt)
    return {
        "trades": len(trades),
        "win_rate": wins / len(nets),
        "avg_r": _mean(r_values),
        "expectancy_r": expectancy_r(trades, cost_multiplier),
        "profit_factor": profit_factor(nets),
        "max_drawdown_pct": max_drawdown_pct(nets, start_equity),
        "net_pnl": sum(nets),
        "status": "OK",
        "pending_reason": None,
    }


def rule_trades(trades: Sequence[ClosedTrade]) -> list[ClosedTrade]:
    """Drop end-of-replay flats that are not a strategy exit."""
    return [trade for trade in trades if trade.reason_code != "BACKTEST_SHUTDOWN"]


def split_by_entry(
    trades: Sequence[ClosedTrade], split_iso: str
) -> tuple[list[ClosedTrade], list[ClosedTrade]]:
    train: list[ClosedTrade] = []
    test: list[ClosedTrade] = []
    for trade in trades:
        if trade.entry_ts < split_iso:
            train.append(trade)
        else:
            test.append(trade)
    return train, test


def activation_verdict(
    *,
    full: dict[str, float | int | str | None],
    cost_2x: dict[str, float | int | str | None],
    fee_tier_status: str,
    engine_sharpe: float | None,
    live_trades: int,
    live_profit_factor: float | None = None,
    live_sharpe: float | None = None,
) -> tuple[str, list[str]]:
    """Return (verdict, reasons). Live trading stays off until every gate is met.

    Forward PASS is PF >= 1.3 and Sharpe >= 0.5 after at least 30 live trades.
    Forward FAIL is PF <= 1.1 once that sample exists. Fewer than 30 live
    trades is not a pass and not a fail.
    """
    reasons: list[str] = []
    if fee_tier_status != "VERIFIED":
        reasons.append("fee_tier_pending")
    if full.get("status") != "OK" or cost_2x.get("status") != "OK":
        reasons.append("backtest_metrics_pending")
    trades = int(full.get("trades") or 0)
    if trades < 30:
        reasons.append("backtest_trades_below_30")
    expectancy_2x = cost_2x.get("expectancy_r")
    if not isinstance(expectancy_2x, (int, float)) or expectancy_2x <= 0:
        reasons.append("negative_or_missing_expectancy_at_2x_costs")
    expectancy_1x = full.get("expectancy_r")
    if not isinstance(expectancy_1x, (int, float)) or expectancy_1x <= 0:
        reasons.append("negative_or_missing_expectancy_at_1x_costs")
    if full.get("profit_factor") is None or cost_2x.get("profit_factor") is None:
        reasons.append("profit_factor_undefined_or_pending")
    if engine_sharpe is None or not isinstance(engine_sharpe, (int, float)):
        reasons.append("sharpe_pending")
    if live_trades < 30:
        reasons.append("forward_sample_below_30")
    elif live_profit_factor is None or live_sharpe is None:
        reasons.append("forward_metrics_pending")
    elif live_profit_factor <= 1.1:
        reasons.append("forward_fail_profit_factor")
    elif not (live_profit_factor >= 1.3 and live_sharpe >= 0.5):
        reasons.append("forward_not_pass")
    if reasons:
        return "do_not_activate", reasons
    return "activate", []
