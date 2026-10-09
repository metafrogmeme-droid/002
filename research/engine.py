"""Offline research engine: bar-level portfolio simulator for the sleeve-A playbook.

Uses the exact signal/sizing code shipped in the package (src/rules.py) so research and live logic cannot drift.
Execution model (deliberately conservative where intrabar order is unknowable):
  * decision at bar close i; long limit at floor_tick(close_i), valid for bars i+1..i+4, cancelled earlier if a bar
    overlaps a +-15min funding-settlement window;
  * fill only if low < limit (strict trade-through); fill price = limit + slip_ticks*tick;
  * stop (attached) is live from the fill bar; TP only from the bar after the fill; stop wins when both touch in a bar;
  * stop/TP/time-stop exits are market-style: taker fee and slip_ticks adverse; gaps fill at the open;
  * time stop exits at the open of bar fill_idx+N;
  * funding: modelled constant rate (Bitget history API only serves ~90 days) x notional per 00/08/16 UTC settlement held;
  * cost multiplier m scales fee, slippage and funding (0 = frictionless, 1 = live spec, 2 = stress).
"""
from __future__ import annotations

import math
import sys
from dataclasses import dataclass, replace
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / "playbooks" / "crypto-perp-regime-long" / "src"))
import rules  # noqa: E402
from rules import Config, HOUR_MS  # noqa: E402

DATA = ROOT / "data"
SPEC = {  # live contract spec pulled 2026-10-09 (out/live_spec.json)
    "BTCUSDT": dict(tick=0.1, step=0.0001, min_qty=0.0001),
    "ETHUSDT": dict(tick=0.01, step=0.01, min_qty=0.01),
    "SOLUSDT": dict(tick=0.001, step=0.1, min_qty=0.1),
}
MAKER = 0.0002
TAKER = 0.0006
MIN_NOTIONAL = 5.0


def load(symbols) -> dict:
    out = {}
    for s in symbols:
        d = pd.read_csv(DATA / f"{s}_1H.csv")
        d.index = pd.to_datetime(d["ts"], unit="ms", utc=True)
        d = d.rename(columns={"base_vol": "volume"})[["open", "high", "low", "close", "volume"]].astype(float)
        out[s] = d
    return out


def prepare(raw: dict, cfg: Config) -> dict:
    prep = {}
    for s, d in raw.items():
        ind = rules.compute_indicators(d, cfg)
        prep[s] = rules.compute_signals(ind, cfg)
    return prep


@dataclass
class Trade:
    symbol: str
    module: str
    decision_ts: int
    fill_ts: int
    exit_ts: int
    limit: float
    fill: float
    exit: float
    qty: float
    risk: float
    reason: str
    gross: float
    fee: float
    slip: float
    funding: float
    net: float

    @property
    def r(self) -> float:
        return self.net / self.risk if self.risk else float("nan")


