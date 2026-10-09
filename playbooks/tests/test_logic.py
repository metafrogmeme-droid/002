"""LOGIC TESTS ONLY (synthetic inputs). These verify code correctness, not
strategy performance. Nothing here is a backtest or evidence of edge.

Run with either:  python3 playbooks/tests/test_logic.py   or   pytest playbooks/tests
"""
import ast
import hashlib
import math
import random
import sys
from decimal import Decimal
from pathlib import Path

import yaml

PKG = Path(__file__).resolve().parents[1] / "bitget-usdtm-trend-v1"
sys.path.insert(0, str(PKG / "src"))

import logic  # noqa: E402
from logic import ReasonCode as RC  # noqa: E402

H = logic.HOUR_MS
P = logic.load_params({})


def ms(text: str) -> int:
    return logic.parse_iso_ms(text)


# --- indicators -----------------------------------------------------------


def _ref_wilder(highs, lows, closes, n=14):
    """Independent array-style reference for Wilder ATR / +DI / -DI / ADX."""
    tr, pdm, mdm = [], [], []
    for i in range(1, len(closes)):
        tr.append(max(highs[i] - lows[i], abs(highs[i] - closes[i - 1]), abs(lows[i] - closes[i - 1])))
        up, dn = highs[i] - highs[i - 1], lows[i - 1] - lows[i]
        pdm.append(up if up > dn and up > 0 else 0.0)
        mdm.append(dn if dn > up and dn > 0 else 0.0)
    atr = [None] * len(tr)
    spdm, smdm, str_ = sum(pdm[:n]), sum(mdm[:n]), sum(tr[:n])
    pdi, mdi, dx = [None] * len(tr), [None] * len(tr), [None] * len(tr)
    for i in range(n - 1, len(tr)):
        if i > n - 1:
            str_ = str_ - str_ / n + tr[i]
            spdm = spdm - spdm / n + pdm[i]
            smdm = smdm - smdm / n + mdm[i]
        atr[i] = str_ / n
        pdi[i], mdi[i] = 100 * spdm / str_, 100 * smdm / str_
        dx[i] = 100 * abs(pdi[i] - mdi[i]) / (pdi[i] + mdi[i])
    adx = [None] * len(tr)
    first = n - 1
    adx[first + n - 1] = sum(dx[first:first + n]) / n
    for i in range(first + n, len(tr)):
        adx[i] = (adx[i - 1] * (n - 1) + dx[i]) / n
    return atr, pdi, mdi, adx


def _random_bars(n, seed=7):
    rnd = random.Random(seed)
    px, out = 100.0, []
    for _ in range(n):
        o = px
        px *= 1 + rnd.gauss(0.0003, 0.01)
        hi, lo = max(o, px) * (1 + abs(rnd.gauss(0, 0.003))), min(o, px) * (1 - abs(rnd.gauss(0, 0.003)))
        out.append((hi, lo, px, 1000 + rnd.random() * 800))
    return out


def test_wilder_matches_independent_reference():
    bars = _random_bars(300)
    eng = logic.IndicatorEngine(atr_pct_min_history=50)
    feats = [eng.update(*b) for b in bars]
    atr, pdi, mdi, adx = _ref_wilder([b[0] for b in bars], [b[1] for b in bars], [b[2] for b in bars])
    checked = 0
    for i, f in enumerate(feats[1:]):
        if atr[i] is not None:
            assert math.isclose(f.atr, atr[i], rel_tol=1e-9)
            assert math.isclose(f.plus_di, pdi[i], rel_tol=1e-9)
            assert math.isclose(f.minus_di, mdi[i], rel_tol=1e-9)
            checked += 1
        if adx[i] is not None:
            assert math.isclose(f.adx, adx[i], rel_tol=1e-9)
            checked += 1
    assert checked > 400


def test_ema_seed_and_recursion():
    eng = logic.IndicatorEngine(ema_fast=3, ema_slow=5, atr_pct_min_history=5)
    closes = [10, 11, 12, 13, 14, 15, 16]
    feats = [eng.update(c + 0.5, c - 0.5, c, 100) for c in closes]
    assert feats[1].ema_fast is None and math.isclose(feats[2].ema_fast, 11.0)
    assert math.isclose(feats[3].ema_fast, 0.5 * 13 + 0.5 * 11.0)
    assert math.isclose(feats[4].ema_slow, 12.0)


