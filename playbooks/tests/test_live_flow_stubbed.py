"""STUBBED live-flow tests for src/main_live.py + src/execution.py.

`getagent` is replaced by an in-memory fake exchange. This checks the Playbook's
OWN control flow (gating, reconciliation, ownership, halt-without-flatten,
no duplicate orders). It does NOT verify that the real Bitget/GetAgent SDK
accepts these calls or returns these payload shapes; see README "PENDING".

Needs pandas (run with the venv python):  python playbooks/tests/test_live_flow_stubbed.py
"""
import json
import os
import sys
import tempfile
import types
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import pandas as pd
import yaml

PKG = Path(__file__).resolve().parents[1] / "bitget-usdtm-trend-v1"
sys.path.insert(0, str(PKG / "src"))

H = 3_600_000
DAY = 24 * H


def ms(text):
    return int(pd.Timestamp(text, tz="UTC").timestamp() * 1000) if "Z" not in text else int(pd.Timestamp(text).timestamp() * 1000)


class FakeExchange:
    def __init__(self):
        self.positions, self.orders, self.fills, self.calls = [], [], [], []

    def ok(self, data=None):
        return {"code": "00000", "data": data if data is not None else []}


EX = FakeExchange()
EMITTED = []
FOLLOW = {"on": True}


def _install_fake_getagent():
    runtime = types.ModuleType("getagent.runtime")
    runtime.manifest = yaml.safe_load((PKG / "manifest.yaml").read_text())

    def emit_signal_or_follow(action, symbol="", confidence=0.0, metrics=None, meta=None, execute_trade=None, **kw):
        EMITTED.append({"action": action, "symbol": symbol, "reason": kw.get("reason_code"), "meta": meta})
        if execute_trade is not None and FOLLOW["on"] and action != "watch":
            return execute_trade()
        return None

    runtime.emit_signal_or_follow = emit_signal_or_follow

    contract = types.SimpleNamespace()

    def current_position(symbol="", product_type="USDT-FUTURES"):
        return EX.ok([p for p in EX.positions if not symbol or p["symbol"] == symbol])

    def pending_orders(symbol="", limit=None, product_type="USDT-FUTURES"):
        return EX.ok({"entrustedList": [o for o in EX.orders if not symbol or o["symbol"] == symbol]})

    def fills(symbol="", order_id="", limit=None, product_type="USDT-FUTURES"):
        return EX.ok({"fillList": EX.fills})

    def place_order(**kw):
        EX.calls.append(("place_order", kw))
        oid = f"oid{len(EX.calls)}"
        EX.orders.append({"symbol": kw["symbol"], "orderId": oid, "marginMode": kw["margin_mode"],
                          "presetStopLossPrice": kw["sl_trigger_price"], "presetStopSurplusPrice": kw["tp_trigger_price"]})
        return EX.ok({"orderId": oid})

    def cancel_order(symbol, order_id, product_type="USDT-FUTURES"):
        EX.calls.append(("cancel_order", symbol, order_id))
        EX.orders[:] = [o for o in EX.orders if o["orderId"] != order_id]
        return EX.ok()

    def close_position(symbol, hold_side, product_type="USDT-FUTURES"):
        EX.calls.append(("close_position", symbol, hold_side))
        EX.positions[:] = [p for p in EX.positions if p["symbol"] != symbol]
        return EX.ok()

    def change_leverage(symbol, leverage, **kw):
        EX.calls.append(("change_leverage", symbol, leverage))
        return EX.ok()

    contract.current_position, contract.pending_orders, contract.fills = current_position, pending_orders, fills
    contract.place_order, contract.cancel_order, contract.close_position = place_order, cancel_order, close_position
    contract.change_leverage = change_leverage
    contract.plan_pending_orders = lambda symbol="", **kw: EX.ok([])

    helpers = types.SimpleNamespace(
        contract_position_records=lambda res, symbol="": list(res["data"]),
        find_contract_position=lambda res, symbol, hold_side="", prefer_first=False: next(
            (SimpleNamespace(hold_side="long", symbol=symbol) for p in res["data"] if p["symbol"] == symbol), None),
        resolve_contract_tpsl=lambda **kw: SimpleNamespace(tp_trigger_price=kw["tp_trigger_price"], sl_trigger_price=kw["sl_trigger_price"]),
        contract_rules=lambda symbol, product_type="USDT-FUTURES": SimpleNamespace(
            price_step={"BTCUSDT": "0.1", "ETHUSDT": "0.01", "SOLUSDT": "0.001"}[symbol]),
    )
    trade = types.ModuleType("getagent.trade")
    trade.contract, trade.helpers = contract, helpers
    trade.is_success = lambda res: isinstance(res, dict) and res.get("code") == "00000"

    pkg = types.ModuleType("getagent")
    pkg.runtime, pkg.trade = runtime, trade
    pkg.data = types.SimpleNamespace(to_records=lambda x: x, crypto=types.SimpleNamespace(futures=types.SimpleNamespace()))
    pkg.backtest = types.SimpleNamespace(prepare_frame=lambda *a, **k: pd.DataFrame())
    sys.modules.update({"getagent": pkg, "getagent.runtime": runtime, "getagent.trade": trade})


