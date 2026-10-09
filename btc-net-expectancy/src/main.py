import json
import math
from datetime import datetime, timedelta, timezone
from decimal import Decimal, ROUND_DOWN
from pathlib import Path
from typing import Any

import pandas as pd
from getagent import backtest, data, runtime


SYMBOL = "BTCUSDT"
INTERVAL_MS = 3_600_000
STATE_PATH = Path("/workspace/.state/btc-net-expectancy.json")


def _cfg() -> dict[str, Any]:
    return dict(runtime.manifest.get("strategy_config", {}) or {})


def _finite(value: Any) -> Any:
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def _money(value: Any) -> float:
    text = str(value or "0").split()[0]
    try:
        return float(text)
    except (TypeError, ValueError):
        return 0.0


def _trade_metrics(
    result: Any,
    risk_usdt: float,
    funding_by_settlement_ms: dict[int, float],
) -> dict[str, Any]:
    raw = result.raw if isinstance(result.raw, dict) else {}
    reports = raw.get("reports", {}) if isinstance(raw, dict) else {}
    positions = reports.get("positions", []) if isinstance(reports, dict) else []
    scenarios: dict[str, list[float]] = {"0x": [], "1x": [], "2x": []}
    for position in positions if isinstance(positions, list) else []:
        if not isinstance(position, dict) or not position.get("ts_closed"):
            continue
        net = _money(position.get("realized_pnl"))
        commissions = sum(_money(value) for value in position.get("commissions", []))
        quantity = float(position.get("peak_qty", 0) or 0)
        slippage = quantity * 0.1 * 2.0
        opened_ms = _timestamp_ms(position.get("ts_opened"))
        closed_ms = _timestamp_ms(position.get("ts_closed"))
        entry_notional = quantity * float(position.get("avg_px_open", 0) or 0)
        funding = sum(
            entry_notional * rate
            for settlement_ms, rate in funding_by_settlement_ms.items()
            if opened_ms < settlement_ms <= closed_ms
        )
        gross = net + commissions
        total_cost = commissions + slippage + funding
        scenarios["0x"].append(gross)
        scenarios["1x"].append(gross - total_cost)
        scenarios["2x"].append(gross - 2.0 * total_cost)

    def summarize(pnls: list[float]) -> dict[str, float]:
        gross_profit = sum(value for value in pnls if value > 0)
        gross_loss = -sum(value for value in pnls if value < 0)
        return {
            "net_pnl": sum(pnls),
            "expectancy_r": sum(pnls) / len(pnls) / risk_usdt if pnls else 0.0,
            "profit_factor": gross_profit / gross_loss if gross_loss > 0 else 0.0,
        }

    summarized = {key: summarize(value) for key, value in scenarios.items()}
    one_x = scenarios["1x"]
    return {
        "round_trip_trades": len(one_x),
        "win_rate_round_trip": (
            sum(1 for value in one_x if value > 0) / len(one_x) if one_x else 0.0
        ),
        "avg_r": summarized["1x"]["expectancy_r"],
        "net_expectancy_r": summarized["1x"]["expectancy_r"],
        "profit_factor_net": summarized["1x"]["profit_factor"],
        "cost_sensitivity": summarized,
        "funding_settlements_loaded": len(funding_by_settlement_ms),
    }


def _evaluation_metrics(result: Any, trade_metrics: dict[str, Any]) -> dict[str, Any]:
    funding_available = trade_metrics["funding_settlements_loaded"] > 0
    return {
        "trades": trade_metrics["round_trip_trades"],
        "win_rate": trade_metrics["win_rate_round_trip"],
        "avg_r": trade_metrics["avg_r"] if funding_available else None,
        "net_expectancy_r": (
            trade_metrics["net_expectancy_r"] if funding_available else None
        ),
        "profit_factor": (
            trade_metrics["profit_factor_net"] if funding_available else None
        ),
        "avg_r_ex_funding": trade_metrics["avg_r"],
        "net_expectancy_r_ex_funding": trade_metrics["net_expectancy_r"],
        "profit_factor_ex_funding": trade_metrics["profit_factor_net"],
        "funding_status": "modeled" if funding_available else "PENDING",
        "max_drawdown_pct": _finite(result.max_drawdown_pct),
        "sharpe": _finite(result.sharpe_ratio),
        "cost_sensitivity_ex_funding": trade_metrics["cost_sensitivity"],
    }


