"""Local-only smoke test of main_live.Cycle against a stub getagent module.

Checks control flow (entry -> fill -> time stop -> exit reconcile, foreign
position halt). Response shapes of the real trade SDK are assumptions here.
"""
import json
import os
import sys
import tempfile
import types
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent
PKG = ROOT.parent / "playbooks" / "crypto-perp-trend-pullback"
HOUR = 3_600_000
DATA = {s: json.loads((ROOT / "data" / f"{s}_1h.json").read_text()) for s in ("BTCUSDT", "ETHUSDT", "SOLUSDT")}

CLOCK = {"now": 0, "offset": 0}
ACCOUNT = {"positions": [], "pending": [], "plan": [], "fills": [], "placed": [], "closed": [], "cancelled": []}
SIGNALS = []


def _kline(symbol, interval, exchange, limit, start_time, end_time, closed_only=True):
    rows = DATA[symbol]
    n = int((end_time - start_time) // HOUR)
    end_idx = len(rows) - CLOCK["offset"]
    seg = rows[max(0, end_idx - n):end_idx]
    out = []
    for i, r in enumerate(seg):
        ts = end_time - (len(seg) - i) * HOUR
        out.append({"time": ts, "open": r[1], "high": r[2], "low": r[3], "close": r[4], "volume": r[5]})
    return out


def _ticker(symbol, exchange):
    rows = DATA[symbol]
    c = float(rows[len(rows) - CLOCK["offset"] - 1][4])
    return [{"timestamp": CLOCK["now"] - 5000, "bid": c, "ask": c * 1.00001, "quote_volume": 2e9}]


def _funding(symbol, exchange, interval, limit, start_time, end_time):
    return [{"timestamp": end_time - HOUR, "funding_rate": 0.01}]  # SDK percent units


def build_stub(manifest):
    g = types.ModuleType("getagent")
    data = types.SimpleNamespace(
        crypto=types.SimpleNamespace(futures=types.SimpleNamespace(kline=_kline, ticker=_ticker, funding_rate=_funding)),
        to_records=lambda x: x,
    )
    ok = {"code": "00000", "data": []}

    def place_order(**kw):
        ACCOUNT["placed"].append(kw)
        return {"code": "00000", "data": {"orderId": f"OID{len(ACCOUNT['placed'])}"}}

    contract = types.SimpleNamespace(
        current_position=lambda symbol="": {"code": "00000", "data": ACCOUNT["positions"]},
        pending_orders=lambda symbol="": {"code": "00000", "data": ACCOUNT["pending"]},
        plan_pending_orders=lambda symbol="": {"code": "00000", "data": ACCOUNT["plan"]},
        fills=lambda symbol="", order_id="", limit=None: {"code": "00000", "data": {"fillList": ACCOUNT["fills"]}},
        change_leverage=lambda symbol, leverage: ok,
        place_order=place_order,
        cancel_order=lambda symbol, order_id: (ACCOUNT["cancelled"].append(order_id), ok)[1],
        close_position=lambda symbol, hold_side: (ACCOUNT["closed"].append(symbol), ok)[1],
    )
    helpers = types.SimpleNamespace(
        contract_open_symbols=lambda res: sorted({p["symbol"] for p in res["data"]}),
        contract_rules=lambda s: types.SimpleNamespace(price_step={"BTCUSDT": "0.1", "ETHUSDT": "0.01", "SOLUSDT": "0.001"}[s]),
        resolve_contract_tpsl=lambda **kw: types.SimpleNamespace(tp_trigger_price=kw["tp_trigger_price"], sl_trigger_price=kw["sl_trigger_price"]),
    )
    trade = types.SimpleNamespace(contract=contract, helpers=helpers, is_success=lambda r: r.get("code") == "00000")

    def emit_signal_or_follow(action, symbol, confidence, metrics, meta, execute_trade=None, **kw):
        SIGNALS.append({"action": action, "symbol": symbol, **meta})
        if action not in ("watch", "hold") and execute_trade is not None:
            return execute_trade()

    def emit_signal(action, symbol="", confidence=0.0, metrics=None, meta=None):
        SIGNALS.append({"action": action, "symbol": symbol, **(meta or {})})

    runtime = types.SimpleNamespace(manifest=manifest, emit_signal=emit_signal, emit_signal_or_follow=emit_signal_or_follow,
                                    is_historical=lambda: False, is_live=lambda: True)
    g.data, g.trade, g.runtime = data, trade, runtime
    g.backtest = types.SimpleNamespace()
    sys.modules["getagent"] = g


def main():
    manifest = yaml.safe_load((PKG / "manifest.yaml").read_text())
    build_stub(manifest)
    sys.path.insert(0, str(PKG))
    os.chdir(tempfile.mkdtemp())
    from src import main_live

    base_now = 1_790_812_800_000 + 16 * 60_000
    main_live._now_ms = lambda: CLOCK["now"]

    placed_at = None
    for off in range(0, 2000):
        CLOCK["offset"], CLOCK["now"] = off, base_now - off * HOUR
        SIGNALS.clear()
        main_live.Cycle().run()
        if ACCOUNT["placed"]:
            placed_at = off
            break
    assert placed_at is not None, "no entry found in scanned windows"
    base_now = CLOCK["now"]
    order = ACCOUNT["placed"][-1]
    print("ENTRY at offset", placed_at, order)
    state = json.loads(Path(".state/crypto_majors_trend_pullback.json").read_text())
    oid = next(iter(state["orders"]))

    ACCOUNT["positions"] = [{"symbol": order["symbol"], "holdSide": "long", "total": order["qty"]}]
    ACCOUNT["plan"] = [{"symbol": order["symbol"], "planType": "loss_plan"}, {"symbol": order["symbol"], "planType": "profit_plan"}]
    ACCOUNT["fills"] = [{"orderId": oid, "price": order["price"], "baseVolume": order["qty"], "fee": "-0.3", "cTime": base_now + HOUR}]
    CLOCK["now"] = base_now + HOUR
    SIGNALS.clear()
    main_live.Cycle().run()
    print("RUN2", [a["reason_code"] for a in SIGNALS[-1]["actions"]], SIGNALS[-1]["status"])

    CLOCK["now"] = base_now + 10 * HOUR
    SIGNALS.clear()
    main_live.Cycle().run()
    print("RUN3", [a["reason_code"] for a in SIGNALS[-1]["actions"]], "closed:", ACCOUNT["closed"])

    ACCOUNT["positions"], ACCOUNT["plan"] = [], []
    ACCOUNT["fills"] = [{"price": float(order["price"]) * 0.995, "baseVolume": order["qty"], "fee": "-0.9", "profit": "-7.5",
                         "cTime": base_now + 10 * HOUR + 60_000}]
    CLOCK["now"] = base_now + 11 * HOUR
    SIGNALS.clear()
    main_live.Cycle().run()
    print("RUN4", json.dumps(SIGNALS[-1]["actions"][:3], indent=0)[:900])

    ACCOUNT["positions"] = [{"symbol": "ETHUSDT", "holdSide": "short", "total": "1"}]
    CLOCK["now"] = base_now + 12 * HOUR
    SIGNALS.clear()
    main_live.Cycle().run()
    print("RUN5", [a["reason_code"] for a in SIGNALS[-1]["actions"]], SIGNALS[-1]["status"])


if __name__ == "__main__":
    main()