def simulate(prep: dict, cfg: Config, i0: int, i1: int, m: float = 1.0, sig_override: dict | None = None, opts: dict | None = None):
    """Run the portfolio over bar indices [i0, i1). Returns (trades, events)."""
    o_ = dict(slip=m, fee=m, funding=m, tp_first=False, tp_in_fill_bar=False, tp_maker=False)
    o_.update(opts or {})
    syms = list(cfg.symbols)
    idx = prep[syms[0]].index
    T = (idx.astype("int64") // 1_000_000).to_numpy()
    A = {}
    for s in syms:
        d = prep[s]
        A[s] = dict(
            o=d["open"].to_numpy(), h=d["high"].to_numpy(), l=d["low"].to_numpy(), c=d["close"].to_numpy(),
            atr=d["atr"].to_numpy(), qv=d["quote_vol_24h"].to_numpy(),
            st=(sig_override[s]["trend"] if sig_override else d["sig_trend"].to_numpy()),
            sm=(sig_override[s]["mr"] if sig_override else d["sig_mr"].to_numpy()),
            sb=(sig_override[s].get("break", np.zeros(len(d), bool)) if sig_override else d["sig_break"].to_numpy()),
        )
    trades, events = [], []
    pending = None
    pos = None
    day_pnl: dict[int, float] = {}
    total = 0.0
    streak = 0
    halted_flags = {"stop40": False}
    for i in range(i0, i1):
        ts = int(T[i])
        # --- pending order
        if pending is not None:
            if i > pending["last"] or rules.blackout_for_order_bar(ts, cfg):
                events.append(dict(ts=ts, ev="entry_cancelled", symbol=pending["sym"], why="expired" if i > pending["last"] else "funding_window"))
                pending = None
            else:
                a = A[pending["sym"]]
                if a["l"][i] < pending["limit"]:
                    sp = SPEC[pending["sym"]]
                    fill = pending["limit"] + o_["slip"] * sp["tick"]
                    pos = dict(pending, fill=fill, fidx=i, fill_ts=ts)
                    pending = None
        # --- open position exits
        if pos is not None:
            a = A[pos["sym"]]
            sp = SPEC[pos["sym"]]
            exit_px = None
            why = None
            fidx = pos["fidx"]
            if i >= fidx + pos["hold"]:
                exit_px, why = a["o"][i], "time_stop"
                exit_ts = ts
            else:
                tp_ok = (i > fidx or o_["tp_in_fill_bar"]) and a["h"][i] >= pos["tp"]
                st_ok = a["l"][i] <= pos["stop"]
                if tp_ok and (not st_ok or o_["tp_first"]):
                    exit_px, why = (a["o"][i] if a["o"][i] >= pos["tp"] else pos["tp"]), "tp"
                    exit_ts = ts + HOUR_MS
                elif st_ok:
                    exit_px, why = (a["o"][i] if a["o"][i] <= pos["stop"] else pos["stop"]), "stop"
                    exit_ts = ts + HOUR_MS
            if exit_px is not None:
                exit_fill = exit_px - o_["slip"] * sp["tick"]
                gross = pos["qty"] * (exit_px - pos["limit"])
                slip = pos["qty"] * o_["slip"] * sp["tick"] * 2
                exit_rate = MAKER if (why == "tp" and o_["tp_maker"]) else TAKER
                fee = o_["fee"] * (MAKER * pos["qty"] * pos["fill"] + exit_rate * pos["qty"] * exit_fill)
                n_set = rules.settlements_between(pos["fill_ts"], exit_ts)
                funding = o_["funding"] * cfg.funding_rate_assumed * pos["qty"] * pos["fill"] * n_set
                net = pos["qty"] * (exit_fill - pos["fill"]) - fee - funding
                tr = Trade(pos["sym"], pos["module"], pos["dec_ts"], pos["fill_ts"], exit_ts, pos["limit"], pos["fill"], exit_fill,
                           pos["qty"], pos["risk"], why, gross, fee, slip, funding, net)
                trades.append(tr)
                day = exit_ts // (24 * HOUR_MS)
                day_pnl[day] = day_pnl.get(day, 0.0) + net
                total += net
                streak = streak + 1 if net < 0 else 0
                if streak == cfg.max_consecutive_losses:
                    events.append(dict(ts=exit_ts, ev="halt_5_losses"))
                if total <= -cfg.stop_playbook_usdt and not halted_flags["stop40"]:
                    halted_flags["stop40"] = True
                    events.append(dict(ts=exit_ts, ev="cum_pnl_le_-40", total=total))
                pos = None
        # --- decision at close of bar i
        if pending is None and pos is None and i + 1 < i1:
            day = (ts + HOUR_MS) // (24 * HOUR_MS)
            if day_pnl.get(day, 0.0) <= -cfg.daily_pause_usdt:
                continue
            for s in syms:
                a = A[s]
                module = "trend" if a["st"][i] else "break" if a["sb"][i] else "mr" if a["sm"][i] else None
                if module is None:
                    continue
                if not (a["qv"][i] >= cfg.min_volume_24h_usdt):
                    continue
                sp = SPEC[s]
                plan = rules.build_plan(
                    module=module, close=a["c"][i], atr=a["atr"][i], decision_ts_ms=ts + HOUR_MS, cfg=cfg,
                    tick=sp["tick"], size_step=sp["step"], min_qty=sp["min_qty"], min_notional=MIN_NOTIONAL,
                    funding_rate=cfg.funding_rate_assumed,
                )
                if not plan.ok:
                    events.append(dict(ts=ts, ev="skip", symbol=s, why=plan.reason))
                    continue
                # order resting from next bar; skip if first bar overlaps a funding window
                if rules.blackout_for_order_bar(T[i] + HOUR_MS, cfg):
                    events.append(dict(ts=ts, ev="skip", symbol=s, why=rules.REASON["FUNDING_WINDOW"]))
                    continue
                pending = dict(sym=s, module=module, limit=plan.limit_price, stop=plan.stop_price, tp=plan.tp_price, qty=plan.qty,
                               risk=plan.risk_usdt, hold=plan.time_stop_hours, last=i + cfg.entry_cancel_hours, dec_ts=ts + HOUR_MS)
                break
    return trades, events


def metrics(trades: list[Trade], i0_ts: int, i1_ts: int, margin_cap: float = 1000.0) -> dict:
    n = len(trades)
    if n == 0:
        return dict(trades=0)
    net = np.array([t.net for t in trades])
    r = np.array([t.r for t in trades])
    wins = net > 0
    gp, gl = net[wins].sum(), -net[~wins].sum()
    eq = np.cumsum(net)
    peak = np.maximum.accumulate(np.r_[0.0, eq])[1:]
    dd = float((peak - eq).max())
    days = np.arange(i0_ts // (24 * HOUR_MS), i1_ts // (24 * HOUR_MS) + 1)
    daily = pd.Series(0.0, index=days)
    for t in trades:
        daily[t.exit_ts // (24 * HOUR_MS)] = daily.get(t.exit_ts // (24 * HOUR_MS), 0.0) + t.net
    sd = daily.std(ddof=1)
    sharpe = float(daily.mean() / sd * math.sqrt(365)) if sd > 0 else float("nan")
    gross_r = np.array([t.gross / t.risk for t in trades])
    return dict(
        trades=n, win_rate=float(wins.mean()), avg_win_r=float(r[wins].mean()) if wins.any() else float("nan"),
        avg_loss_r=float(r[~wins].mean()) if (~wins).any() else float("nan"),
        gross_expectancy_r=float(gross_r.mean()), net_expectancy_r=float(r.mean()),
        pf=float(gp / gl) if gl > 0 else float("inf"), net_pnl=float(net.sum()), max_dd_usdt=dd, max_dd_r=dd / 15.0,
        sharpe_daily=sharpe, fees=float(sum(t.fee for t in trades)), funding=float(sum(t.funding for t in trades)),
        exits={k: int(sum(1 for t in trades if t.reason == k)) for k in ("stop", "tp", "time_stop")},
        by_module={k: int(sum(1 for t in trades if t.module == k)) for k in ("trend", "break", "mr")},
        by_symbol={k: int(sum(1 for t in trades if t.symbol == k)) for k in ("BTCUSDT", "ETHUSDT", "SOLUSDT")},
    )


def boot_ci(r: np.ndarray, n: int = 5000, seed: int = 7):
    if len(r) < 2:
        return (float("nan"), float("nan"))
    rng = np.random.default_rng(seed)
    means = rng.choice(r, size=(n, len(r)), replace=True).mean(axis=1)
    return float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))
