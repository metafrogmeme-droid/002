"""Anchored walk-forward evaluation + cost sensitivity + null test + kill-switch analysis.

Split (UTC): warm-up 2024-03-04..2024-04-10 (indicator history only);
train anchor 2024-04-10 .. 2025-04-10 (12 months), then six consecutive 3-month OOS folds to 2026-10-09 17:00.
Parameter grid (pre-registered, 7 configs): adx_trend_min in {20,25,30} x module set {T, M, T+M} (M has no tunables).
Selection per fold: max net expectancy R (1x costs) on the anchored train window with >=30 trades, else stay flat.
"""
from __future__ import annotations

import json
from dataclasses import replace

import numpy as np
import pandas as pd

from engine import Config, Trade, boot_ci, load, metrics, prepare, simulate, HOUR_MS

import sys

ROUND = sys.argv[1] if len(sys.argv) > 1 else "r1"
MIN_TRAIN_EXP = 0.0 if ROUND == "r1" else 0.05
BASE = Config()
raw = load(BASE.symbols)
CFGS = {}
if ROUND == "r1":
    for adx in (20, 25, 30):
        CFGS[f"T@{adx}"] = replace(BASE, adx_trend_min=float(adx), enable_trend=True, enable_mr=False)
        CFGS[f"T@{adx}+M"] = replace(BASE, adx_trend_min=float(adx), enable_trend=True, enable_mr=True)
    CFGS["M"] = replace(BASE, enable_trend=False, enable_mr=True)
else:
    sets = {"T": (1, 0, 0), "B": (0, 1, 0), "T+B": (1, 1, 0), "T+M": (1, 0, 1), "T+B+M": (1, 1, 1)}
    for htf in (False, True):
        tag = "|HTF" if htf else ""
        for nm, (t, b, m_) in sets.items():
            for adx in (20, 25, 30):
                CFGS[f"{nm}@{adx}{tag}"] = replace(BASE, adx_trend_min=float(adx), enable_trend=bool(t), enable_break=bool(b),
                                                    enable_mr=bool(m_), htf_filter=htf)
        CFGS[f"M{tag}"] = replace(BASE, enable_trend=False, enable_mr=True, htf_filter=htf)

PREP = {}
for name, cfg in CFGS.items():
    key = (cfg.adx_trend_min, cfg.enable_trend, cfg.enable_mr)
    PREP[name] = prepare(raw, cfg)