def test_rolling_rank_window_and_percent():
    rr = logic.RollingRank(maxlen=4)
    assert rr.rank_pct(1.0) is None
    for v in (1, 2, 3, 4):
        rr.add(v)
    assert rr.rank_pct(2.5) == 50.0 and rr.rank_pct(4) == 100.0 and rr.rank_pct(0.5) == 0.0
    rr.add(10)  # evicts 1
    assert len(rr) == 4 and rr.rank_pct(2.5) == 25.0


def test_trigger_is_state_transition_not_level():
    eng = logic.IndicatorEngine(ema_fast=3, ema_slow=5, adx_period=3, atr_period=3, atr_pct_min_history=3, volume_lookback=3)
    seq = [(101, 99, 100, 10)] * 12 + [(102 + i, 100 + i, 101 + i, 30) for i in range(8)]
    trig = [eng.update(*b).trigger for b in seq]
    assert sum(trig) <= 2 and not all(trig)


# --- signal / regime ------------------------------------------------------


def _feat(**kw):
    base = dict(close=100.0, ema_fast=99.0, ema_slow=95.0, atr=1.0, atr_pct=0.01, atr_pct_rank=50.0, adx=30.0,
                plus_di=30.0, minus_di=10.0, vol_ratio=2.0, structure=True, structure_prev=False, ready=True)
    base.update(kw)
    return logic.Features(**base)


def test_signal_gate_order_and_reasons():
    assert logic.evaluate_signal(_feat(), P) == RC.SIGNAL_LONG_ENTRY
    assert logic.evaluate_signal(_feat(ready=False), P) == RC.REGIME_WARMUP
    assert logic.evaluate_signal(_feat(structure_prev=True), P) == RC.NO_SIGNAL
    assert logic.evaluate_signal(_feat(adx=24.99), P) == RC.REGIME_ADX_LOW
    assert logic.evaluate_signal(_feat(atr_pct_rank=19.9), P) == RC.REGIME_ATR_PCT_LOW
    assert logic.evaluate_signal(_feat(atr_pct_rank=90.1), P) == RC.REGIME_ATR_PCT_HIGH
    assert logic.evaluate_signal(_feat(vol_ratio=1.49), P) == RC.SKIP_VOLUME_NOT_CONFIRMED
    assert logic.evaluate_signal(_feat(vol_ratio=1.5, adx=25.0, atr_pct_rank=20.0), P) == RC.SIGNAL_LONG_ENTRY


def test_funding_gate_direction():
    assert logic.funding_adverse(0.00031, "long", 0.0003)
    assert not logic.funding_adverse(0.0003, "long", 0.0003)
    assert not logic.funding_adverse(-0.001, "long", 0.0003)  # negative funding pays longs
    assert logic.funding_adverse(-0.00031, "short", 0.0003)


# --- time helpers ---------------------------------------------------------


def test_funding_window_bounds():
    t8 = ms("2025-03-01T08:00:00Z")
    assert logic.in_funding_window(t8, 15)
    assert logic.in_funding_window(t8 - 15 * 60_000, 15) and logic.in_funding_window(t8 + 15 * 60_000, 15)
    assert not logic.in_funding_window(t8 - 15 * 60_000 - 1, 15)
    assert logic.in_funding_window(ms("2025-03-01T00:00:00Z"), 15)
    assert logic.in_funding_window(ms("2025-03-01T23:50:00Z"), 15)  # window of next-day 00:00
    assert not logic.in_funding_window(ms("2025-03-01T12:00:00Z"), 15)


def test_next_window_and_entry_expiry_shortening():
    d = ms("2025-03-01T14:00:00Z")
    assert logic.next_window_start_ms(d, 15) == ms("2025-03-01T15:45:00Z")
    assert logic.entry_expiry_ms(d, P) == ms("2025-03-01T15:45:00Z")  # shortened below 4h
    d2 = ms("2025-03-01T09:00:00Z")
    assert logic.entry_expiry_ms(d2, P) == ms("2025-03-01T13:00:00Z")  # full 4h
    assert logic.next_window_start_ms(ms("2025-03-01T08:05:00Z"), 15) == ms("2025-03-01T08:05:00Z")


