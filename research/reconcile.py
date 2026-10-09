"""Reconcile the offline engine against the real Nautilus replay (src/strategy.py) on the same bars/window."""
import json, subprocess, sys
from dataclasses import replace
import pandas as pd
from engine import *

V1 = replace(Config(), enable_trend=False, enable_mr=False, enable_break=True, adx_trend_min=30.0, margin_cap_usdt=500.0)
raw = load(V1.symbols); prep = prepare(raw, V1); idx = prep["BTCUSDT"].index
i0 = 0; i1 = len(idx)
ts_ms = (idx.astype("int64") // 1_000_000).to_numpy()
out = {}
for name, opts in {
    "engine_conservative_1x_ex_funding": dict(funding=0.0),
    "engine_nautilus_like_ex_funding": dict(slip=0, funding=0, tp_first=True, tp_in_fill_bar=True, tp_maker=True),
}.items():
    tr, _ = simulate(prep, V1, i0, i1, m=1.0, opts=opts); d = metrics(tr, int(ts_ms[i0]), int(ts_ms[-1]))
    out[name] = dict(trades=d["trades"], net_pnl=round(d["net_pnl"], 2), pf=round(d["pf"], 3), net_expectancy_r=round(d["net_expectancy_r"], 3))
p = subprocess.run([sys.executable, "nautilus_local.py", "2024-03-04", "2026-10-10"], capture_output=True, text=True)
for line in p.stdout.splitlines():
    if line.startswith("net pnl (nautilus") or line.startswith("positions"):
        out.setdefault("nautilus_replay_raw", []).append(line)
json.dump(out, open("out/reconcile.json", "w"), indent=1)
print(json.dumps(out, indent=1))
