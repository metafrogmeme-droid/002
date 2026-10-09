"""Local, reproducible portfolio simulator for the BTC/ETH/SOL regime Playbook.

Engine label used in all reports: LOCAL-RESEARCH-ENGINE (this file).

Fill / exit model (1H bars, conservative where the bar is ambiguous):
  * Signal evaluated on a CLOSED bar. A limit order is placed at the signal close
    (rounded to tick) and lives for ``entry_ttl_hours`` bars, then is cancelled.
  * A long limit fills only if a later bar trades strictly through it
    (low < limit - 1 tick). Fill price = limit, maker fee.
  * Stop = limit -/+ stop_atr_mult * ATR(signal bar); TP = fixed R multiple.
    Both are modelled as exchange-side triggers attached to the entry order.
  * Stop/TP triggers fill as taker market orders with ``slippage_ticks`` adverse
    slippage. A bar that opens beyond the stop fills at the open (gap) minus slippage.
  * If stop and TP are both inside one bar, the stop is assumed first.
    In the fill bar only the stop is checked (TP ignored: order unknown).
  * Time stop at the close of the bar where (bar close - fill bar open) >= time_stop_hours,
    taker + slippage. If that close falls inside a funding block window the exit is
    deferred one bar (the Playbook does not act inside the window).
  * Funding: every settlement at a bar open while a position is held is charged
    qty * open * rate (longs pay positive rates).
Portfolio rules: max concurrent (positions + pending orders), one per symbol,
daily realised pause / stop, consecutive-loss halt. A Playbook "stop" or
consecutive-loss halt is simulated as "no new entries until the next UTC day"
(live it requires a manual restart) and every occurrence is counted.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pandas as pd

import sys
from pathlib import Path

PKG_SRC = Path(__file__).resolve().parents[2] / "playbooks" / "btc-eth-sol-regime-long" / "src"
sys.path.insert(0, str(PKG_SRC.parent))
from src.features import (  # noqa: E402
    compute_indicators,
    compute_signals,
    funding_blocks,
    in_funding_window,
)

HOUR_MS = 3_600_000
DAY_MS = 86_400_000

TICKS = {"BTCUSDT": 0.1, "ETHUSDT": 0.01, "SOLUSDT": 0.001}
SIZE_STEPS = {"BTCUSDT": 0.0001, "ETHUSDT": 0.01, "SOLUSDT": 0.1}

SIM_DEFAULTS: dict[str, Any] = {
    "risk_per_trade_usdt": 15.0,
    "max_leverage": 5.0,
    "margin_budget": 1500.0,
    "max_concurrent": 3,
    "stop_atr_mult": 1.5,
    "tp_r_multiple": 2.0,
    "time_stop_hours": 8,
    "entry_ttl_hours": 4,
    "daily_pause_usdt": 30.0,
    "daily_stop_usdt": 40.0,
    "max_consecutive_losses": 5,
    "funding_block_minutes": 15,
    "funding_max_against": 0.0003,
    "maker_fee": 0.0002,
    "taker_fee": 0.0006,
    "slippage_ticks": 1,
}


@dataclass
class Order:
    symbol: str
    side: str
    signal_i: int
    limit: float
    stop: float
    tp: float
    qty: float
    expiry_i: int
    regime: str
    adx: float


@dataclass
class Position:
    symbol: str
    side: str
    signal_i: int
    entry_i: int
    entry: float
    stop: float
    tp: float
    qty: float
    regime: str
    adx: float
    fees: float = 0.0
    funding: float = 0.0
    slippage: float = 0.0


@dataclass
class SimResult:
    trades: pd.DataFrame
    events: dict[str, int]
    skips: dict[str, int]
    daily_pnl: pd.Series
    start_ms: int
    end_ms: int
    params: dict[str, Any] = field(default_factory=dict)


def _round_tick(px: float, tick: float) -> float:
    return round(round(px / tick) * tick, 10)


def _floor_step(qty: float, step: float) -> float:
    return math.floor(qty / step + 1e-9) * step


def prepare(raw: dict[str, pd.DataFrame], cfg: dict[str, Any]) -> dict[str, pd.DataFrame]:
    out = {}
    for sym, df in raw.items():
        ind = compute_indicators(df.set_index("ts"), cfg)
        out[sym] = compute_signals(ind, cfg)
    return out


def funding_lookup(funding: pd.DataFrame) -> tuple[dict[int, float], np.ndarray, np.ndarray]:
    by_ts = dict(zip(funding["ts"].astype("int64"), funding["rate"].astype(float)))
    ts_arr = funding["ts"].astype("int64").to_numpy()
    rate_arr = funding["rate"].astype(float).to_numpy()
    return by_ts, ts_arr, rate_arr


def simulate(
    frames: dict[str, pd.DataFrame],
    funding: dict[str, pd.DataFrame],
    start_ms: int,
    end_ms: int,
    sides: tuple[str, ...] = ("long",),
    cost_mult: float = 1.0,
    params: dict[str, Any] | None = None,
) -> SimResult:
    p = dict(SIM_DEFAULTS)
    p.update(params or {})
    symbols = list(frames)
    index = frames[symbols[0]].index.to_numpy()
    for s in symbols:
        if not np.array_equal(frames[s].index.to_numpy(), index):
            raise ValueError("frames must share one hourly index")
    cols = {}
    for s in symbols:
        f = frames[s]
        cols[s] = {c: f[c].to_numpy() for c in
                   ("open", "high", "low", "close", "atr", "adx", "signal_long", "signal_short", "regime")}
    fund = {s: funding_lookup(funding[s]) for s in symbols}

    first_i = int(np.searchsorted(index, start_ms))
    last_signal_i = int(np.searchsorted(index, end_ms)) - 1
    n = len(index)

    pending: dict[str, Order] = {}
    positions: dict[str, Position] = {}
    trades: list[dict[str, Any]] = []
    events = {"daily_pause": 0, "daily_stop": 0, "consecutive_loss_halt": 0}
    skips = {k: 0 for k in ("funding_window", "funding_against", "size_cap", "slots", "paused",
                             "qty_below_min", "invalid_atr")}
    daily: dict[int, float] = {}
    consec = 0
    paused_day = -1
    halted_day = -1

    risk = float(p["risk_per_trade_usdt"])
    maker = float(p["maker_fee"]) * cost_mult
    taker = float(p["taker_fee"]) * cost_mult
    slip_ticks = float(p["slippage_ticks"]) * cost_mult
    fund_mult = cost_mult
    slot_margin = float(p["margin_budget"]) / int(p["max_concurrent"])
    max_notional = slot_margin * float(p["max_leverage"])
    time_stop_bars = int(p["time_stop_hours"])
    ttl = int(p["entry_ttl_hours"])
    block_min = int(p["funding_block_minutes"])

    def realise(pos: Position, exit_i: int, raw_exit: float, reason: str, exit_ms: int) -> None:
        nonlocal consec, paused_day, halted_day
        tick = TICKS[pos.symbol]
        sgn = 1.0 if pos.side == "long" else -1.0
        fill = raw_exit - sgn * slip_ticks * tick
        slip_cost = slip_ticks * tick * pos.qty
        exit_fee = fill * pos.qty * taker
        gross = sgn * (raw_exit - pos.entry) * pos.qty
        fees = pos.fees + exit_fee
        net = gross - fees - slip_cost - pos.funding
        day = exit_ms // DAY_MS
        daily[day] = daily.get(day, 0.0) + net
        trades.append({
            "symbol": pos.symbol, "side": pos.side,
            "signal_ts": int(index[pos.signal_i]) + HOUR_MS,
            "entry_bar_ts": int(index[pos.entry_i]), "exit_ts": exit_ms,
            "entry": pos.entry, "stop": pos.stop, "tp": pos.tp, "exit_raw": raw_exit,
            "exit_fill": fill, "qty": pos.qty, "notional": pos.qty * pos.entry,
            "exit_reason": reason, "gross_pnl": gross, "fees": fees,
            "slippage": slip_cost, "funding": pos.funding, "net_pnl": net,
            "r_gross": gross / risk, "r_net": net / risk,
            "regime": pos.regime, "adx": pos.adx,
            "hold_hours": (exit_ms - int(index[pos.entry_i])) / HOUR_MS,
        })
        consec = consec + 1 if net < 0 else 0
        if consec >= int(p["max_consecutive_losses"]):
            events["consecutive_loss_halt"] += 1
            halted_day = day
            consec = 0
        if daily[day] <= -float(p["daily_stop_usdt"]) and halted_day != day:
            events["daily_stop"] += 1
            halted_day = day
        elif daily[day] <= -float(p["daily_pause_usdt"]) and paused_day != day:
            events["daily_pause"] += 1
            paused_day = day

    for i in range(first_i, n):
        t_open = int(index[i])
        t_close = t_open + HOUR_MS
        day = t_open // DAY_MS

        # 1) funding on positions carried into this bar, then exits.
        for sym in list(positions):
            pos = positions[sym]
            c = cols[sym]
            by_ts = fund[sym][0]
            if pos.entry_i < i and t_open in by_ts:
                sgn = 1.0 if pos.side == "long" else -1.0
                pos.funding += sgn * pos.qty * c["open"][i] * by_ts[t_open] * fund_mult
            o, h, l, cl = c["open"][i], c["high"][i], c["low"][i], c["close"][i]
            if pos.entry_i == i:
                continue
            if pos.side == "long":
                if o <= pos.stop:
                    realise(pos, i, o, "SL_GAP", t_open); del positions[sym]; continue
                if l <= pos.stop:
                    realise(pos, i, pos.stop, "SL", t_open); del positions[sym]; continue
                if o >= pos.tp:
                    realise(pos, i, o, "TP_GAP", t_open); del positions[sym]; continue
                if h >= pos.tp:
                    realise(pos, i, pos.tp, "TP", t_open); del positions[sym]; continue
            else:
                if o >= pos.stop:
                    realise(pos, i, o, "SL_GAP", t_open); del positions[sym]; continue
                if h >= pos.stop:
                    realise(pos, i, pos.stop, "SL", t_open); del positions[sym]; continue
                if o <= pos.tp:
                    realise(pos, i, o, "TP_GAP", t_open); del positions[sym]; continue
                if l <= pos.tp:
                    realise(pos, i, pos.tp, "TP", t_open); del positions[sym]; continue
            if (i - pos.entry_i + 1) >= time_stop_bars and not in_funding_window(t_close, block_min):
                realise(pos, i, cl, "TIME", t_close); del positions[sym]

        # 2) risk state after this bar's exits; cancel pending orders when paused/halted.
        blocked_today = (paused_day == day) or (halted_day == day)
        if blocked_today and pending:
            pending.clear()

        # 3) pending limit fills / expiry.
        for sym in list(pending):
            od = pending[sym]
            c = cols[sym]
            tick = TICKS[sym]
            filled = (c["low"][i] < od.limit - tick) if od.side == "long" else (c["high"][i] > od.limit + tick)
            if filled:
                pos = Position(sym, od.side, od.signal_i, i, od.limit, od.stop, od.tp, od.qty, od.regime, od.adx)
                pos.fees = od.limit * od.qty * maker
                del pending[sym]
                stop_hit = (c["low"][i] <= od.stop) if od.side == "long" else (c["high"][i] >= od.stop)
                if stop_hit:
                    realise(pos, i, od.stop, "SL_FILL_BAR", t_open)
                else:
                    positions[sym] = pos
            elif i >= od.expiry_i:
                del pending[sym]

        # 4) new signals on this closed bar.
        if i > last_signal_i:
            if not positions and not pending:
                break
            continue
        for sym in symbols:
            c = cols[sym]
            for side in sides:
                sig = c["signal_long"][i] if side == "long" else c["signal_short"][i]
                if not sig:
                    continue
                if sym in positions or sym in pending:
                    continue
                if (paused_day == day) or (halted_day == day):
                    skips["paused"] += 1
                    continue
                if len(positions) + len(pending) >= int(p["max_concurrent"]):
                    skips["slots"] += 1
                    continue
                if in_funding_window(t_close, block_min):
                    skips["funding_window"] += 1
                    continue
                f_ts, f_rate = fund[sym][1], fund[sym][2]
                k = int(np.searchsorted(f_ts, t_close, side="right")) - 1
                rate = float(f_rate[k]) if k >= 0 else None
                if funding_blocks(side, rate, float(p["funding_max_against"])):
                    skips["funding_against"] += 1
                    continue
                atr = float(c["atr"][i])
                if not np.isfinite(atr) or atr <= 0:
                    skips["invalid_atr"] += 1
                    continue
                tick = TICKS[sym]
                limit = _round_tick(float(c["close"][i]), tick)
                dist = float(p["stop_atr_mult"]) * atr
                if side == "long":
                    stop = _round_tick(limit - dist, tick)
                    risk_px = limit - stop
                    tp = _round_tick(limit + float(p["tp_r_multiple"]) * risk_px, tick)
                else:
                    stop = _round_tick(limit + dist, tick)
                    risk_px = stop - limit
                    tp = _round_tick(limit - float(p["tp_r_multiple"]) * risk_px, tick)
                qty = _floor_step(risk / risk_px, SIZE_STEPS[sym])
                if qty <= 0:
                    skips["qty_below_min"] += 1
                    continue
                if qty * limit > max_notional:
                    skips["size_cap"] += 1
                    continue
                pending[sym] = Order(sym, side, i, limit, stop, tp, qty, i + ttl, str(c["regime"][i]),
                                     float(c["adx"][i]))
                break

    tdf = pd.DataFrame(trades)
    days = pd.RangeIndex(start_ms // DAY_MS, max(start_ms // DAY_MS + 1, end_ms // DAY_MS))
    dser = pd.Series(daily, dtype=float).reindex(days, fill_value=0.0)
    return SimResult(tdf, events, skips, dser, start_ms, end_ms, p)


def metrics(res: SimResult, capital: float | None = None) -> dict[str, Any]:
    t = res.trades
    capital = float(capital or res.params.get("margin_budget", 1500.0))
    risk = float(res.params.get("risk_per_trade_usdt", 15.0))
    out: dict[str, Any] = {
        "trades": int(len(t)),
        "window_start": pd.Timestamp(res.start_ms, unit="ms", tz="UTC").date().isoformat(),
        "window_end": pd.Timestamp(res.end_ms, unit="ms", tz="UTC").date().isoformat(),
        "events": res.events,
        "skips": res.skips,
    }
    if len(t) == 0:
        out.update({"verdict_allowed": False})
        return out
    wins = t[t["net_pnl"] > 0]
    losses = t[t["net_pnl"] <= 0]
    gp = float(wins["net_pnl"].sum())
    gl = float(-losses["net_pnl"].sum())
    cum = t.sort_values("exit_ts")["net_pnl"].cumsum()
    peak = np.maximum.accumulate(np.concatenate([[0.0], cum.to_numpy()]))
    dd = float((peak[1:] - cum.to_numpy()).max()) if len(cum) else 0.0
    d = res.daily_pnl / capital
    sharpe = float(d.mean() / d.std(ddof=1) * math.sqrt(365)) if d.std(ddof=1) > 0 else float("nan")
    out.update({
        "win_rate": float(len(wins) / len(t)),
        "avg_r_gross": float(t["r_gross"].mean()),
        "net_expectancy_r": float(t["r_net"].mean()),
        "avg_win_r": float(wins["r_net"].mean()) if len(wins) else 0.0,
        "avg_loss_r": float(losses["r_net"].mean()) if len(losses) else 0.0,
        "profit_factor": float(gp / gl) if gl > 0 else float("inf"),
        "net_pnl_usdt": float(t["net_pnl"].sum()),
        "gross_pnl_usdt": float(t["gross_pnl"].sum()),
        "fees_usdt": float(t["fees"].sum()),
        "slippage_usdt": float(t["slippage"].sum()),
        "funding_usdt": float(t["funding"].sum()),
        "max_dd_usdt": dd,
        "max_dd_r": dd / risk,
        "max_dd_pct_of_capital": dd / capital * 100.0,
        "sharpe_daily_ann": sharpe,
        "return_pct_of_capital": float(t["net_pnl"].sum()) / capital * 100.0,
        "exit_reasons": t["exit_reason"].value_counts().to_dict(),
        "by_symbol": {s: {"trades": int(len(g)), "net_expectancy_r": float(g["r_net"].mean())}
                      for s, g in t.groupby("symbol")},
        "avg_hold_hours": float(t["hold_hours"].mean()),
        "avg_notional_usdt": float(t["notional"].mean()),
        "verdict_allowed": bool(len(t) >= 30),
    })
    return out