def test_funding_settlements_enumeration():
    got = logic.funding_settlements(ms("2025-03-01T07:00:00Z"), ms("2025-03-02T00:00:00Z"))
    assert [logic.iso(x) for x in got] == ["2025-03-01T08:00:00Z", "2025-03-01T16:00:00Z", "2025-03-02T00:00:00Z"]
    assert logic.funding_settlements(ms("2025-03-01T08:00:00Z"), ms("2025-03-01T15:00:00Z")) == []


def test_bar_freshness():
    now = ms("2025-03-01T10:00:30Z")
    assert logic.bar_freshness(now, ms("2025-03-01T09:00:00Z"), 60) == "fresh"
    assert logic.bar_freshness(now, ms("2025-03-01T08:00:00Z"), 60) == "not_yet"
    assert logic.bar_freshness(now + 61_000, ms("2025-03-01T08:00:00Z"), 60) == "stale"
    assert logic.bar_freshness(now, None, 60) == "stale"


# --- sizing ---------------------------------------------------------------


def test_sizing_rounds_down_and_never_exceeds_risk():
    spec = logic.CONTRACT_SPECS["BTCUSDT"]
    plan, why = logic.plan_long_entry(close=60000.07, atr=400.0, spec=spec, p=P, equity=1000.0)
    assert why == RC.SIGNAL_LONG_ENTRY and plan is not None
    assert plan.entry == Decimal("60000.0") and plan.stop == Decimal("59400.0")
    assert plan.take_profit == Decimal("61200.0")  # 2R
    assert plan.qty == Decimal("0.0250")  # 15/600 = 0.025 exactly
    assert plan.risk_at_stop_usdt <= 15.0
    assert plan.required_leverage == 1500.0 / 1000.0
    plan2, _ = logic.plan_long_entry(close=60000.0, atr=410.0, spec=spec, p=P, equity=1000.0)
    assert plan2.qty * plan2.stop_dist <= Decimal("15")  # 15/615 -> 0.0243 (rounded down)
    assert plan2.qty == Decimal("0.0243")


def test_sizing_skips():
    btc, eth, sol = (logic.CONTRACT_SPECS[s] for s in ("BTCUSDT", "ETHUSDT", "SOLUSDT"))
    assert logic.plan_long_entry(close=60000.0, atr=400.0, spec=btc, p=P, equity=100.0)[1] == RC.SKIP_LEVERAGE_CAP
    assert logic.plan_long_entry(close=60000.0, atr=400.0, spec=btc, p=P, equity=1000.0, open_notional=4000.0)[1] == RC.SKIP_MARGIN_INSUFFICIENT
    assert logic.plan_long_entry(close=60000.0, atr=1e9, spec=btc, p=P, equity=1000.0)[1] == RC.SKIP_INVALID_STOP
    # stop distance so wide that 15/dist rounds below the 0.01 ETH minimum lot
    assert logic.plan_long_entry(close=5000.0, atr=1100.0, spec=eth, p=P, equity=1000.0)[1] == RC.SKIP_BELOW_MIN_QTY
    # lot is fine but notional is under Bitget's 5 USDT minimum (min_notional_usdt)
    small = logic.load_params({"risk_usdt": 0.06})
    plan, why = logic.plan_long_entry(close=100.0, atr=1.0, spec=eth, p=small, equity=1000.0)
    assert plan is None and why == RC.SKIP_BELOW_MIN_QTY


def test_tick_quantisation_per_symbol():
    for sym, px, atr in (("ETHUSDT", 3123.456, 21.37), ("SOLUSDT", 151.23456, 1.3141)):
        spec = logic.CONTRACT_SPECS[sym]
        plan, _ = logic.plan_long_entry(close=px, atr=atr, spec=spec, p=P, equity=2000.0)
        for v in (plan.entry, plan.stop, plan.take_profit):
            assert v % spec.tick == 0
        assert plan.qty % spec.qty_step == 0 and plan.entry <= Decimal(str(px)) and plan.stop < plan.entry < plan.take_profit


# --- risk state -----------------------------------------------------------