_install_fake_getagent()
import features  # noqa: E402
import ledger as ledger_mod  # noqa: E402
import logic  # noqa: E402
import main_live  # noqa: E402

RC = logic.ReasonCode


class _Clock:
    now_ms = 0

    @classmethod
    def now(cls, tz=None):
        return datetime.fromtimestamp(cls.now_ms / 1000, tz=timezone.utc)


main_live.datetime = _Clock

FEATS = logic.Features(close=60000.0, ema_fast=59900.0, ema_slow=59000.0, atr=400.0, atr_pct=0.0066, atr_pct_rank=50.0,
                       adx=30.0, plus_di=30.0, minus_di=10.0, vol_ratio=2.0, structure=True, structure_prev=False, ready=True)
STATE = {"latest": None, "feats": FEATS, "mark_rate": 0.0001}


def setup_env(now_iso, latest_iso):
    EX.positions, EX.orders, EX.fills, EX.calls = [], [], [], []
    EMITTED.clear()
    FOLLOW["on"] = True
    _Clock.now_ms = ms(now_iso)
    STATE["latest"] = ms(latest_iso)
    STATE["mark_rate"] = 0.0001
    features.latest_closed_bar_open_ms = lambda symbol: STATE["latest"]
    features.mark_snapshot = lambda symbol: {"mark_price": 60000.0, "last_funding_rate": STATE["mark_rate"], "next_funding_time_ms": None}
    features.fetch_funding = lambda *a, **k: None
    main_live._features_for = lambda symbol, latest, p: STATE["feats"] if symbol == "BTCUSDT" else logic.Features(close=1.0)


def fresh_dir():
    d = tempfile.mkdtemp()
    os.chdir(d)
    return Path(d)


def run_at(now_iso):
    _Clock.now_ms = ms(now_iso)
    main_live.run()
    return json.loads((Path("output") / "playbook_actions.json").read_text())["records"]


def reasons(records):
    return [r["reason_code"] for r in records]


def mutating(kind):
    return [c for c in EX.calls if c[0] == kind]


def test_entry_is_isolated_with_preset_sltp_and_not_duplicated():
    fresh_dir()
    setup_env("2025-03-03T10:00:10Z", "2025-03-03T09:00:00Z")
    recs = run_at("2025-03-03T10:00:10Z")
    placed = mutating("place_order")
    assert len(placed) == 1 and placed[0][1]["margin_mode"] == "isolated" and placed[0][1]["order_type"] == "limit"
    assert placed[0][1]["sl_trigger_price"] and placed[0][1]["tp_trigger_price"]
    assert Decimal_ok(placed[0][1]["qty"], placed[0][1]["price"], placed[0][1]["sl_trigger_price"])
    assert mutating("change_leverage")[0][2] == 5
    assert RC.ORDER_PLACED.value in reasons(recs)
    saved = json.loads(Path(".state/ledger.json").read_text())
    assert saved["owned"]["BTCUSDT"]["status"] == "pending"
    run_at("2025-03-03T10:15:10Z")  # same bar again, order still resting
    assert len(mutating("place_order")) == 1


def Decimal_ok(qty, price, sl):
    from decimal import Decimal
    return Decimal(qty) * (Decimal(price) - Decimal(sl)) <= Decimal("15")


