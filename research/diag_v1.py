"""Post-hoc in-sample diagnostics for the frozen v1 candidate (B@30). NOT out-of-sample."""
import json
from dataclasses import replace
import numpy as np, pandas as pd
from engine import *

V1 = replace(Config(), enable_trend=False, enable_mr=False, enable_break=True, adx_trend_min=30.0)
raw = load(V1.symbols); prep = prepare(raw, V1)
idx = prep["BTCUSDT"].index; ts_ms = (idx.astype("int64")//1_000_000).to_numpy()
i0 = int(idx.searchsorted(pd.Timestamp("2024-04-10", tz="UTC"))); i1 = len(idx)
out = {"candidate": "v1 = breakout-continuation (module B), adx_trend_min=30, no HTF filter, trend/MR modules off"}
for m in (0.0, 1.0, 2.0):
    tr, ev = simulate(prep, V1, i0, i1, m=m)
    d = metrics(tr, int(ts_ms[i0]), int(ts_ms[-1])); r = np.array([t.r for t in tr])
    d["net_expectancy_r_ci95"] = boot_ci(r); out[f"all_{m}x"] = d
tr, ev = simulate(prep, V1, i0, i1, m=1.0)
df = pd.DataFrame([dict(sym=t.symbol, exit=pd.Timestamp(t.exit_ts, unit="ms", tz="UTC"), net=t.net, r=t.r, reason=t.reason, fee=t.fee, funding=t.funding,
                        notional=t.qty*t.fill, risk=t.risk) for t in tr])
df["q"] = df["exit"].dt.to_period("Q").astype(str)
out["by_quarter"] = {q: dict(n=len(g), exp_r=float(g.r.mean()), pf=float(g.net[g.net>0].sum()/max(-g.net[g.net<=0].sum(),1e-9))) for q, g in df.groupby("q")}
mid = idx[(i0 + i1)//2]
out["half_split"] = {"split_at": str(mid), "first": dict(n=int((df.exit<mid).sum()), exp_r=float(df[df.exit<mid].r.mean())), "second": dict(n=int((df.exit>=mid).sum()), exp_r=float(df[df.exit>=mid].r.mean()))}
out["by_symbol"] = {s: dict(n=len(g), exp_r=float(g.r.mean()), net=float(g.net.sum())) for s, g in df.groupby("sym")}
out["by_exit"] = {s: dict(n=len(g), exp_r=float(g.r.mean())) for s, g in df.groupby("reason")}
out["notional"] = dict(p50=float(df.notional.median()), p95=float(df.notional.quantile(.95)), p99=float(df.notional.quantile(.99)), max=float(df.notional.max()),
                       margin_at_5x_p99=float(df.notional.quantile(.99)/5), margin_at_5x_max=float(df.notional.max()/5))
out["cost_per_trade_r"] = dict(fees=float((df.fee/df.risk).mean()), funding=float((df.funding/df.risk).mean()))
# null: random entry times, same count rate, same exits/costs
sig_cnt = sum(int(prep[s]["sig_break"].iloc[i0:i1].sum()) for s in V1.symbols)
p = sig_cnt / ((i1 - i0) * len(V1.symbols))
nulls = []
for seed in range(400):
    rng = np.random.default_rng(seed)
    ov = {s: dict(trend=(rng.random(len(idx)) < p) & prep[s]["valid"].to_numpy(), mr=np.zeros(len(idx), bool)) for s in V1.symbols}
    t2, _ = simulate(prep, replace(V1, enable_trend=True), i0, i1, m=1.0, sig_override=ov)
    if t2: nulls.append(float(np.mean([t.r for t in t2])))
obs = out["all_1.0x"]["net_expectancy_r"]
out["null_random_entry"] = dict(n=len(nulls), mean=float(np.mean(nulls)), p05=float(np.percentile(nulls,5)), p95=float(np.percentile(nulls,95)),
                                observed=obs, pct_null_below=float(np.mean(np.array(nulls) < obs)))
# kill-switch start-date analysis
seq = list(df.net)
def hit(w):
    hs=n=0
    for s in range(len(seq)-10):
        sub=seq[s:s+w]; n+=1; hs += bool((np.cumsum(sub) <= -40).any())
    return dict(starts=n, hit=hs, frac=hs/n)
out["kill_switch_minus40"] = dict(first_30_trades=hit(30), first_100_trades=hit(100))
span = (ts_ms[-1]-ts_ms[i0])/(86400000)
out["frequency"] = dict(days=float(span), trades_per_month=len(tr)/span*30.4, months_to_30_trades=30/(len(tr)/span*30.4))
# longest losing streak
mx=c=0
for n in seq:
    c = c+1 if n<0 else 0; mx=max(mx,c)
out["max_losing_streak"]=mx
out["events"] = {k: sum(1 for e in ev if e["ev"]==k) for k in ("halt_5_losses","cum_pnl_le_-40")}
from collections import Counter
out["skips"] = dict(Counter(e.get("why") for e in ev if e["ev"]=="skip"))
out["cancels"] = dict(Counter(e.get("why") for e in ev if e["ev"]=="entry_cancelled"))
json.dump(out, open("out/diag_v1.json","w"), indent=1, default=float)
print(json.dumps(out, indent=1, default=float))
