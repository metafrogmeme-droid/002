import time, numpy as np, pandas as pd
from engine import *
cfg = Config()
t=time.time(); raw = load(cfg.symbols); prep = prepare(raw, cfg); print("prep", round(time.time()-t,1),"s")
idx = prep["BTCUSDT"].index
print(idx[0], idx[-1], len(idx))
for s in cfg.symbols:
    d=prep[s]; print(s, "valid from", d.index[d.valid.values.argmax()], "trend sigs", int(d.sig_trend.sum()), "mr sigs", int(d.sig_mr.sum()), "adx>=25 share", round((d.adx>=25).mean(),3), "adx<20 share", round((d.adx<20).mean(),3))
i0 = int(idx.searchsorted(pd.Timestamp("2024-04-10", tz="UTC"))); i1 = int(idx.searchsorted(pd.Timestamp("2025-04-10", tz="UTC")))
t=time.time(); tr, ev = simulate(prep, cfg, i0, i1); print("sim", round(time.time()-t,2),"s", len(tr), "trades in TRAIN window only")
from collections import Counter; print(Counter((e["ev"], e.get("why")) for e in ev))
# sanity: indicator check vs independent calc
d=prep["BTCUSDT"]; print(d[["close","atr","adx","ema_fast","rsi","atr_pct_rank"]].iloc[-3:])