def test_fill_then_time_stop_then_flat_logs_exit():
    fresh_dir()
    setup_env("2025-03-03T10:00:10Z", "2025-03-03T09:00:00Z")
    run_at("2025-03-03T10:00:10Z")
    oid = EX.orders[0]["orderId"]
    EX.orders.clear()
    fill_ms = ms("2025-03-03T10:20:00Z")
    EX.positions.append({"symbol": "BTCUSDT", "holdSide": "long", "total": "0.025", "openPriceAvg": "60000", "cTime": str(fill_ms), "marginMode": "isolated"})
    recs = run_at("2025-03-03T10:30:10Z")
    assert RC.ORDER_FILLED.value in reasons(recs) and not mutating("close_position")
    STATE["latest"] = ms("2025-03-03T17:00:00Z")
    recs = run_at("2025-03-03T18:20:10Z")  # 8h after fill
    assert mutating("close_position") == [("close_position", "BTCUSDT", "long")]
    assert RC.EXIT_TIME_STOP.value in reasons(recs)
    EX.fills.append({"symbol": "BTCUSDT", "orderId": "c1", "cTime": str(ms("2025-03-03T18:20:30Z")), "tradeSide": "close", "priceAvg": "60100",
                     "baseVolume": "0.025", "profit": "2.5", "feeDetail": [{"totalFee": "-0.9"}]})
    recs = run_at("2025-03-03T18:35:10Z")
    exits = [r for r in recs if r["action"] == "exit"]
    assert exits and exits[0]["reason_code"] == RC.EXIT_TIME_STOP.value and abs(exits[0]["pnl_usdt"] - 1.6) < 1e-9
    assert json.loads(Path(".state/ledger.json").read_text())["owned"] == {}
    assert oid


def test_unfilled_entry_cancelled_after_expiry_and_before_funding():
    fresh_dir()
    setup_env("2025-03-03T14:00:10Z", "2025-03-03T13:00:00Z")
    run_at("2025-03-03T14:00:10Z")
    led = json.loads(Path(".state/ledger.json").read_text())["owned"]["BTCUSDT"]
    assert led["expire_ms"] == ms("2025-03-03T15:45:00Z")  # shortened ahead of 16:00 funding
    run_at("2025-03-03T15:30:10Z")
    assert not mutating("cancel_order")
    recs = run_at("2025-03-03T15:45:10Z")
    assert len(mutating("cancel_order")) == 1 and RC.ORDER_CANCELLED_FUNDING_WINDOW.value in reasons(recs)
    assert json.loads(Path(".state/ledger.json").read_text())["owned"] == {}


def test_foreign_position_halts_entries_and_is_never_touched():
    fresh_dir()
    setup_env("2025-03-03T10:00:10Z", "2025-03-03T09:00:00Z")
    EX.positions.append({"symbol": "ETHUSDT", "holdSide": "long", "total": "1", "openPriceAvg": "3000", "cTime": "1", "marginMode": "crossed"})
    recs = run_at("2025-03-03T10:00:10Z")
    assert RC.HALT_FOREIGN_POSITION.value in reasons(recs)
    assert not mutating("place_order") and not mutating("close_position") and not mutating("cancel_order")


def test_five_consecutive_losses_halt_without_flattening():
    fresh_dir()
    now = ms("2025-03-03T10:00:10Z")
    setup_env("2025-03-03T10:00:10Z", "2025-03-03T09:00:00Z")
    for i in range(5):
        EX.fills.append({"symbol": "BTCUSDT", "orderId": f"l{i}", "cTime": str(now - (30 - i * 5) * H), "tradeSide": "close", "priceAvg": "1",
                         "baseVolume": "1", "profit": "-1", "feeDetail": [{"totalFee": "-0.1"}]})
    recs = run_at("2025-03-03T10:00:10Z")
    assert RC.HALT_CONSEC_LOSSES.value in reasons(recs) and not mutating("place_order") and not mutating("close_position")
    marker = now + 1  # operator raises halt_reset_after_ts_ms
    main_live.runtime.manifest["strategy_config"]["halt_reset_after_ts_ms"] = marker
    try:
        setup_env("2025-03-03T10:15:10Z", "2025-03-03T09:00:00Z")
        EX.fills.extend([])
        recs = run_at("2025-03-03T10:15:10Z")
        assert RC.HALT_CONSEC_LOSSES.value not in reasons(recs)
    finally:
        main_live.runtime.manifest["strategy_config"]["halt_reset_after_ts_ms"] = 0