def _records(value: Any) -> list[dict[str, Any]]:
    return [dict(row) for row in data.to_records(value)]


def _fetch_two_year_frame() -> pd.DataFrame:
    end = datetime(2026, 10, 9, tzinfo=timezone.utc)
    start = datetime(2024, 10, 9, tzinfo=timezone.utc)
    cursor = start
    chunks: list[pd.DataFrame] = []
    while cursor < end:
        chunk_end = min(cursor + timedelta(days=40), end)
        bars = data.crypto.futures.kline(
            symbol=SYMBOL,
            interval="1h",
            exchange="bitget",
            limit=1000,
            start_time=int(cursor.timestamp() * 1000),
            end_time=int(chunk_end.timestamp() * 1000),
            closed_only=True,
        )
        frame = backtest.prepare_frame(bars, datetime_index="date")
        if not frame.empty:
            chunks.append(frame)
        cursor = chunk_end
    if not chunks:
        return pd.DataFrame()
    frame = pd.concat(chunks).sort_index()
    frame = frame[~frame.index.duplicated(keep="last")]
    return frame[(frame.index >= pd.Timestamp(start)) & (frame.index < pd.Timestamp(end))]


def _fetch_historical_funding() -> dict[int, float]:
    end = datetime(2026, 10, 9, tzinfo=timezone.utc)
    start = datetime(2024, 10, 9, tzinfo=timezone.utc)
    settlements: dict[int, float] = {}
    response = data.crypto.futures.funding_rate(
        symbol=SYMBOL,
        exchange="bitget",
        interval="1h",
        limit=1000,
        start_time=int((end - timedelta(days=40)).timestamp() * 1000),
        end_time=int(end.timestamp() * 1000),
    )
    for row in _records(response):
        settlement_ms = _timestamp_ms(row.get("next_funding_time"))
        rate = row.get("funding_rate")
        if settlement_ms > 0 and rate not in (None, ""):
            settlements[settlement_ms] = float(rate)
    if not settlements:
        return {}
    earliest = min(settlements)
    latest = max(settlements)
    if earliest > int((start + timedelta(hours=8)).timestamp() * 1000):
        return {}
    if latest < int((end - timedelta(hours=8)).timestamp() * 1000):
        return {}
    return settlements


def _write_report(
    result: Any,
    frame: pd.DataFrame,
    trade_metrics: dict[str, Any],
) -> None:
    output = Path("/workspace/output")
    output.mkdir(parents=True, exist_ok=True)
    raw = dict(result.raw or {})
    summary = dict(result.summary or {})
    engine_net_pnl = float(summary.get("net_pnl", 0) or 0)
    net_pnl = float(trade_metrics["cost_sensitivity"]["1x"]["net_pnl"])
    margin_budget = float(_cfg()["margin_budget"])
    raw["engine_net_pnl_ex_funding_and_slippage"] = engine_net_pnl
    raw["net_pnl"] = net_pnl
    raw["starting_balance"] = summary.get("starting_balance")
    raw["total_return_pct"] = net_pnl / margin_budget * 100.0
    raw["evidence"] = {
        "source": "Bitget BTCUSDT perpetual 1h bars",
        "rows": len(frame),
        "first_bar": frame.index.min().isoformat(),
        "last_bar": frame.index.max().isoformat(),
        "walk_forward_split": {
            "development": "2024-10-09/2025-10-08",
            "validation": "2025-10-09/2026-10-08",
        },
        "cost_basis": (
            "public maker/taker fees plus two ticks per round trip and modeled historical funding; account-tier rate pending"
            if trade_metrics["funding_settlements_loaded"] > 0
            else "public maker/taker fees plus two ticks per round trip; historical funding and account-tier rate pending"
        ),
    }
    reports = raw.get("reports")
    if isinstance(reports, dict):
        reports.pop("equity_curve", None)
    (output / "backtest_report.json").write_text(
        json.dumps(raw, default=str),
        encoding="utf-8",
    )

    equity = None
    if isinstance(result.raw, dict):
        result_reports = result.raw.get("reports")
        if isinstance(result_reports, dict):
            equity = result_reports.get("equity_curve")
    if isinstance(equity, list) and equity:
        lines = ["timestamp,value,nav"]
        for point in equity:
            if not isinstance(point, dict):
                continue
            lines.append(
                f"{point.get('timestamp','')},{point.get('value','')},{point.get('nav','')}"
            )
        if len(lines) > 1:
            (output / "equity_curve.csv").write_text(
                "\n".join(lines) + "\n",
                encoding="utf-8",
            )


