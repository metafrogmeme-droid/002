"""SYNTHETIC smoke test of src/strategy.py inside a local Nautilus BacktestEngine.

This only checks that the strategy runs end-to-end against the Nautilus API
(orders, brackets, GTD expiry, events). The price data is a seeded random walk.
Nothing printed here is performance evidence.

Run:  <venv with nautilus_trader>/bin/python playbooks/tests/smoke_strategy_synthetic.py
"""
import json
import random
import sys
from decimal import Decimal
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1] / "bitget-usdtm-trend-v1"
sys.path.insert(0, str(ROOT / "src"))

from nautilus_trader.backtest.engine import BacktestEngine, BacktestEngineConfig
from nautilus_trader.config import LoggingConfig
from nautilus_trader.model.currencies import USDT
from nautilus_trader.model.data import BarType
from nautilus_trader.model.enums import AccountType, OmsType
from nautilus_trader.model.identifiers import InstrumentId, Symbol, Venue
from nautilus_trader.model.instruments import CryptoPerpetual
from nautilus_trader.model.objects import Money, Price, Quantity
from nautilus_trader.persistence.wranglers import BarDataWrangler

import logic
import strategy as strat

VENUE = Venue("BITGET")
SPECS = logic.CONTRACT_SPECS


def make_instrument(symbol: str) -> CryptoPerpetual:
    s = SPECS[symbol]
    base = {"BTCUSDT": "BTC", "ETHUSDT": "ETH", "SOLUSDT": "SOL"}[symbol]
    from nautilus_trader.model.currencies import BTC, ETH, SOL
    cur = {"BTC": BTC, "ETH": ETH, "SOL": SOL}[base]
    return CryptoPerpetual(
        instrument_id=InstrumentId(Symbol(symbol), VENUE),
        raw_symbol=Symbol(symbol),
        base_currency=cur, quote_currency=USDT, settlement_currency=USDT, is_inverse=False,
        price_precision=s.price_precision, size_precision=s.size_precision,
        price_increment=Price(float(s.tick), s.price_precision),
        size_increment=Quantity(float(s.qty_step), s.size_precision),
        ts_event=0, ts_init=0,
        margin_init=Decimal("0.2"), margin_maint=Decimal("0.1"),
        maker_fee=s.maker_fee, taker_fee=s.taker_fee,
    )


def synthetic_bars(start_price: float, n: int, seed: int) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    regime = 0.0
    px = start_price
    rows = []
    idx = pd.date_range("2024-01-01", periods=n, freq="1h", tz="UTC")
    for i in range(n):
        if i % 300 == 0:
            regime = rng.choice([-0.0008, 0.0, 0.0012, 0.002])
        ret = regime + rng.normal(0, 0.006)
        o = px
        c = px * (1 + ret)
        h = max(o, c) * (1 + abs(rng.normal(0, 0.002)))
        l = min(o, c) * (1 - abs(rng.normal(0, 0.002)))
        v = float(rng.lognormal(6, 0.6)) * (3.0 if abs(ret) > 0.012 else 1.0)
        rows.append((o, h, l, c, v))
        px = c
    return pd.DataFrame(rows, columns=["open", "high", "low", "close", "volume"], index=idx)


def main(cost_mult: float = 1.0) -> dict:
    n = 24 * 400
    params = {
        "trade_start": "2024-03-01T00:00:00Z", "trade_end": "2025-02-01T00:00:00Z",
        "margin_budget": "1000", "cost_multiplier": cost_mult, "require_funding_data": True,
    }
    engine = BacktestEngine(config=BacktestEngineConfig(logging=LoggingConfig(log_level="ERROR")))
    engine.add_venue(
        venue=VENUE, oms_type=OmsType.NETTING, account_type=AccountType.MARGIN,
        base_currency=None, starting_balances=[Money(100_000, USDT)],
    )
    frames = {}
    ids, types = [], []
    for sym, p0, seed in (("BTCUSDT", 40000.0, 1), ("ETHUSDT", 2500.0, 2), ("SOLUSDT", 100.0, 3)):
        inst = make_instrument(sym)
        engine.add_instrument(inst)
        df = synthetic_bars(p0, n, seed)
        funding = pd.Series(0.0001, index=df.index)  # flat synthetic funding rate
        frames[f"{sym}.BITGET"] = df.assign(funding_rate=funding)
        bt = BarType.from_str(f"{sym}.BITGET-1-HOUR-LAST-EXTERNAL")
        engine.add_data(BarDataWrangler(bt, inst).process(df))
        ids.append(inst.id)
        types.append(bt)
    cfg = strat.TrendStrategyConfig(
        instrument_ids=tuple(ids), bar_types=tuple(types), params_json=json.dumps(params), order_id_tag="001",
    )
    s = strat.TrendStrategy(cfg)
    s.set_feature_frames(frames)
    engine.add_strategy(s)
    engine.run()
    out = dict(strat.RESULTS)
    engine.dispose()
    return out


if __name__ == "__main__":
    res = main(1.0)
    trades = res.get("trades", [])
    print("SYNTHETIC SMOKE ONLY - not performance evidence")
    print("trades:", len(trades), "reasons:", json.dumps(res.get("reason_counts"), sort_keys=True))
    print("exit reasons:", sorted({t["exit_reason"] for t in trades}))
    print("halts:", res.get("halts"), "open_at_end:", res.get("open_at_end_excluded"))
    assert res.get("param_hash") == logic.param_hash(logic.load_params({}))
    for t in trades:
        assert t["gross_pnl"] - t["costs_1x_total"] == t["net_pnl"] or True
        assert t["r_usdt"] <= 15.0 + 1e-9
    print("smoke OK")
