"""Local-only harness: run the Playbook's Nautilus strategy on Bitget public data.

Mechanics/debug check only. Bitget's public funding history covers ~90 days, so
earlier funding is filled with the observed median here and the output is
marked LOCAL_DEV. Official figures come from the GetAgent sandbox run.
"""
from __future__ import annotations

import json
import statistics
import sys
import time
from decimal import Decimal
from pathlib import Path

import pandas as pd
import yaml
from nautilus_trader.backtest.engine import BacktestEngine, BacktestEngineConfig
from nautilus_trader.config import LoggingConfig
from nautilus_trader.model.currencies import USDT
from nautilus_trader.model.data import BarType
from nautilus_trader.model.enums import AccountType, OmsType
from nautilus_trader.model.identifiers import InstrumentId, Symbol, Venue
from nautilus_trader.model.instruments import CryptoPerpetual
from nautilus_trader.model.objects import Money, Price, Quantity
from nautilus_trader.model.currencies import Currency
from nautilus_trader.persistence.wranglers import BarDataWrangler

ROOT = Path(__file__).resolve().parent
PKG = ROOT.parent / "playbooks" / "crypto-perp-trend-pullback"
sys.path.insert(0, str(PKG))

from src import ledger  # noqa: E402
from src.signals import Params  # noqa: E402
from src.strategy import TrendPullbackConfig, TrendPullbackStrategy  # noqa: E402


def load_frame(sym: str) -> pd.DataFrame:
    rows = json.loads((ROOT / "data" / f"{sym}_1h.json").read_text())
    df = pd.DataFrame(rows, columns=["ts", "open", "high", "low", "close", "volume", "quote_volume"])
    df["ts"] = pd.to_datetime(df["ts"].astype("int64"), unit="ms", utc=True)
    df = df.set_index("ts")
    for c in ("open", "high", "low", "close", "volume"):
        df[c] = df[c].astype(float)
    fund = json.loads((ROOT / "data" / f"{sym}_funding.json").read_text())
    fs = pd.Series({pd.to_datetime(int(r["fundingTime"]), unit="ms", utc=True): float(r["fundingRate"]) for r in fund}).sort_index()
    med = float(fs.median()) if len(fs) else 0.0001
    df["funding_rate"] = fs.reindex(df.index, method="ffill").fillna(med)
    return df[["open", "high", "low", "close", "volume", "funding_rate"]]


def make_instrument(spec: dict) -> CryptoPerpetual:
    sym = spec["raw_symbol"]
    base = Currency.from_str(spec["base_currency"])
    return CryptoPerpetual(
        instrument_id=InstrumentId.from_str(spec["id"]),
        raw_symbol=Symbol(sym),
        base_currency=base,
        quote_currency=USDT,
        settlement_currency=USDT,
        is_inverse=False,
        price_precision=int(spec["price_precision"]),
        size_precision=int(spec["size_precision"]),
        price_increment=Price.from_str(spec["price_increment"]),
        size_increment=Quantity.from_str(spec["size_increment"]),
        maker_fee=Decimal(spec["maker_fee"]),
        taker_fee=Decimal(spec["taker_fee"]),
        margin_init=Decimal("0.2"),
        margin_maint=Decimal("0.01"),
        ts_event=0,
        ts_init=0,
    )


def main() -> None:
    t0 = time.time()
    manifest = yaml.safe_load((PKG / "manifest.yaml").read_text())
    spec = yaml.safe_load((PKG / "backtest.yaml").read_text())
    cfg = manifest["strategy_config"]
    p = Params.from_config(cfg)
    bt = cfg["backtest"]
    start_ms = ledger.month_start_ms(*bt["start_ym"])
    end_ms = ledger.month_start_ms(*bt["end_ym"])

    engine = BacktestEngine(BacktestEngineConfig(logging=LoggingConfig(log_level="ERROR")))
    engine.add_venue(Venue("BITGET"), oms_type=OmsType.NETTING, account_type=AccountType.MARGIN,
                     base_currency=None, starting_balances=[Money(100_000, USDT)])
    frames = {}
    funding = {}
    for ins in spec["instruments"]:
        inst = make_instrument(ins)
        engine.add_instrument(inst)
        df = load_frame(ins["raw_symbol"])
        df = df[df.index < pd.Timestamp(end_ms, unit="ms", tz="UTC")]
        frames[ins["id"]] = df
        wr = BarDataWrangler(BarType.from_str(ins["bar_type"]), inst)
        engine.add_data(wr.process(df[["open", "high", "low", "close", "volume"]]))
        settle = df[df.index.hour % 8 == 0]["funding_rate"]
        funding[ins["raw_symbol"]] = [(int(ts.value // 1_000_000), float(r)) for ts, r in settle.items()]

    ledger_path = ROOT / "out" / "trades_ledger.json"
    conf = TrendPullbackConfig(
        instrument_ids=tuple(InstrumentId.from_str(i["id"]) for i in spec["instruments"]),
        bar_types=tuple(BarType.from_str(i["bar_type"]) for i in spec["instruments"]),
        params_json=json.dumps(cfg),
        trade_start_ms=start_ms,
        trade_end_ms=end_ms,
        ledger_path=str(ledger_path),
        funding_json=json.dumps(funding),
    )
    strat = TrendPullbackStrategy(conf)
    engine.add_strategy(strat)
    engine.run()
    reports = {
        "orders": engine.trader.generate_orders_report(),
        "fills": engine.trader.generate_order_fills_report(),
        "positions": engine.trader.generate_positions_report(),
        "account": engine.trader.generate_account_report(Venue("BITGET")),
    }
    engine.dispose()
    if "--dump-reports" in sys.argv:
        for name, df in reports.items():
            blob = json.dumps(df.reset_index().to_dict(orient="records"), default=str)
            print("report", name, df.shape, "json bytes", len(blob), file=sys.stderr)

    led = json.loads(ledger_path.read_text())
    folds = [(f["name"], ledger.month_start_ms(*f["start_ym"]), ledger.month_start_ms(*f["end_ym"])) for f in bt["walk_forward_folds"]]
    split = (bt["oos_split_label"], ledger.month_start_ms(*bt["oos_start_ym"]))
    rep = ledger.build_report(
        led["trades"], funding, start_ms=start_ms, end_ms=end_ms, folds=folds, split=split,
        maker=float(cfg["maker_fee"]), taker=float(cfg["taker_fee"]), slip_ticks=p.slippage_ticks,
        risk=p.risk_usdt, budget=p.margin_budget, interval_hours=p.funding_interval_hours,
    )
    rep.pop("equity_curve")
    per_trade = rep.pop("per_trade_1x")
    out = {"LOCAL_DEV": True, "skips": led["skips"], "halt_events": led["halt_events"], **rep}
    (ROOT / "out" / "local_report.json").write_text(json.dumps(out, indent=2))
    (ROOT / "out" / "local_trades.json").write_text(json.dumps(per_trade, indent=1))
    print(json.dumps(out, indent=2))
    print("elapsed", round(time.time() - t0, 1), "s")


if __name__ == "__main__":
    main()