def _run_historical() -> None:
    frame = _fetch_two_year_frame()
    if frame.empty:
        runtime.emit_signal(
            action="watch",
            symbol=SYMBOL,
            confidence=0.0,
            metrics={"rows": 0},
            meta={"reason_code": "NO_REPLAY_DATA"},
        )
        return
    if frame.index.min() > pd.Timestamp("2024-10-09T01:00:00Z"):
        raise RuntimeError(f"two-year replay coverage incomplete: {frame.index.min()}")
    funding_by_settlement_ms = _fetch_historical_funding()
    result = backtest.run(
        ohlcv_data={"BTCUSDT.BITGET": frame},
        spec=runtime.backtest_spec,
    )
    risk_usdt = float(_cfg()["risk_usdt"])
    trade_metrics = _trade_metrics(result, risk_usdt, funding_by_settlement_ms)

    development_spec = json.loads(json.dumps(dict(runtime.backtest_spec)))
    development_spec["execution"] = {
        "start": "2024-10-09T00:00:00Z",
        "end": "2025-10-09T00:00:00Z",
    }
    validation_spec = json.loads(json.dumps(dict(runtime.backtest_spec)))
    validation_spec["execution"] = {
        "start": "2025-10-09T00:00:00Z",
        "end": "2026-10-09T00:00:00Z",
    }
    development_result = backtest.run(
        ohlcv_data={"BTCUSDT.BITGET": frame},
        spec=development_spec,
    )
    validation_result = backtest.run(
        ohlcv_data={"BTCUSDT.BITGET": frame},
        spec=validation_spec,
    )
    development_metrics = _trade_metrics(
        development_result,
        risk_usdt,
        funding_by_settlement_ms,
    )
    validation_metrics = _trade_metrics(
        validation_result,
        risk_usdt,
        funding_by_settlement_ms,
    )
    walk_forward = {
        "development": _evaluation_metrics(development_result, development_metrics),
        "validation": _evaluation_metrics(validation_result, validation_metrics),
    }
    _write_report(result, frame, trade_metrics)
    chart_path = backtest.generate_chart(result)
    summary = dict(result.summary or {})
    metrics = {
        "net_pnl": trade_metrics["cost_sensitivity"]["1x"]["net_pnl"],
        "engine_net_pnl_ex_funding_and_slippage": float(summary.get("net_pnl", 0) or 0),
        "total_return_pct": _finite(result.total_return_pct),
        "max_drawdown_pct": _finite(result.max_drawdown_pct),
        "sharpe_ratio": _finite(result.sharpe_ratio),
        "profit_factor": _finite(result.profit_factor),
        "win_rate": _finite(result.win_rate),
        "total_trades": result.total_trades,
        "round_trip_trades": trade_metrics["round_trip_trades"],
        "win_rate_round_trip": trade_metrics["win_rate_round_trip"],
        "rows": len(frame),
        "avg_r": trade_metrics["avg_r"] if funding_by_settlement_ms else None,
        "net_expectancy_r": (
            trade_metrics["net_expectancy_r"] if funding_by_settlement_ms else None
        ),
        "profit_factor_net": (
            trade_metrics["profit_factor_net"] if funding_by_settlement_ms else None
        ),
        "avg_r_ex_funding": trade_metrics["avg_r"],
        "net_expectancy_r_ex_funding": trade_metrics["net_expectancy_r"],
        "profit_factor_ex_funding": trade_metrics["profit_factor_net"],
        "cost_sensitivity_0x": trade_metrics["cost_sensitivity"]["0x"]["expectancy_r"],
        "cost_sensitivity_1x": trade_metrics["cost_sensitivity"]["1x"]["expectancy_r"],
        "cost_sensitivity_2x": trade_metrics["cost_sensitivity"]["2x"]["expectancy_r"],
    }
    if trade_metrics["round_trip_trades"] < 30:
        verdict = "PENDING_FEWER_THAN_30_TRADES"
    elif not funding_by_settlement_ms:
        verdict = "PENDING_HISTORICAL_FUNDING"
    else:
        verdict = "PENDING_FORWARD"
    runtime.emit_signal(
        action="watch",
        symbol=SYMBOL,
        confidence=float(result.win_rate or 0),
        metrics=metrics,
        meta={
            "verdict": verdict,
            "chart_path": chart_path,
            "period_start": frame.index.min().isoformat(),
            "period_end": frame.index.max().isoformat(),
            "walk_forward_split": {
                "development": "2024-10-09/2025-10-08",
                "validation": "2025-10-09/2026-10-08",
            },
            "walk_forward": walk_forward,
            "selection_note": "validation is a fixed time split, but prior aggregate candidate inspection creates selection leakage",
            "cost_sensitivity_ex_funding": trade_metrics["cost_sensitivity"],
            "pending": (
                ["account-tier fees"]
                if funding_by_settlement_ms
                else ["account-tier fees", "historical funding"]
            ),
        },
    )