idx = PREP["M"][BASE.symbols[0]].index
ts_ms = (idx.astype("int64") // 1_000_000).to_numpy()


def ix(date: str) -> int:
    return int(idx.searchsorted(pd.Timestamp(date, tz="UTC")))


BOUNDS = ["2024-04-10", "2025-04-10", "2025-07-10", "2025-10-10", "2026-01-10", "2026-04-10", "2026-07-10"]
B = [ix(b) for b in BOUNDS] + [len(idx)]
TRAIN0 = B[0]


def run(name, i0, i1, m=1.0):
    return simulate(PREP[name], CFGS[name], i0, i1, m=m)[0]


def summarize(trs, i0, i1):
    d = metrics(trs, int(ts_ms[i0]), int(ts_ms[min(i1, len(ts_ms)) - 1]))
    if d.get("trades"):
        r = np.array([t.r for t in trs])
        d["net_expectancy_r_ci95"] = boot_ci(r)
    return d


report = {"round": ROUND, "min_train_expectancy_r": MIN_TRAIN_EXP, "n_configs": len(CFGS), "split": dict(bounds=BOUNDS + [str(idx[-1])], grid=list(CFGS)), "folds": []}
oos_trades = {1.0: [], 0.0: [], 2.0: []}
fold_cfgs = []
for k in range(1, len(B) - 1):
    train_i0, train_i1 = TRAIN0, B[k]
    test_i0, test_i1 = B[k], B[k + 1]
    cand = {}
    for name in CFGS:
        trs = run(name, train_i0, train_i1)
        if len(trs) >= 30:
            cand[name] = float(np.mean([t.r for t in trs]))
    best = max(cand, key=cand.get) if cand else None
    chosen = best if (best and cand[best] > MIN_TRAIN_EXP) else None
    fold = dict(fold=k, train=[str(idx[train_i0]), str(idx[train_i1])], test=[str(idx[test_i0]), str(idx[min(test_i1, len(idx) - 1)])],
                train_expectancy_r={k2: round(v, 4) for k2, v in cand.items()}, chosen=chosen)
    fold_cfgs.append(chosen)
    if chosen:
        for m in (0.0, 1.0, 2.0):
            trs = run(chosen, test_i0, test_i1, m)
            oos_trades[m] += trs
            if m == 1.0:
                fold["oos"] = summarize(trs, test_i0, test_i1)
    else:
        fold["oos"] = dict(trades=0, note="flat (no config with >=30 train trades and positive net expectancy)")
    report["folds"].append(fold)

OOS0, OOS1 = B[1], len(idx)
stitched = {}
for m, trs in oos_trades.items():
    trs.sort(key=lambda t: t.exit_ts)
    stitched[str(m)] = summarize(trs, OOS0, OOS1)
report["stitched_oos"] = stitched

# ---- final fit on all data -> v1 candidate (in-sample, flagged)
cand_all = {}
for name in CFGS:
    trs = run(name, TRAIN0, len(idx))
    cand_all[name] = dict(summarize(trs, TRAIN0, len(idx)))
report["final_fit_in_sample"] = cand_all

# ---- per-symbol / per-module breakdown of stitched OOS (1x)
def breakdown(trs, key):
    out = {}
    for kk in sorted({getattr(t, key) for t in trs}):
        sub = [t for t in trs if getattr(t, key) == kk]
        net = np.array([t.net for t in sub]); r = np.array([t.r for t in sub])
        out[kk] = dict(trades=len(sub), net_expectancy_r=float(r.mean()), net_pnl=float(net.sum()),
                       win_rate=float((net > 0).mean()))
    return out

t1 = oos_trades[1.0]
report["stitched_oos_breakdown"] = dict(by_symbol=breakdown(t1, "symbol"), by_module=breakdown(t1, "module"), by_exit=breakdown(t1, "reason"))

# ---- null test: same exits/costs/sizing, random entry timing (stitched OOS folds)
rng = np.random.default_rng(11)
null_exp = []
if t1:
    for seed in range(300):
        rng = np.random.default_rng(seed)
        allr = []
        for k, chosen in enumerate(fold_cfgs, start=1):
            if not chosen:
                continue
            i0, i1 = B[k], B[k + 1]
            cfg = CFGS[chosen]
            prep = PREP[chosen]
            n_sig = sum(int((prep[s]["sig_trend"] | prep[s]["sig_mr"] | prep[s]["sig_break"]).iloc[i0:i1].sum()) for s in cfg.symbols)
            p = n_sig / ((i1 - i0) * len(cfg.symbols))
            ov = {}
            for s in cfg.symbols:
                v = prep[s]["valid"].to_numpy()
                ov[s] = dict(trend=(rng.random(len(idx)) < p) & v, mr=np.zeros(len(idx), bool))
            trs, _ = simulate(prep, replace(cfg, enable_trend=True), i0, i1, m=1.0, sig_override=ov)
            allr += [t.r for t in trs]
        if allr:
            null_exp.append(float(np.mean(allr)))
    obs = stitched["1.0"].get("net_expectancy_r")
    report["null_test"] = dict(
        n_sims=len(null_exp), null_mean=float(np.mean(null_exp)), null_p05=float(np.percentile(null_exp, 5)),
        null_p95=float(np.percentile(null_exp, 95)), observed=obs,
        pct_null_below_observed=float(np.mean(np.array(null_exp) < obs)) if obs is not None else None,
    )

# ---- kill-switch analysis on stitched OOS sequence (1x): would -40 cum stop have fired within first 30 / 100 trades?
seq = [t.net for t in t1]
def stop_hit(window):
    hits = 0; starts = 0
    for s in range(0, max(len(seq) - 1, 0)):
        sub = seq[s : s + window]
        if len(sub) < min(window, 10):
            continue
        starts += 1
        c = np.cumsum(sub)
        if (c <= -40).any():
            hits += 1
    return dict(starts=starts, hit=hits, frac=(hits / starts if starts else None))
report["kill_switch_minus40"] = dict(within_30_trades=stop_hit(30), within_100_trades=stop_hit(100))
report["streaks"] = dict(
    max_consecutive_losses_stitched=int(max((len(list(g)) for k2, g in __import__("itertools").groupby([n < 0 for n in seq]) if k2), default=0)),
)
if t1:
    span_days = (ts_ms[-1] - ts_ms[OOS0]) / (24 * HOUR_MS)
    report["frequency"] = dict(oos_days=float(span_days), trades_per_month=len(t1) / span_days * 30.4,
                               days_to_30_trades=30 / (len(t1) / span_days) if len(t1) else None)

# save trades
rows = [dict(symbol=t.symbol, module=t.module, dec=pd.Timestamp(t.decision_ts, unit="ms", tz="UTC").isoformat(),
             fill=pd.Timestamp(t.fill_ts, unit="ms", tz="UTC").isoformat(), exit=pd.Timestamp(t.exit_ts, unit="ms", tz="UTC").isoformat(),
             limit=t.limit, fill_px=t.fill, exit_px=t.exit, qty=t.qty, risk=t.risk, reason=t.reason, gross=t.gross, fee=t.fee,
             funding=t.funding, net=t.net, r=t.r) for t in t1]
pd.DataFrame(rows).to_csv(f"out/oos_trades_1x_{ROUND}.csv", index=False)
json.dump(report, open(f"out/wfa_report_{ROUND}.json", "w"), indent=1, default=float)
print(json.dumps(report, indent=1, default=float))
