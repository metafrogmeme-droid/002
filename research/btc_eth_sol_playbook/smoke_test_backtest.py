"""Local smoke test of the Playbook's src/main_backtest.py using a mock `getagent` module.

The mock serves the downloaded Bitget CSVs through `data.crypto.futures.kline/funding_rate`
and implements `backtest.run` with a plain Nautilus BacktestEngine (same wiring as
nautilus_harness.py). It only checks that the Playbook code path runs end to end and
writes its outputs; it is NOT the managed GetAgent engine.

Usage: python3 smoke_test_backtest.py --start 2026-04-01 --end 2026-10-01
"""
import argparse
import json
import sys
import tempfile
import types
from pathlib import Path

import pandas as pd
import yaml

HERE = Path(__file__).resolve().parent
PKG = HERE.parents[1] / "playbooks" / "btc-eth-sol-regime-long"
HOUR_MS = 3_600_000


class _Records(list):
    pass


def _kline(symbol, interval, exchange, limit, start_time, end_time, closed_only=True):
    assert interval == "1h" and exchange == "bitget" and limit <= 1000
    assert end_time - start_time <= 90 * 86_400_000
    df = pd.read_csv(HERE / "data" / f"{symbol}_1h.csv")
    df = df[(df.ts >= start_time) & (df.ts <= end_time)].tail(limit)
    return _Records({"time": int(r.ts), "date": pd.Timestamp(int(r.ts), unit="ms", tz="UTC").isoformat(),
                     "open": r.open, "high": r.high, "low": r.low, "close": r.close, "volume": r.volume,
                     "symbol": symbol, "interval": "1h", "exchange": "bitget"} for r in df.itertuples())


def _funding_rate(symbol, exchange, interval="4h", limit=1000, start_time=None, end_time=None, days=None):
    df = pd.read_csv(HERE / "data" / f"{symbol}_funding.csv")
    src = "bitget" if exchange == "bitget" else "binance_proxy"
    df = df[(df.source == src) & (df.ts >= start_time) & (df.ts <= end_time)].tail(limit)
    return _Records({"timestamp": pd.Timestamp(int(r.ts), unit="ms", tz="UTC").isoformat(),
                     "date": pd.Timestamp(int(r.ts), unit="ms", tz="UTC").isoformat(),
                     "funding_rate": r.rate, "symbol": symbol, "exchange": exchange} for r in df.itertuples())


class _Result:
    def __init__(self, raw, trades):
        self.raw = raw
        self.summary = raw["summary"]
        self.total_trades = trades
        self.position_count = trades
        self.total_return_pct = None


def _run(ohlcv_data, spec):
    from decimal import Decimal
    from nautilus_trader.backtest.engine import BacktestEngine, BacktestEngineConfig
    from nautilus_trader.model.currencies import USDT, Currency
    from nautilus_trader.model.data import BarType
    from nautilus_trader.model.enums import AccountType, OmsType
    from nautilus_trader.model.identifiers import InstrumentId, Symbol, Venue
    from nautilus_trader.model.instruments import CryptoPerpetual
    from nautilus_trader.model.objects import Money, Price, Quantity
    from nautilus_trader.persistence.wranglers import BarDataWrangler
    from src.strategy import RegimeLongConfig, RegimeLongStrategy

    venue = spec["venue"]["name"]
    engine = BacktestEngine(config=BacktestEngineConfig(trader_id="SMOKE-001"))
    engine.add_venue(venue=Venue(venue), oms_type=OmsType.NETTING, account_type=AccountType.MARGIN,
                     base_currency=USDT, starting_balances=[Money(100_000, USDT)])
    start = pd.Timestamp(spec["execution"]["start"])
    end = pd.Timestamp(spec["execution"]["end"])
    for fld in spec["data_requirements"]["required_bar_fields"]:
        for key, frame in ohlcv_data.items():
            w = frame.loc[start:end]
            assert fld in frame.columns and not w[fld].isna().all(), (key, fld)
    for ins in spec["instruments"]:
        inst = CryptoPerpetual(
            instrument_id=InstrumentId.from_str(ins["id"]), raw_symbol=Symbol(ins["raw_symbol"]),
            base_currency=Currency.from_str(ins["base_currency"]), quote_currency=USDT, settlement_currency=USDT,
            is_inverse=False, price_precision=ins["price_precision"], size_precision=ins["size_precision"],
            price_increment=Price.from_str(ins["price_increment"]), size_increment=Quantity.from_str(ins["size_increment"]),
            margin_init=Decimal("0.2"), margin_maint=Decimal("0.01"), maker_fee=Decimal(ins["maker_fee"]),
            taker_fee=Decimal(ins["taker_fee"]), ts_event=0, ts_init=0)
        engine.add_instrument(inst)
        frame = ohlcv_data[ins["id"]].loc[start:end]
        engine.add_data(BarDataWrangler(BarType.from_str(ins["bar_type"]), inst).process(
            frame[["open", "high", "low", "close", "volume"]]))
    cfg = RegimeLongConfig(**spec["strategy"]["config"])
    strat = RegimeLongStrategy(cfg)
    strat.set_feature_frames(ohlcv_data)
    engine.add_strategy(strat)
    engine.run()
    n = len(engine.trader.generate_positions_report())
    engine.dispose()
    return _Result({"summary": {"net_pnl": None}, "stats": {}, "reports": {"equity_curve": [1]}, "config": {}}, n)


def install_mock(manifest, spec, emitted):
    ga = types.ModuleType("getagent")
    data = types.SimpleNamespace(
        crypto=types.SimpleNamespace(futures=types.SimpleNamespace(kline=_kline, funding_rate=_funding_rate)),
        to_records=lambda x: list(x))
    backtest = types.SimpleNamespace(prepare_frame=lambda f, **k: f, run=_run, generate_chart=lambda r: "")
    runtime = types.SimpleNamespace(manifest=manifest, backtest_spec=spec, run_id="smoke",
                                    emit_signal=lambda **kw: emitted.append(kw))
    ga.data, ga.backtest, ga.runtime = data, backtest, runtime
    sys.modules["getagent"] = ga


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="2026-04-01T00:00:00Z")
    ap.add_argument("--end", default="2026-10-01T00:00:00Z")
    args = ap.parse_args()
    manifest = yaml.safe_load((PKG / "manifest.yaml").read_text())
    spec = yaml.safe_load((PKG / "backtest.yaml").read_text())
    spec["execution"] = {"start": args.start, "end": args.end}
    emitted = []
    install_mock(manifest, spec, emitted)
    sys.path.insert(0, str(PKG))
    from src import main_backtest
    out = Path(tempfile.mkdtemp())
    main_backtest.OUT_DIR = out
    main_backtest.run()
    print(json.dumps(emitted[-1]["metrics"], indent=1))
    print(json.dumps({k: v for k, v in emitted[-1]["meta"].items() if k != "coverage"}, indent=1, default=str)[:1500])
    print("outputs:", sorted(p.name for p in out.iterdir()))
    print((out / "equity_curve.csv").read_text().splitlines()[:3])


if __name__ == "__main__":
    main()