def test_risk_pause_halt_and_resume():
    r = logic.RiskState(P, resume_after_hours=72)
    t0 = ms("2025-03-01T10:00:00Z")
    r.record_trade(t0, -15.0)
    assert r.entry_gate(t0 + H) is None
    r.record_trade(t0 + H, -15.0)  # day pnl -30 -> pause
    assert r.entry_gate(t0 + 2 * H) == RC.PAUSE_DAILY_LOSS
    assert r.entry_gate(t0 + 20 * H) is None  # next UTC day
    r.record_trade(t0 + 3 * H, -10.0)  # day -40 -> hard stop latched
    assert r.entry_gate(t0 + 4 * H) == RC.HALT_DAILY_LOSS_STOP
    assert r.entry_gate(t0 + 20 * H) == RC.HALT_DAILY_LOSS_STOP  # latched past midnight
    assert r.entry_gate(t0 + 3 * H + 72 * H) is None  # simulated manual reset (backtest only)
    assert any(c == RC.RESUME_SIMULATED_MANUAL_RESET for _, c, _ in r.events)


def test_consecutive_loss_halt_and_win_resets_streak():
    r = logic.RiskState(P, resume_after_hours=None)
    t = ms("2025-03-01T00:30:00Z")
    for i in range(4):
        r.record_trade(t + i * 2 * DAY, -1.0)
    r.record_trade(t + 9 * DAY, 2.0)
    assert r.consecutive_losses == 0 and r.halt_reason is None
    for i in range(5):
        r.record_trade(t + (10 + i) * DAY, -1.0)
    assert r.halt_reason == RC.HALT_CONSEC_LOSSES
    assert r.entry_gate(t + 400 * DAY) == RC.HALT_CONSEC_LOSSES  # never auto-resumes live


DAY = logic.DAY_MS


# --- config / safety --------------------------------------------------------


def test_config_refuses_unsafe_values():
    for bad in ({"allow_short": True}, {"leverage_cap": 6}, {"margin_mode": "crossed"}, {"max_per_symbol": 2},
                {"trading_symbols": ["DOGEUSDT"]}, {"cost_multiplier": -1}):
        try:
            logic.load_params(bad)
        except logic.ConfigError:
            continue
        raise AssertionError(f"accepted unsafe config {bad}")


def test_param_hash_ignores_eval_keys_and_tracks_frozen_keys():
    h = logic.param_hash({})
    assert h == logic.param_hash({"margin_budget": "5000", "cost_multiplier": 2.0, "trade_start": "2024-01-01T00:00:00Z"})
    assert h != logic.param_hash({"adx_min": 26.0})
    assert logic.sha256_hex(b"abc") == hashlib.sha256(b"abc").hexdigest()


# --- live payload helpers -------------------------------------------------


def _fill(order_id, ts, profit, fee, side="close", symbol="BTCUSDT"):
    rec = {"symbol": symbol, "orderId": order_id, "cTime": str(ts), "tradeSide": side, "priceAvg": "100", "baseVolume": "1",
           "feeDetail": [{"feeCoin": "USDT", "totalFee": str(-fee)}]}
    if profit is not None:
        rec["profit"] = str(profit)
    return rec


def test_realised_summary_day_pnl_streak_and_fail_closed():
    now = ms("2025-03-02T12:00:00Z")
    fills = [
        _fill("o0", now - 5 * DAY, 20, 0.5), _fill("o1", now - 4 * H, -15, 0.5), _fill("o2", now - 3 * H, -15, 0.5),
        _fill("o1", now - 4 * H, None, 0.3, side="open"),
    ]
    s = logic.realised_summary(fills, owned_symbols={"BTCUSDT"}, now_ms=now)
    assert s["pnl_available"] and s["loss_streak"] == 2
    assert math.isclose(s["day_pnl"], -15.5 - 15.5 - 0.3)
    assert logic.realised_summary(fills, owned_symbols={"BTCUSDT"}, now_ms=now, reset_after_ms=now - 3 * H - 1)["loss_streak"] == 1
    missing = fills + [_fill("o9", now - H, None, 0.1)]
    assert not logic.realised_summary(missing, owned_symbols={"BTCUSDT"}, now_ms=now)["pnl_available"]
    assert logic.realised_summary(fills, owned_symbols={"ETHUSDT"}, now_ms=now)["loss_streak"] == 0


def test_extract_records_and_deep_find():
    env = {"code": "00000", "data": {"fillList": [{"symbol": "BTCUSDT", "orderId": "1"}]}}
    assert logic.extract_records(env)[0]["orderId"] == "1"
    assert logic.extract_records({"data": {"entrustedList": []}}) == []
    assert logic.extract_records([{"symbol": "A"}, 3]) == [{"symbol": "A"}]
    assert logic.deep_find({"data": {"x": {"orderId": "77"}}}, ("orderId",)) == "77"

    class Obj:
        def model_dump(self):
            return {"data": {"order_id": "5"}}
    assert logic.deep_find(Obj(), ("order_id",)) == "5"