def _read_state() -> dict[str, Any]:
    if not STATE_PATH.exists():
        return {
            "owned_position": False,
            "entry_order_id": "",
            "entry_order_time_ms": 0,
            "entry_time_ms": 0,
            "entry_price": "",
            "daily_date": "",
            "daily_realized_usdt": "0",
            "playbook_realized_usdt": "0",
            "consecutive_losses": 0,
            "actions": [],
        }
    return dict(json.loads(STATE_PATH.read_text(encoding="utf-8")))


def _write_state(state: dict[str, Any]) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, default=str), encoding="utf-8")


def _timestamp_ms(value: Any) -> int:
    if value in (None, ""):
        return 0
    text = str(value)
    if text.isdigit():
        number = int(text)
        return number if number > 10_000_000_000 else number * 1000
    return int(datetime.fromisoformat(text.replace("Z", "+00:00")).timestamp() * 1000)


def _ema(values: list[Decimal], period: int) -> Decimal:
    alpha = Decimal(2) / Decimal(period + 1)
    current = values[0]
    for value in values[1:]:
        current = alpha * value + (Decimal(1) - alpha) * current
    return current


def _atr(rows: list[dict[str, Any]], period: int) -> Decimal:
    ranges: list[Decimal] = []
    for idx in range(1, len(rows)):
        high = Decimal(str(rows[idx]["high"]))
        low = Decimal(str(rows[idx]["low"]))
        previous = Decimal(str(rows[idx - 1]["close"]))
        ranges.append(max(high - low, abs(high - previous), abs(low - previous)))
    return sum(ranges[-period:], Decimal("0")) / Decimal(period)


