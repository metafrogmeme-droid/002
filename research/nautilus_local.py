"""Local emulation of the platform replay (backtest.run) to unit-test src/strategy.py with real Nautilus."""
import json, sys, time
from decimal import Decimal
from pathlib import Path
import pandas as pd
sys.path.insert(0, "/workspace/playbooks/crypto-perp-regime-long/src")
import yaml
import rules
from nautilus_trader.backtest.engine import BacktestEngine, BacktestEngineConfig
from nautilus_trader.model.currencies import USDT, BTC, ETH, SOL
from nautilus_trader.model.enums import AccountType, OmsType
from nautilus_trader.model.identifiers import InstrumentId, Symbol, Venue
from nautilus_trader.model.instruments import CryptoPerpetual
from nautilus_trader.model.objects import Money, Price, Quantity, Currency
from nautilus_trader.model.data import BarType
from nautilus_trader.persistence.wranglers import BarDataWrangler
from engine import load
import strategy as strat_mod

START = sys.argv[1] if len(sys.argv) > 1 else "2024-04-01"
END = sys.argv[2] if len(sys.argv) > 2 else "2026-10-10"
mf = yaml.safe_load(open("/workspace/playbooks/crypto-perp-regime-long/manifest.yaml"))["strategy_config"]
mf["margin_cap_usdt"] = mf["margin_budget"]
cfg = rules.Config.from_mapping(mf)
spec = yaml.safe_load(open("/workspace/playbooks/crypto-perp-regime-long/backtest.yaml"))
raw = load(cfg.symbols)
engine = BacktestEngine(config=BacktestEngineConfig())
venue = Venue("BITGET")
engine.add_venue(venue=venue, oms_type=OmsType.NETTING, account_type=AccountType.MARGIN, base_currency=None,
                 starting_balances=[Money(10000, USDT)], default_leverage=Decimal(5))
ccy = {"BTC": BTC, "ETH": ETH, "SOL": SOL}
frames = {}
for ins in spec["instruments"]:
    sym = ins["raw_symbol"]
    iid = InstrumentId.from_str(ins["id"])
    inst = CryptoPerpetual(
        instrument_id=iid, raw_symbol=Symbol(sym), base_currency=ccy[ins["base_currency"]], quote_currency=USDT, settlement_currency=USDT,
        is_inverse=False, price_precision=ins["price_precision"], size_precision=ins["size_precision"],
        price_increment=Price.from_str(ins["price_increment"]), size_increment=Quantity.from_str(ins["size_increment"]),
        margin_init=Decimal("0.2"), margin_maint=Decimal("0.1"), maker_fee=Decimal(ins["maker_fee"]), taker_fee=Decimal(ins["taker_fee"]),
        ts_event=0, ts_init=0,
    )
    engine.add_instrument(inst)
    d = raw[sym].loc[START:END]
    ind = rules.compute_indicators(raw[sym], cfg); sig = rules.compute_signals(ind, cfg)
    f = d.copy()
    f["atr"] = sig["atr"].loc[f.index].bfill().fillna(0.0); f["quote_vol_24h"] = sig["quote_vol_24h"].loc[f.index].bfill().fillna(0.0)
    for c in ("sig_trend", "sig_mr", "sig_break"):
        f[c] = sig[c].loc[f.index].astype(float)
    frames[ins["id"]] = f
    bt = BarType.from_str(ins["bar_type"])
    wr = BarDataWrangler(bt, inst)
    engine.add_data(wr.process(f[["open", "high", "low", "close", "volume"]]))
scfg = strat_mod.RegimeLongStrategyConfig(order_id_tag="001", symbols=tuple(cfg.symbols), venue="BITGET", rules_json=json.dumps(mf),
                                          tick_json=json.dumps({s: {"tick": t["tick"], "step": t["step"], "min_qty": t["min_qty"]} for s, t in
                                                                {"BTCUSDT": dict(tick=0.1, step=0.0001, min_qty=0.0001), "ETHUSDT": dict(tick=0.01, step=0.01, min_qty=0.01), "SOLUSDT": dict(tick=0.001, step=0.1, min_qty=0.1)}.items()}),
                                          enforce_halts=False)
s = strat_mod.RegimeLongStrategy(scfg)

engine.add_strategy(s)
t = time.time(); engine.run(); print("run secs", round(time.time() - t, 1))
pos = engine.trader.generate_positions_report()
fills = engine.trader.generate_order_fills_report()
print("positions", len(pos), "fills", len(fills))
if len(pos):
    pnl = pos["realized_pnl"].astype(str).str.split().str[0].astype(float)
    print("net pnl (nautilus, incl commissions, no funding):", round(pnl.sum(), 2), "win rate", round((pnl > 0).mean(), 3), "PF", round(pnl[pnl > 0].sum() / -pnl[pnl <= 0].sum(), 3))
    print(pos[["instrument_id", "entry", "ts_opened", "ts_closed", "avg_px_open", "avg_px_close", "realized_pnl"]].head(8).to_string())
    pos.to_csv("out/nautilus_local_positions.csv")