def test_classify_exit():
    assert logic.classify_exit(99.0, 99.0, 103.0, 0.1, False) == RC.EXIT_STOP_LOSS
    assert logic.classify_exit(103.0, 99.0, 103.0, 0.1, False) == RC.EXIT_TAKE_PROFIT
    assert logic.classify_exit(101.0, 99.0, 103.0, 0.1, True) == RC.EXIT_TIME_STOP
    assert logic.classify_exit(101.0, 99.0, 103.0, 0.1, False) == RC.EXIT_UNKNOWN


# --- costs / metrics ------------------------------------------------------


def _trade(net, gross, r=15.0, day=0, cost=None):
    return {"entry_ts_ms": ms("2025-01-01T00:00:00Z") + day * DAY, "exit_ts_ms": ms("2025-01-01T08:00:00Z") + day * DAY,
            "gross_pnl": gross, "net_pnl": net, "r_usdt": r, "net_r": net / r,
            "costs_1x_total": gross - net if cost is None else cost}


def test_cost_arithmetic():
    c = logic.trade_costs_1x(entry_px=100.0, exit_px=102.0, qty=10.0, tick=0.01, maker_fee=0.0002,
                             taker_fee=0.0006, slippage_ticks=1, funding_paid=0.5)
    assert math.isclose(c["fee_entry"], 0.2) and math.isclose(c["fee_exit"], 0.612)
    assert math.isclose(c["slippage"], 0.2) and math.isclose(c["total"], 0.2 + 0.612 + 0.2 + 0.5)


def test_metrics_hand_computed_and_reprice():
    trades = [_trade(28.0, 30.0, day=0), _trade(-16.0, -15.0, day=1), _trade(-16.0, -15.0, day=2), _trade(14.0, 15.0, day=3)]
    m = logic.compute_metrics(trades, equity_basis=1000.0, start_ms=ms("2025-01-01T00:00:00Z"), end_ms=ms("2025-01-11T00:00:00Z"))
    assert m["trades"] == 4 and m["win_rate"] == 0.5
    assert math.isclose(m["profit_factor"], 42.0 / 32.0)
    assert math.isclose(m["net_pnl"], 10.0) and math.isclose(m["max_drawdown_usdt"], 32.0)
    assert math.isclose(m["expectancy_r_net"], 10.0 / 4 / 15.0)
    assert math.isclose(m["avg_r_gross"], 15.0 / 4 / 15.0)
    assert m["verdict"] == "INSUFFICIENT_TRADES_NO_VERDICT"
    assert m["sharpe_daily_annualised"] is not None
    r0 = logic.reprice_trades(trades, 0.0)
    assert math.isclose(sum(t["net_pnl"] for t in r0), 15.0)
    r2 = logic.reprice_trades(trades, 2.0)
    assert math.isclose(sum(t["net_pnl"] for t in r2), 15.0 - 2 * 5.0)
    assert logic.compute_metrics([], equity_basis=1000.0, start_ms=0, end_ms=DAY)["verdict"] == "NO_TRADES"


def test_walk_forward_windows():
    o, e = ms("2023-01-01T00:00:00Z"), ms("2025-01-01T00:00:00Z")
    w = logic.walk_forward_windows(o, e, 12, 3, 3)
    assert len(w) == 4
    assert logic.iso(w[0]["test_start"]) == "2024-01-01T00:00:00Z" and logic.iso(w[-1]["test_end"]) == "2025-01-01T00:00:00Z"
    assert w[1]["test_start"] == w[0]["test_end"]  # disjoint, contiguous OOS windows
    assert logic.walk_forward_windows(o, ms("2024-12-31T00:00:00Z"), 12, 3, 3).__len__() == 3
    assert logic.add_months(ms("2024-11-30T00:00:00Z"), 3) == ms("2025-02-28T00:00:00Z")


def test_log_record_schema():
    rec = logic.make_log(ms("2025-01-01T00:00:00Z"), "BTCUSDT", "place_entry", RC.ORDER_PLACED, intended_price=Decimal("100.1"), qty=Decimal("0.01"))
    assert set(logic.LOG_FIELDS) == set(rec) and rec["reason_code"] == "ORDER_PLACED" and rec["timestamp"] == "2025-01-01T00:00:00Z"