def _adx(rows: list[dict[str, Any]], period: int) -> Decimal:
    dx_values: list[Decimal] = []
    for end in range(len(rows) - period + 1, len(rows) + 1):
        plus = Decimal("0")
        minus = Decimal("0")
        true_range = Decimal("0")
        for idx in range(end - period, end):
            high = Decimal(str(rows[idx]["high"]))
            low = Decimal(str(rows[idx]["low"]))
            previous_high = Decimal(str(rows[idx - 1]["high"]))
            previous_low = Decimal(str(rows[idx - 1]["low"]))
            previous_close = Decimal(str(rows[idx - 1]["close"]))
            up = high - previous_high
            down = previous_low - low
            plus += up if up > down and up > 0 else Decimal("0")
            minus += down if down > up and down > 0 else Decimal("0")
            true_range += max(high - low, abs(high - previous_close), abs(low - previous_close))
        if true_range <= 0:
            continue
        plus_di = Decimal("100") * plus / true_range
        minus_di = Decimal("100") * minus / true_range
        denominator = plus_di + minus_di
        if denominator > 0:
            dx_values.append(Decimal("100") * abs(plus_di - minus_di) / denominator)
    return sum(dx_values, Decimal("0")) / Decimal(len(dx_values)) if dx_values else Decimal("0")


def _rsi(values: list[Decimal], period: int) -> Decimal:
    if len(values) < period + 1:
        return Decimal("50")
    changes = [
        values[idx] - values[idx - 1]
        for idx in range(len(values) - period, len(values))
    ]
    average_gain = sum((max(change, Decimal("0")) for change in changes), Decimal("0")) / Decimal(period)
    average_loss = sum((max(-change, Decimal("0")) for change in changes), Decimal("0")) / Decimal(period)
    if average_loss <= 0:
        return Decimal("100")
    relative_strength = average_gain / average_loss
    return Decimal("100") - Decimal("100") / (Decimal("1") + relative_strength)


def _emit_hold(code: str, metrics: dict[str, Any], state: dict[str, Any]) -> None:
    runtime.emit_signal_or_follow(
        action="hold",
        symbol=SYMBOL,
        confidence=0.0,
        metrics=metrics,
        meta={"reason_code": code},
        execute_trade=None,
        reason_code=code,
    )
    _write_state(state)


def _extract_order_id(result: Any) -> str:
    for key in ("order_id", "orderId"):
        value = getattr(result, key, None)
        if value:
            return str(value)
    if isinstance(result, dict):
        for container in (result, result.get("data", {})):
            if isinstance(container, dict):
                for key in ("order_id", "orderId"):
                    if container.get(key):
                        return str(container[key])
    return ""


def _execute_entry(
    *,
    entry: Decimal,
    stop: Decimal,
    target: Decimal,
    qty: Any,
    leverage: int,
    state: dict[str, Any],
    now_ms: int,
) -> Any:
    from getagent import trade

    leverage_result = trade.contract.change_leverage(SYMBOL, leverage)
    if not trade.is_success(leverage_result):
        raise RuntimeError(f"leverage change failed: {leverage_result}")
    tpsl = trade.helpers.resolve_contract_tpsl(
        symbol=SYMBOL,
        side="long",
        leverage=leverage,
        tp_trigger_price=target,
        sl_trigger_price=stop,
        reference_price=entry,
    )
    result = trade.contract.place_order(
        symbol=SYMBOL,
        side="buy",
        order_type="limit",
        qty=qty,
        price=entry,
        margin_mode="isolated",
        margin_coin="USDT",
        pos_side="long",
        trade_side="open",
        tp_trigger_price=tpsl.tp_trigger_price,
        sl_trigger_price=tpsl.sl_trigger_price,
    )
    if not trade.is_success(result):
        raise RuntimeError(f"entry failed: {result}")
    order_id = _extract_order_id(result)
    if not order_id:
        raise RuntimeError("entry accepted without auditable order id")
    state["entry_order_id"] = order_id
    state["entry_order_time_ms"] = now_ms
    state["entry_price"] = str(entry)
    state["owned_position"] = True
    state["entry_time_ms"] = now_ms
    state["actions"] = (
        list(state.get("actions", []))[-49:]
        + [{
            "timestamp": datetime.fromtimestamp(now_ms / 1000, tz=timezone.utc).isoformat(),
            "symbol": SYMBOL,
            "side": "long",
            "intended_price": str(entry),
            "filled_price": "PENDING",
            "fees": "PENDING",
            "funding": "PENDING",
            "reason_code": "LONG_PULLBACK_RECOVERY",
        }]
    )
    _write_state(state)
    return result


