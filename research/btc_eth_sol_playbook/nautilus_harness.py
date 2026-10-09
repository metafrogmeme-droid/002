"""Run the Playbook's Nautilus strategy (src/strategy.py) locally on the downloaded Bitget data.

Engine label: LOCAL-NAUTILUS-HARNESS. This approximates the managed GetAgent replay
(bars wrangled with the bar OPEN time as ts_event, feature frames injected via
``set_feature_frames``) so the strategy class can be debugged before upload and
cross-checked against LOCAL-RESEARCH-ENGINE.

Usage: python3 nautilus_harness.py --start 2024-10-01 --end 2026-10-01 --adx 25
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

from src.features import attach_replay_columns, compute_indicators, compute_signals  # noqa: E402
from src.strategy import RegimeLongConfig, RegimeLongStrategy  # noqa: E402

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
    ap.add_argument("--adx", type=float, default=25.0)
    ap.add_argument("--out", default=str(HERE / "results" / "nautilus_harness.json"))
    args = ap.parse_args()

    start = pd.Timestamp(args.start, tz="UTC")
    end = pd.Timestamp(args.end, tz="UTC")
    cfg = {"base_strategy": "ema_adx_trend", "adx_trend_min": args.adx}

    engine = BacktestEngine(config=BacktestEngineConfig(trader_id="HARNESS-001"))
    engine.add_venue(venue=Venue("BITGET"), oms_type=OmsType.NETTING, account_type=AccountType.MARGIN,
                     base_currency=USDT, starting_balances=[Money(100_000, USDT)])
    frames, bar_types = {}, []
    for sym in SPECS:
        raw = pd.read_csv(HERE / "data" / f"{sym}_1h.csv")
        raw.index = pd.to_datetime(raw["ts"], unit="ms", utc=True)
        fund = pd.read_csv(HERE / "data" / f"{sym}_funding.csv")
        fser = pd.Series(fund["rate"].to_numpy(), index=pd.to_datetime(fund["ts"], unit="ms", utc=True))
        sig = compute_signals(compute_indicators(raw, cfg), cfg)
        frame = attach_replay_columns(sig, fser)
        inst = make_instrument(sym)
        engine.add_instrument(inst)
        bt = BarType.from_str(f"{sym}.BITGET-1-HOUR-LAST-EXTERNAL")
        win = frame.loc[start - pd.Timedelta(hours=1): end + pd.Timedelta(hours=12)]
        bars = BarDataWrangler(bt, inst).process(win[["open", "high", "low", "close", "volume"]])
        engine.add_data(bars)
        frames[f"{sym}.BITGET"] = frame
        bar_types.append(bt)

    ledger = HERE / "results" / "nautilus_harness_ledger.json"
    strat = RegimeLongStrategy(RegimeLongConfig(
        bar_types=tuple(bar_types), signal_start_ms=int(start.timestamp() * 1000),
        ledger_path=str(ledger)))
    strat.set_feature_frames(frames)
    engine.add_strategy(strat)
    engine.run()
    engine.dispose()

    led = json.loads(ledger.read_text())
    t = pd.DataFrame(led["trades"])
    t = t[t["signal_close_ms"] < int(end.timestamp() * 1000)]
    summary = {"engine": "LOCAL-NAUTILUS-HARNESS", "window": [args.start, args.end], "adx_trend_min": args.adx,
               "trades": int(len(t)), "events": led["events"], "skips": led["skips"],
               "ts_shift_ms": led.get("ts_shift_ms")}
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