# --- package consistency / static rules ------------------------------------


def test_manifest_backtest_and_specs_agree():
    man = yaml.safe_load((PKG / "manifest.yaml").read_text())
    cfg = man["strategy_config"]
    expected = set(logic.FROZEN_DEFAULTS) - {"symbols"} | set(logic.EVAL_DEFAULTS) | {"trading_symbols"}
    assert set(cfg) == expected, set(cfg) ^ expected
    for k, v in logic.FROZEN_DEFAULTS.items():
        if k != "symbols":
            assert cfg[k] == v, k
    assert cfg["trading_symbols"] == man["trading_symbols"] == logic.FROZEN_DEFAULTS["symbols"]
    for k in man["user_config_schema"]:
        assert k in cfg and k in logic.EVAL_DEFAULTS  # only non-trading keys are user-editable
    assert man["schedule"]["cron"] == "*/15 * * * *" and man["follow_trade_supported"] is True
    assert man["runtime_profile"] == "deterministic" and man["backtest_support"] == "full"
    spec = yaml.safe_load((PKG / "backtest.yaml").read_text())
    for inst in spec["instruments"]:
        s = logic.CONTRACT_SPECS[inst["raw_symbol"]]
        assert Decimal(inst["price_increment"]) == s.tick and Decimal(inst["size_increment"]) == s.qty_step
        assert Decimal(inst["lot_size"]) == s.qty_step and inst["price_precision"] == s.price_precision
        assert inst["size_precision"] == s.size_precision
        assert Decimal(inst["maker_fee"]) == s.maker_fee and Decimal(inst["taker_fee"]) == s.taker_fee
        assert inst["id"] == inst["raw_symbol"] + ".BITGET"


def test_src_has_no_forbidden_imports_and_pure_logic_is_sdk_free():
    banned = {"requests", "httpx", "ccxt", "urllib", "socket", "subprocess", "os", "sys", "trade_sdk", "hashlib"}
    for path in (PKG / "src").glob("*.py"):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            mods = [a.name for a in node.names] if isinstance(node, ast.Import) else [node.module or ""] if isinstance(node, ast.ImportFrom) and node.level == 0 else []
            for mod in mods:
                assert mod.split(".")[0] not in banned, (path.name, mod)
    logic_mods = {n.module.split(".")[0] if isinstance(n, ast.ImportFrom) else a.name.split(".")[0]
                  for n in ast.walk(ast.parse((PKG / "src" / "logic.py").read_text()))
                  for a in (n.names if isinstance(n, ast.Import) else [None]) if isinstance(n, (ast.Import, ast.ImportFrom))}
    assert "getagent" not in logic_mods and "nautilus_trader" not in logic_mods and "pandas" not in logic_mods


def test_trade_mutations_only_in_execution_module():
    mutating = ("place_order", "cancel_order", "close_position", "change_leverage", "modify_", "open_long", "open_short")
    for path in (PKG / "src").glob("*.py"):
        if path.name == "execution.py":
            continue
        text = path.read_text()
        for name in mutating:
            assert f"contract.{name}" not in text, (path.name, name)
    assert "from getagent import trade" not in (PKG / "src" / "main_backtest.py").read_text()


def test_versioning_doc_hash_matches_code():
    h = logic.param_hash(P)
    doc = (PKG / "docs" / "VERSIONING.md").read_text()
    assert h in doc
    manifest = yaml.safe_load((PKG / "manifest.yaml").read_text())
    assert logic.param_hash(logic.load_params(manifest["strategy_config"])) == h
    for key, value in logic.FROZEN_DEFAULTS.items():
        assert key.split("_")[0] in doc or key in doc, key


def test_no_secret_like_strings_in_package():
    import re
    pat = re.compile(r"(bg_[A-Za-z0-9]{16,})|(ACCESS-KEY['\"]?\s*[:=]\s*['\"]?[A-Za-z0-9_\-]{12,})", re.I)
    for path in PKG.rglob("*"):
        if path.is_file():
            assert not pat.search(path.read_text(errors="ignore")), path


if __name__ == "__main__":
    failures = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"ok    {name}")
            except Exception as exc:  # noqa: BLE001
                failures += 1
                print(f"FAIL  {name}: {type(exc).__name__}: {exc}")
    print("LOGIC TESTS (synthetic, not performance evidence):", "FAILED" if failures else "all passed")
    sys.exit(1 if failures else 0)
