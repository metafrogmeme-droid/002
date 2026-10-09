import sys
from dataclasses import replace
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import engine
from engine import Config, rules, simulate, SPEC, HOUR_MS

CFG = Config()


def _real(sym="BTCUSDT", n=6000):
    return engine.load([sym])[sym].iloc[:n]


def test_indicators_causal_no_lookahead():
    d = _real()
    full = rules.compute_signals(rules.compute_indicators(d, CFG), CFG)
    for k in (2500, 3333, 4999):
        part = rules.compute_signals(rules.compute_indicators(d.iloc[: k + 1], CFG), CFG)
        for col in ("atr", "adx", "ema_fast", "atr_pct_rank", "rsi", "bb_low", "prior_high"):
            a, b = full[col].iloc[k], part[col].iloc[k]
            assert (np.isnan(a) and np.isnan(b)) or abs(a - b) < 1e-9, (col, k, a, b)
        for col in ("sig_trend", "sig_mr", "sig_break"):
            assert bool(full[col].iloc[k]) == bool(part[col].iloc[k])


def test_atr_matches_independent_wilder():
    d = _real()
    ind = rules.compute_indicators(d, CFG)
    tr = pd.concat([d.high - d.low, (d.high - d.close.shift()).abs(), (d.low - d.close.shift()).abs()], axis=1).max(axis=1)
    ref = tr.ewm(alpha=1 / 14, adjust=False).mean()
    assert abs(ind["atr"].iloc[-1] / ref.iloc[-1] - 1) < 1e-3


def test_plan_risk_and_tp():
    p = rules.build_plan(module="break", close=65000.0, atr=400.0, decision_ts_ms=1_700_000_000_000, cfg=CFG, tick=0.1, size_step=0.0001,
                         min_qty=0.0001, min_notional=5.0, funding_rate=0.0001)
    assert p.ok
    assert p.risk_usdt <= 15.0 and p.risk_usdt > 14.9
    assert abs((p.tp_price - p.limit_price) - 2 * (p.limit_price - p.stop_price)) <= 0.1
    assert abs(p.stop_distance - 600.0) <= 0.1


def test_plan_rejections():
    big = rules.build_plan(module="break", close=65000.0, atr=5.0, decision_ts_ms=0, cfg=CFG, tick=0.1, size_step=0.0001, min_qty=0.0001,
                           min_notional=5.0, funding_rate=0.0001)
    assert not big.ok and big.reason == rules.REASON["SIZE_CAP"]
    fund = rules.build_plan(module="break", close=65000.0, atr=400.0, decision_ts_ms=7 * HOUR_MS, cfg=CFG, tick=0.1, size_step=0.0001,
                            min_qty=0.0001, min_notional=5.0, funding_rate=0.01)
    assert not fund.ok and fund.reason == rules.REASON["FUNDING_COST"]


def test_funding_helpers():
    assert rules.in_funding_window(8 * HOUR_MS + 10 * 60_000, 15)
    assert rules.in_funding_window(8 * HOUR_MS - 14 * 60_000, 15)
    assert not rules.in_funding_window(8 * HOUR_MS + 16 * 60_000, 15)
    assert rules.in_funding_window(24 * HOUR_MS * 5 + 0, 15)
    assert rules.settlements_between(7 * HOUR_MS, 15 * HOUR_MS) == 1
    assert rules.settlements_between(7 * HOUR_MS, 16 * HOUR_MS) == 2
    assert rules.blackout_for_order_bar(7 * HOUR_MS, CFG) and rules.blackout_for_order_bar(8 * HOUR_MS, CFG)
    assert not rules.blackout_for_order_bar(9 * HOUR_MS, CFG) and not rules.blackout_for_order_bar(6 * HOUR_MS, CFG)


def _synthetic(bars):
    """bars: list of (o,h,l,c). Builds a one-symbol prep dict with a single hand-placed trend signal at bar 0."""
    idx = pd.date_range("2025-01-01 01:00", periods=len(bars), freq="1h", tz="UTC")
    d = pd.DataFrame(bars, columns=["open", "high", "low", "close"], index=idx)
    d["volume"] = 1.0
    d["atr"] = 100.0
    d["quote_vol_24h"] = 1e9
    d["sig_trend"] = False
    d["sig_mr"] = False
    d["sig_break"] = False
    d.iloc[0, d.columns.get_loc("sig_trend")] = True
    return {"BTCUSDT": d}


def _cfg1():
    return replace(CFG, symbols=("BTCUSDT",), adx_trend_min=0.0, margin_cap_usdt=1e9)


def test_engine_stop_and_gap_and_costs():
    bars = [(10000, 10000, 10000, 10000), (10000, 10010, 9990, 10000), (9990, 9995, 9800, 9850), (9850, 9860, 9840, 9850)]
    prep = _synthetic(bars)
    tr, _ = simulate(prep, _cfg1(), 0, len(bars), m=1.0)
    assert len(tr) == 1 and tr[0].reason == "stop"
    t = tr[0]
    assert abs(t.limit - 10000.0) < 1e-9 and t.fill > t.limit
    assert t.exit < 9850 + 1e-9  # stop at 9850 filled with 1 tick adverse
    assert t.net < 0
    tr0, _ = simulate(prep, _cfg1(), 0, len(bars), m=0.0)
    assert tr0[0].fee == 0 and abs(tr0[0].r + 1.0) < 0.01  # frictionless stop is -1R


def test_engine_tp_not_in_fill_bar_and_stop_priority():
    # fill bar (idx1) high exceeds TP but TP is only armed from the next bar; next bar touches both -> stop first
    bars = [(10000, 10000, 10000, 10000), (10000, 10400, 9990, 10000), (10000, 10400, 9840, 10000), (10000, 10000, 10000, 10000)]
    tr, _ = simulate(_synthetic(bars), _cfg1(), 0, len(bars), m=0.0)
    assert tr[0].reason == "stop"
    bars2 = [(10000, 10000, 10000, 10000), (10000, 10010, 9990, 10000), (10000, 10400, 9990, 10300), (10300, 10300, 10300, 10300)]
    tr2, _ = simulate(_synthetic(bars2), _cfg1(), 0, len(bars2), m=0.0)
    assert tr2[0].reason == "tp" and abs(tr2[0].r - 2.0) < 0.02


def test_engine_time_stop_and_unfilled_cancel():
    flat = [(10000, 10010, 9990, 10000)] * 14
    bars = [(10000, 10000, 10000, 10000)] + flat
    tr, _ = simulate(_synthetic(bars), _cfg1(), 0, len(bars), m=0.0)
    assert tr and tr[0].reason == "time_stop"
    assert (tr[0].exit_ts - tr[0].fill_ts) == 8 * HOUR_MS
    up = [(10000, 10000, 10000, 10000)] + [(10010, 10050, 10005, 10040)] * 10
    tr2, ev = simulate(_synthetic(up), _cfg1(), 0, len(up), m=0.0)
    assert not tr2 and any(e["ev"] == "entry_cancelled" for e in ev)
