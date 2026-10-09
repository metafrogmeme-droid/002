"""Run the Playbook's Nautilus strategy (src/strategy.py) locally on the downloaded Bitget data.

Engine label: LOCAL-NAUTILUS-HARNESS. This approximates the managed GetAgent replay
(plain OHLCV bars wrangled with the bar OPEN time as ts_event, 40 days of warmup
bars, funding passed through ``funding_json``) so the strategy class can be
debugged before upload and cross-checked against LOCAL-RESEARCH-ENGINE.

Usage: python3 nautilus_harness.py --start 2024-10-01 --end 2026-10-01 --adx 30 [--no-funding]
"""
from __future__ import annotations

import argparse
import json
import sys
from decimal import Decimal
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
PKG = HERE.parents[1] / "playbooks" / "btc-eth-sol-regime-long"
sys.path.insert(0, str(PKG))

from nautilus_trader.backtest.engine import BacktestEngine, BacktestEngineConfig  # noqa: E402
from nautilus_trader.model.currencies import USDT  # noqa: E402
from nautilus_trader.model.data import BarType  # noqa: E402
from nautilus_trader.model.enums import AccountType, OmsType  # noqa: E402
from nautilus_trader.model.identifiers import InstrumentId, Symbol, Venue  # noqa: E402
from nautilus_trader.model.instruments import CryptoPerpetual  # noqa: E402
from nautilus_trader.model.objects import Money, Price, Quantity  # noqa: E402
from nautilus_trader.persistence.wranglers import BarDataWrangler  # noqa: E402

from src.features import FundingLookup  # noqa: E402
from src.strategy import RegimeLongConfig, RegimeLongStrategy  # noqa: E402

WARMUP = pd.Timedelta(days=40)

SPECS = {
    "BTCUSDT": ("BTC", 1, "0.1", 4, "0.0001"),
    "ETHUSDT": ("ETH", 2, "0.01", 2, "0.01"),
    "SOLUSDT": ("SOL", 3, "0.001", 1, "0.1"),
}


def make_instrument(sym: str) -> CryptoPerpetual:
    from nautilus_trader.model.currencies import Currency
    base, pp, pinc, sp, sinc = SPECS[sym]
    return CryptoPerpetual(
        instrument_id=InstrumentId(Symbol(sym), Venue("BITGET")),
        raw_symbol=Symbol(sym),
        base_currency=Currency.from_str(base),
        quote_currency=USDT,
        settlement_currency=USDT,
        is_inverse=False,
        price_precision=pp,
        size_precision=sp,
        price_increment=Price.from_str(pinc),
        size_increment=Quantity.from_str(sinc),
        margin_init=Decimal("0.2"),
        margin_maint=Decimal("0.01"),
        maker_fee=Decimal("0.0002"),
        taker_fee=Decimal("0.0006"),
        ts_event=0,
        ts_init=0,
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="2024-10-01")
    ap.add_argument("--end", default="2026-10-01")
    ap.add_argument("--adx", type=float, default=30.0)
    ap.add_argument("--no-funding", action="store_true",
                    help="replay without funding data (unknown_funding_policy=allow), like the managed run")
    ap.add_argument("--out", default=str(HERE / "results" / "nautilus_harness.json"))
    args = ap.parse_args()

    start = pd.Timestamp(args.start, tz="UTC")
    end = pd.Timestamp(args.end, tz="UTC")

    engine = BacktestEngine(config=BacktestEngineConfig(trader_id="HARNESS-001"))
    engine.add_venue(venue=Venue("BITGET"), oms_type=OmsType.NETTING, account_type=AccountType.MARGIN,
                     base_currency=USDT, starting_balances=[Money(100_000, USDT)])
    funding, bar_types = {}, []
    for sym in SPECS:
        raw = pd.read_csv(HERE / "data" / f"{sym}_1h.csv")
        raw.index = pd.to_datetime(raw["ts"], unit="ms", utc=True)
        fund = pd.read_csv(HERE / "data" / f"{sym}_funding.csv")
        funding[sym] = FundingLookup(fund["ts"].astype("int64").tolist(), fund["rate"].tolist()).to_dict()
        inst = make_instrument(sym)
        engine.add_instrument(inst)
        bt = BarType.from_str(f"{sym}.BITGET-1-HOUR-LAST-EXTERNAL")
        win = raw.loc[start - WARMUP: end + pd.Timedelta(hours=12)]
        bars = BarDataWrangler(bt, inst).process(win[["open", "high", "low", "close", "volume"]])
        engine.add_data(bars)
        bar_types.append(bt)

    ledger = HERE / "results" / "nautilus_harness_ledger.json"
    strat = RegimeLongStrategy(RegimeLongConfig(
        bar_types=tuple(bar_types), adx_trend_min=args.adx, signal_start_ms=int(start.timestamp() * 1000),
        ledger_path=str(ledger),
        funding_json="" if args.no_funding else json.dumps(funding),
        unknown_funding_policy="allow" if args.no_funding else "block"))
    engine.add_strategy(strat)
    engine.run()
    engine.dispose()

    led = json.loads(ledger.read_text())
    t = pd.DataFrame(led["trades"])
    t = t[t["signal_close_ms"] < int(end.timestamp() * 1000)]
    summary = {"engine": "LOCAL-NAUTILUS-HARNESS", "window": [args.start, args.end], "adx_trend_min": args.adx,
               "funding": "none (unknown allowed)" if args.no_funding else "local Bitget + Binance proxy",
               "trades": int(len(t)), "events": led["events"], "skips": led["skips"],
               "signal_evaluations": led.get("signal_evaluations")}
    if len(t):
        wins, losses = t[t.net_pnl > 0], t[t.net_pnl <= 0]
        summary.update({
            "win_rate": round(len(wins) / len(t), 4),
            "avg_r_gross": round(float(t.r_gross.mean()), 4),
            "net_expectancy_r": round(float(t.r_net.mean()), 4),
            "profit_factor": round(float(wins.net_pnl.sum() / -losses.net_pnl.sum()), 4) if len(losses) else None,
            "net_pnl_usdt": round(float(t.net_pnl.sum()), 2),
            "fees_usdt": round(float(t.fees.sum()), 2),
            "funding_usdt": round(float(t.funding.sum()), 2),
            "exit_reasons": t.exit_reason.value_counts().to_dict(),
        })
    Path(args.out).write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