def _run_live() -> None:
    from getagent import trade

    cfg = _cfg()
    now = datetime.now(timezone.utc)
    now_ms = int(now.timestamp() * 1000)
    state = _read_state()
    today = now.date().isoformat()
    if state.get("daily_date") != today:
        state["daily_date"] = today
        state["daily_realized_usdt"] = "0"
    if not bool(cfg.get("activation_eligible", False)):
        _emit_hold("RESEARCH_VALIDATION_FAILED", {}, state)
        return

    if not trade.account.subaccount_exists():
        _emit_hold("NO_ISOLATED_SUBACCOUNT", {}, state)
        return
    support = trade.market.check_symbol_support([SYMBOL])
    if not trade.is_success(support):
        _emit_hold("SYMBOL_NOT_SUPPORTED_FOR_SUBACCOUNT", {}, state)
        return

    all_positions = trade.contract.current_position()
    if not trade.is_success(all_positions):
        _emit_hold("POSITION_QUERY_FAILED", {}, state)
        return
    open_symbols = trade.helpers.contract_open_symbols(all_positions)
    if any(symbol != SYMBOL for symbol in open_symbols):
        _emit_hold("UNRECOGNIZED_POSITION_ALERT", {"open_symbols": open_symbols}, state)
        return
    current = trade.helpers.find_contract_position(all_positions, symbol=SYMBOL, hold_side="long")
    if current is not None and not bool(state.get("owned_position")):
        _emit_hold("UNRECOGNIZED_POSITION_ALERT", {"open_symbols": open_symbols}, state)
        return

    pending = trade.contract.pending_orders(symbol=SYMBOL)
    if not trade.is_success(pending):
        _emit_hold("PENDING_ORDER_QUERY_FAILED", {}, state)
        return
    order_id = str(state.get("entry_order_id", ""))
    order_time = int(state.get("entry_order_time_ms", 0) or 0)
    if order_id and now_ms - order_time >= int(cfg["order_ttl_hours"]) * INTERVAL_MS:
        located = trade.helpers.find_contract_order(pending, order_id)
        if located is not None:
            cancelled = trade.contract.cancel_order(SYMBOL, order_id)
            if not trade.is_success(cancelled):
                _emit_hold("ORDER_CANCEL_FAILED", {}, state)
                return
        state["entry_order_id"] = ""
        state["entry_order_time_ms"] = 0
        if current is None:
            state["owned_position"] = False

    if current is not None:
        held_ms = now_ms - int(state.get("entry_time_ms", now_ms) or now_ms)
        if held_ms >= int(cfg["time_stop_hours"]) * INTERVAL_MS:
            runtime.emit_signal_or_follow(
                action="close",
                symbol=SYMBOL,
                confidence=1.0,
                metrics={"held_hours": held_ms / INTERVAL_MS},
                meta={"reason_code": "TIME_STOP"},
                execute_trade=lambda: trade.contract.close_position(SYMBOL, "long"),
                reason_code="TIME_STOP",
            )
            return
        _emit_hold("POSITION_MANAGED_BY_ATTACHED_TPSL", {"held_hours": held_ms / INTERVAL_MS}, state)
        return

    daily_realized = Decimal(str(state.get("daily_realized_usdt", "0")))
    total_realized = Decimal(str(state.get("playbook_realized_usdt", "0")))
    if daily_realized <= -Decimal(str(cfg["daily_pause_loss_usdt"])):
        _emit_hold("DAILY_LOSS_PAUSE", {"daily_realized_usdt": float(daily_realized)}, state)
        return
    if total_realized <= -Decimal(str(cfg["playbook_stop_loss_usdt"])):
        _emit_hold("PLAYBOOK_LOSS_HALT", {"playbook_realized_usdt": float(total_realized)}, state)
        return
    if int(state.get("consecutive_losses", 0)) >= int(cfg["consecutive_loss_halt"]):
        _emit_hold("CONSECUTIVE_LOSS_HALT", {}, state)
        return

    ticker_rows = _records(
        data.crypto.futures.ticker(symbol=SYMBOL, exchange="bitget", include_market_data=True)
    )
    if not ticker_rows:
        _emit_hold("NO_TICKER", {}, state)
        return
    ticker = ticker_rows[-1]
    ticker_ms = _timestamp_ms(ticker.get("timestamp"))
    if ticker_ms <= 0 or now_ms - ticker_ms > 60_000:
        _emit_hold("STALE_DATA", {"ticker_age_ms": now_ms - ticker_ms}, state)
        return
    bid = Decimal(str(ticker["bid"]))
    ask = Decimal(str(ticker["ask"]))
    midpoint = (bid + ask) / Decimal("2")
    spread_bps = (ask - bid) / midpoint * Decimal("10000")
    quote_volume = Decimal(str(ticker["quote_volume"]))
    if spread_bps > Decimal(str(cfg["max_spread_bps"])):
        _emit_hold("SPREAD_GATE", {"spread_bps": float(spread_bps)}, state)
        return
    if quote_volume < Decimal(str(cfg["min_24h_volume_usdt"])):
        _emit_hold("VOLUME_GATE", {"quote_volume": float(quote_volume)}, state)
        return

    funding_rows = _records(
        data.crypto.futures.funding_rate(
            symbol=SYMBOL,
            exchange="bitget",
            interval="1h",
            limit=8,
            days=1,
        )
    )
    if not funding_rows:
        _emit_hold("NO_FUNDING_DATA", {}, state)
        return
    funding = funding_rows[-1]
    next_funding_ms = _timestamp_ms(funding.get("next_funding_time"))
    blackout_ms = int(cfg["funding_blackout_minutes"]) * 60_000
    if next_funding_ms and abs(next_funding_ms - now_ms) <= blackout_ms:
        _emit_hold("FUNDING_BLACKOUT", {}, state)
        return

    bars = data.crypto.futures.kline(
        symbol=SYMBOL,
        interval="1h",
        exchange="bitget",
        limit=max(
            int(cfg["atr_percentile_lookback"]) + 20,
            int(cfg["long_trend_period"]) + int(cfg["trend_slope_hours"]) + 2,
        ),
        days=10,
        closed_only=True,
    )
    rows = _records(bars)
    minimum_rows = max(
        int(cfg["atr_percentile_lookback"]) + int(cfg["atr_period"]),
        int(cfg["long_trend_period"]) + int(cfg["trend_slope_hours"]),
    )
    if len(rows) < minimum_rows:
        _emit_hold("INSUFFICIENT_BARS", {"rows": len(rows)}, state)
        return
    last_bar_ms = _timestamp_ms(rows[-1].get("date"))
    if last_bar_ms <= 0 or now_ms - (last_bar_ms + INTERVAL_MS) > 2 * INTERVAL_MS:
        _emit_hold("STALE_BAR_DATA", {}, state)
        return

    closes = [Decimal(str(row["close"])) for row in rows]
    atr_period = int(cfg["atr_period"])
    atr = _atr(rows, atr_period)
    adx = _adx(rows, int(cfg["adx_period"]))
    lookback = int(cfg["atr_percentile_lookback"])
    atr_samples = [_atr(rows[:idx], atr_period) for idx in range(len(rows) - lookback + 1, len(rows) + 1)]
    atr_percentile = Decimal("100") * Decimal(sum(1 for value in atr_samples if value <= atr)) / Decimal(len(atr_samples))
    close = closes[-1]
    trend_period = int(cfg["long_trend_period"])
    trend_slope_hours = int(cfg["trend_slope_hours"])
    trend_now = _ema(closes[-trend_period:], trend_period)
    trend_then = _ema(
        closes[-trend_period - trend_slope_hours : -trend_slope_hours],
        trend_period,
    )
    rsi_period = int(cfg["rsi_period"])
    rsi_now = _rsi(closes, rsi_period)
    rsi_previous = _rsi(closes[:-1], rsi_period)
    recovery_level = Decimal(str(cfg["rsi_recovery_level"]))
    signal_ok = (
        rsi_previous < recovery_level <= rsi_now
        and close > trend_now
        and trend_now > trend_then
        and adx >= Decimal(str(cfg["adx_min"]))
        and adx <= Decimal(str(cfg["adx_max"]))
        and Decimal(str(cfg["atr_percentile_min"])) <= atr_percentile <= Decimal(str(cfg["atr_percentile_max"]))
    )
    if not signal_ok:
        _emit_hold(
            "NO_VALID_SIGNAL",
            {"adx": float(adx), "atr_percentile": float(atr_percentile)},
            state,
        )
        return

    leverage = min(int(cfg["leverage"]), 5)
    rules = trade.helpers.contract_rules(SYMBOL)
    tick = Decimal(str(rules.price_step))
    entry = ((bid - tick) / tick).to_integral_value(rounding=ROUND_DOWN) * tick
    stop_distance = Decimal(str(cfg["atr_stop_multiple"])) * atr
    stop = ((entry - stop_distance) / tick).to_integral_value(rounding=ROUND_DOWN) * tick
    actual_stop_distance = entry - stop
    target = (
        (entry + Decimal(str(cfg["take_profit_r"])) * actual_stop_distance) / tick
    ).to_integral_value(rounding=ROUND_DOWN) * tick
    risk = Decimal(str(cfg["risk_usdt"]))
    desired_qty = risk / (entry - stop)
    desired_notional = desired_qty * entry
    margin_needed = desired_notional / Decimal(leverage)
    if margin_needed > Decimal(str(cfg["margin_budget"])):
        _emit_hold("MARGIN_BUDGET_GATE", {"margin_needed": float(margin_needed)}, state)
        return
    qty_plan = trade.helpers.compute_qty(
        symbol=SYMBOL,
        market="contract",
        budget_amount=margin_needed,
        leverage=leverage,
        price=entry,
    )
    expected_funding = desired_notional * max(Decimal(str(funding["funding_rate"])), Decimal("0"))
    if expected_funding > risk * Decimal(str(cfg["funding_r_limit"])):
        _emit_hold("FUNDING_COST_GATE", {"expected_funding_usdt": float(expected_funding)}, state)
        return

    runtime.emit_signal_or_follow(
        action="long",
        symbol=SYMBOL,
        confidence=min(float(adx / Decimal("100")), 1.0),
        metrics={
            "spread_bps": float(spread_bps),
            "quote_volume_24h": float(quote_volume),
            "risk_usdt": float(risk),
            "expected_funding_usdt": float(expected_funding),
        },
        meta={
            "reason_code": "LONG_PULLBACK_RECOVERY",
            "entry": str(entry),
            "stop": str(stop),
            "target": str(target),
            "quantity": str(qty_plan.qty),
        },
        execute_trade=lambda: _execute_entry(
            entry=entry,
            stop=stop,
            target=target,
            qty=qty_plan.qty,
            leverage=leverage,
            state=state,
            now_ms=now_ms,
        ),
        reason_code="LONG_PULLBACK_RECOVERY",
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