def test_hard_daily_stop_latches_and_pause_threshold():
    fresh_dir()
    now = ms("2025-03-03T10:00:10Z")
    setup_env("2025-03-03T10:00:10Z", "2025-03-03T09:00:00Z")
    EX.fills.append({"symbol": "BTCUSDT", "orderId": "a", "cTime": str(now - 2 * H), "tradeSide": "close", "priceAvg": "1", "baseVolume": "1", "profit": "-31", "feeDetail": []})
    recs = run_at("2025-03-03T10:00:10Z")
    assert RC.PAUSE_DAILY_LOSS.value in reasons(recs) and not mutating("place_order")
    EX.fills.append({"symbol": "BTCUSDT", "orderId": "b", "cTime": str(now - H), "tradeSide": "close", "priceAvg": "1", "baseVolume": "1", "profit": "-10", "feeDetail": []})
    recs = run_at("2025-03-03T10:15:10Z")
    assert RC.HALT_DAILY_LOSS_STOP.value in reasons(recs)
    EX.fills.clear()  # even if the fills window rolls, the latch persists in .state
    recs = run_at("2025-03-04T01:00:10Z")
    assert RC.HALT_DAILY_LOSS_STOP.value in reasons(recs) and not mutating("place_order")


def test_missing_pnl_field_fails_closed():
    fresh_dir()
    setup_env("2025-03-03T10:00:10Z", "2025-03-03T09:00:00Z")
    EX.fills.append({"symbol": "BTCUSDT", "orderId": "a", "cTime": str(ms("2025-03-03T08:00:00Z")), "tradeSide": "close", "priceAvg": "1", "baseVolume": "1"})
    recs = run_at("2025-03-03T10:00:10Z")
    assert RC.HALT_PNL_UNAVAILABLE.value in reasons(recs) and not mutating("place_order")


def test_stale_data_blocks_entry():
    fresh_dir()
    setup_env("2025-03-03T10:02:00Z", "2025-03-03T08:00:00Z")  # 09:00 bar missing > 60s after the hour
    recs = run_at("2025-03-03T10:02:00Z")
    assert RC.HALT_STALE_DATA.value in reasons(recs) and not mutating("place_order")
    setup_env("2025-03-03T10:00:30Z", "2025-03-03T08:00:00Z")  # within 60s grace: wait, no alert
    recs = run_at("2025-03-03T10:00:30Z")
    assert RC.HALT_STALE_DATA.value not in reasons(recs) and not mutating("place_order")


def test_funding_window_and_adverse_funding_and_stale_signal():
    fresh_dir()
    setup_env("2025-03-03T08:00:10Z", "2025-03-03T07:00:00Z")
    assert RC.NO_TRADE_FUNDING_WINDOW.value in reasons(run_at("2025-03-03T08:00:10Z")) and not mutating("place_order")
    fresh_dir()
    setup_env("2025-03-03T10:00:10Z", "2025-03-03T09:00:00Z")
    STATE["mark_rate"] = 0.00031
    assert RC.SKIP_FUNDING_RATE_ADVERSE.value in reasons(run_at("2025-03-03T10:00:10Z")) and not mutating("place_order")
    fresh_dir()
    setup_env("2025-03-03T10:20:00Z", "2025-03-03T09:00:00Z")  # signal 20 min old > 15
    assert RC.SKIP_SIGNAL_STALE.value in reasons(run_at("2025-03-03T10:20:00Z")) and not mutating("place_order")


def test_non_follow_subscription_places_nothing_and_records_no_ownership():
    fresh_dir()
    setup_env("2025-03-03T10:00:10Z", "2025-03-03T09:00:00Z")
    FOLLOW["on"] = False
    recs = run_at("2025-03-03T10:00:10Z")
    assert not EX.calls and "signal_only" in [r["action"] for r in recs]
    assert json.loads(Path(".state/ledger.json").read_text())["owned"] == {}


def test_max_concurrent_blocks_scanning():
    fresh_dir()
    setup_env("2025-03-03T10:00:10Z", "2025-03-03T09:00:00Z")
    led = ledger_mod.Ledger()
    for s in ("BTCUSDT", "ETHUSDT", "SOLUSDT"):
        led.owned[s] = {"status": "pending", "placed_ms": ms("2025-03-03T09:55:00Z"), "expire_ms": ms("2025-03-03T13:00:00Z"),
                        "plan": {"entry": 1.0, "stop": 0.5, "take_profit": 2.0, "qty": 1.0, "notional": 1.0, "risk": 1.0}}
        EX.orders.append({"symbol": s, "orderId": s})
    led.save()
    run_at("2025-03-03T10:00:10Z")
    assert not mutating("place_order")


if __name__ == "__main__":
    failures = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"ok    {name}")
            except Exception as exc:  # noqa: BLE001
                import traceback
                failures += 1
                print(f"FAIL  {name}: {type(exc).__name__}: {exc}")
                traceback.print_exc()
    print("STUBBED LIVE-FLOW TESTS (fake exchange, not SDK verification):", "FAILED" if failures else "all passed")
    sys.exit(1 if failures else 0)
