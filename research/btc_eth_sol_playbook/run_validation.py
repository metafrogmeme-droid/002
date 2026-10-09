"""Walk-forward validation for the BTC/ETH/SOL regime Playbook (LOCAL-RESEARCH-ENGINE).

Protocol (fixed before looking at out-of-sample results):
  Stage 1 - base selection, train only (2023-10-01 .. 2024-10-01):
      regime time shares per symbol + both candidate bases (EMA-ADX trend,
      mean reversion), long-only, default thresholds, 1x costs. Pick the base
      with the higher train net expectancy (>= 30 trades required).
  Stage 2 - rolling walk-forward, train 12 months / test 6 months, step 6 months.
      Only ONE parameter is fitted per fold: the regime ADX threshold of the
      selected base (trend: adx_trend_min in {20, 25, 30}; mean reversion:
      adx_range_max in {15, 20, 25}), chosen by train net expectancy with
      >= 30 train trades (ties / too few trades -> spec default).
      Test windows: 2024-10-01 .. 2026-10-01 (24 months, stitched).
  Stage 3 - cost sensitivity 0x / 1x / 2x on the stitched out-of-sample run.
  Stage 4 - short-side test: mirror signals, same folds and fitted thresholds.
  Stage 5 - v1 freeze: refit the threshold on the most recent 12 months.

Usage:  python3 run_validation.py   (after fetch_data.py)
Writes: results/validation_results.json, results/validation_report.md, results/oos_trades.csv
"""
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import pandas as pd

from engine import SIM_DEFAULTS, metrics, prepare, simulate

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
OUT = HERE / "results"
SYMBOLS = ("BTCUSDT", "ETHUSDT", "SOLUSDT")

BASE_TREND = "ema_adx_trend"
BASE_MR = "mean_reversion"
GRID = {BASE_TREND: ("adx_trend_min", (20.0, 25.0, 30.0), 25.0),
        BASE_MR: ("adx_range_max", (15.0, 20.0, 25.0), 20.0)}
TIME_STOP = {BASE_TREND: 8, BASE_MR: 2}

STAGE1 = ("2023-10-01", "2024-10-01")
FOLDS = [
    (("2023-10-01", "2024-10-01"), ("2024-10-01", "2025-04-01")),
    (("2024-04-01", "2025-04-01"), ("2025-04-01", "2025-10-01")),
    (("2024-10-01", "2025-10-01"), ("2025-10-01", "2026-04-01")),
    (("2025-04-01", "2026-04-01"), ("2026-04-01", "2026-10-01")),
]
FREEZE_TRAIN = ("2025-10-01", "2026-10-01")


def ms(d: str) -> int:
    return int(pd.Timestamp(d, tz="UTC").timestamp() * 1000)


def load() -> tuple[dict[str, pd.DataFrame], dict[str, pd.DataFrame]]:
    raw, fund = {}, {}
    for s in SYMBOLS:
        raw[s] = pd.read_csv(DATA / f"{s}_1h.csv")
        fund[s] = pd.read_csv(DATA / f"{s}_funding.csv")
    return raw, fund


def clean(obj: Any) -> Any:
    if isinstance(obj, float):
        return None if not math.isfinite(obj) else round(obj, 4)
    if isinstance(obj, dict):
        return {str(k): clean(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [clean(v) for v in obj]
    return obj


class Runner:
    def __init__(self) -> None:
        self.raw, self.fund = load()
        self._cache: dict[tuple, dict[str, pd.DataFrame]] = {}

    def frames(self, base: str, thr: float) -> dict[str, pd.DataFrame]:
        key = (base, thr)
        if key not in self._cache:
            name, _, _ = GRID[base]
            self._cache[key] = prepare(self.raw, {"base_strategy": base, name: thr})
        return self._cache[key]

    def run(self, base: str, thr: float, window: tuple[str, str], sides=("long",), cost_mult=1.0):
        params = {"time_stop_hours": TIME_STOP[base]}
        return simulate(self.frames(base, thr), self.fund, ms(window[0]), ms(window[1]),
                        sides=sides, cost_mult=cost_mult, params=params)


def regime_shares(frames: dict[str, pd.DataFrame], window: tuple[str, str]) -> dict[str, dict[str, float]]:
    out = {}
    for s, f in frames.items():
        w = f[(f.index >= ms(window[0])) & (f.index < ms(window[1]))]
        out[s] = {k: float(v) for k, v in w["regime"].value_counts(normalize=True).items()}
    return out


def fit_threshold(r: Runner, base: str, train: tuple[str, str], sides=("long",)) -> dict[str, Any]:
    name, grid, default = GRID[base]
    rows = []
    for thr in grid:
        m = metrics(r.run(base, thr, train, sides=sides))
        rows.append({"value": thr, "trades": m["trades"], "net_expectancy_r": m.get("net_expectancy_r")})
    eligible = [x for x in rows if x["trades"] >= 30 and x["net_expectancy_r"] is not None]
    if eligible:
        best = max(eligible, key=lambda x: (round(x["net_expectancy_r"], 6), x["value"] == default))
        chosen = best["value"]
    else:
        chosen = default
    return {"param": name, "chosen": chosen, "grid": rows}


def stitched(r: Runner, base: str, fold_fits: list[dict], sides=("long",), cost_mult=1.0):
    parts, trades, events, skips, daily = [], [], {}, {}, []
    for (train, test), fit in zip(FOLDS, fold_fits):
        res = r.run(base, fit["chosen"], test, sides=sides, cost_mult=cost_mult)
        parts.append({"test": test, "param_value": fit["chosen"], **metrics(res)})
        if len(res.trades):
            trades.append(res.trades)
        for k, v in res.events.items():
            events[k] = events.get(k, 0) + v
        for k, v in res.skips.items():
            skips[k] = skips.get(k, 0) + v
        daily.append(res.daily_pnl)
    from engine import SimResult
    all_trades = pd.concat(trades, ignore_index=True) if trades else pd.DataFrame()
    combined = SimResult(all_trades, events, skips, pd.concat(daily), ms(FOLDS[0][1][0]), ms(FOLDS[-1][1][1]),
                         dict(SIM_DEFAULTS))
    return metrics(combined), parts, all_trades


def main() -> None:
    OUT.mkdir(exist_ok=True)
    r = Runner()
    results: dict[str, Any] = {
        "engine": "LOCAL-RESEARCH-ENGINE (research/btc_eth_sol_playbook/engine.py)",
        "data": json.loads((DATA / "data_manifest.json").read_text()),
        "cost_model": {
            "maker_fee": SIM_DEFAULTS["maker_fee"], "taker_fee": SIM_DEFAULTS["taker_fee"],
            "slippage_ticks": SIM_DEFAULTS["slippage_ticks"],
            "funding": "charged per settlement; Bitget history where available, Binance archive proxy before",
            "cost_multiplier_scales": "fees, slippage and funding together",
        },
        "risk_model": {k: SIM_DEFAULTS[k] for k in (
            "risk_per_trade_usdt", "max_leverage", "margin_budget", "max_concurrent", "stop_atr_mult",
            "tp_r_multiple", "entry_ttl_hours", "daily_pause_usdt", "daily_stop_usdt",
            "max_consecutive_losses", "funding_block_minutes", "funding_max_against")},
        "sharpe_definition": "daily realised PnL / margin_budget (1500 USDT), mean/std * sqrt(365), "
                             "calendar days incl. zero-PnL days",
    }

    # Stage 1
    stage1 = {"window": STAGE1, "regime_shares": regime_shares(r.frames(BASE_TREND, 25.0), STAGE1), "candidates": {}}
    for base in (BASE_TREND, BASE_MR):
        _, _, default = GRID[base]
        stage1["candidates"][base] = metrics(r.run(base, default, STAGE1))
    elig = {b: m for b, m in stage1["candidates"].items() if m["trades"] >= 30}
    if elig:
        chosen = max(elig, key=lambda b: elig[b]["net_expectancy_r"])
    else:
        chosen = BASE_TREND
    stage1["chosen_base"] = chosen
    results["stage1_base_selection"] = stage1
    print("stage1", chosen, {b: (m["trades"], m.get("net_expectancy_r")) for b, m in stage1["candidates"].items()})

    # Stage 2
    fits = [fit_threshold(r, chosen, train) for train, _ in FOLDS]
    oos, parts, oos_trades = stitched(r, chosen, fits)
    results["stage2_walk_forward"] = {
        "folds": [{"train": tr, "test": te, "fit": f} for (tr, te), f in zip(FOLDS, fits)],
        "per_fold_oos": parts,
        "oos_stitched_1x": oos,
    }
    oos_trades.to_csv(OUT / "oos_trades.csv", index=False)
    print("oos", oos["trades"], oos.get("net_expectancy_r"), oos.get("profit_factor"))

    # Also report the other base out-of-sample (transparency, not used for selection)
    other = BASE_MR if chosen == BASE_TREND else BASE_TREND
    other_fits = [fit_threshold(r, other, train) for train, _ in FOLDS]
    other_oos, _, _ = stitched(r, other, other_fits)
    results["transparency_other_base_oos_1x"] = {"base": other, "fits": [f["chosen"] for f in other_fits],
                                                 "oos": other_oos}

    # Stage 3
    sweep = {}
    for cm in (0.0, 1.0, 2.0):
        m, _, _ = stitched(r, chosen, fits, cost_mult=cm)
        sweep[f"{cm:g}x"] = m
    results["stage3_cost_sensitivity"] = sweep
    print("sweep", {k: (v["trades"], v.get("net_expectancy_r")) for k, v in sweep.items()})

    # Stage 4: short side
    short_fits = [fit_threshold(r, chosen, train, sides=("short",)) for train, _ in FOLDS]
    short_oos, short_parts, _ = stitched(r, chosen, short_fits, sides=("short",))
    short_full = metrics(r.run(chosen, GRID[chosen][2], ("2023-10-01", "2026-10-01"), sides=("short",)))
    results["stage4_short_side"] = {"fits": [f["chosen"] for f in short_fits], "oos_stitched_1x": short_oos,
                                    "per_fold_oos": short_parts, "full_3y_default_threshold_1x": short_full}
    print("short", short_oos["trades"], short_oos.get("net_expectancy_r"))

    # Reference: full 3y with defaults (not out-of-sample for the base choice)
    results["reference_full_3y_default_long_1x"] = metrics(r.run(chosen, GRID[chosen][2], ("2023-10-01", "2026-10-01")))

    # Stage 5
    freeze = fit_threshold(r, chosen, FREEZE_TRAIN)
    results["stage5_v1_freeze"] = {"train": FREEZE_TRAIN, **freeze}

    # Section 6 verdict
    v = {}
    v["trades_ge_30"] = oos["trades"] >= 30
    v["net_expectancy_1x_positive"] = (oos.get("net_expectancy_r") or -1) > 0
    v["net_expectancy_2x_positive"] = (sweep["2x"].get("net_expectancy_r") or -1) > 0
    if not v["trades_ge_30"]:
        v["verdict"] = "NO VERDICT (<30 trades)"
    elif not v["net_expectancy_2x_positive"]:
        v["verdict"] = "REJECT (negative net expectancy at 2x costs)"
    elif not v["net_expectancy_1x_positive"]:
        v["verdict"] = "REJECT (negative net expectancy at 1x costs)"
    else:
        v["verdict"] = "ELIGIBLE FOR FORWARD TEST (backtest gates passed; forward PASS/FAIL criteria still apply)"
    v["shorts_enabled"] = bool(short_oos["trades"] >= 30 and (short_oos.get("net_expectancy_r") or -1) > 0)
    results["section6_verdict"] = v
    print("verdict", v)

    cleaned = clean(results)
    (OUT / "validation_results.json").write_text(json.dumps(cleaned, indent=2))
    (OUT / "validation_report.md").write_text(render_report(cleaned))


def _fmt(v: Any, nd: int = 3) -> str:
    if v is None:
        return "n/a"
    if isinstance(v, float):
        return f"{v:.{nd}f}"
    return str(v)


def _row(label: str, m: dict[str, Any]) -> str:
    return (f"| {label} | {m['trades']} | {_fmt(m.get('win_rate'))} | {_fmt(m.get('avg_r_gross'))} | "
            f"{_fmt(m.get('net_expectancy_r'))} | {_fmt(m.get('profit_factor'))} | "
            f"{_fmt(m.get('max_dd_usdt'), 1)} ({_fmt(m.get('max_dd_r'), 1)}R) | {_fmt(m.get('sharpe_daily_ann'), 2)} | "
            f"{_fmt(m.get('net_pnl_usdt'), 1)} |")


def render_report(r: dict[str, Any]) -> str:
    hdr = ("| Run | Trades | Win rate | Avg R (gross) | Net expectancy (R) | PF | Max DD USDT (R) | Sharpe | Net PnL USDT |\n"
           "|---|---|---|---|---|---|---|---|---|")
    s1 = r["stage1_base_selection"]
    wf = r["stage2_walk_forward"]
    lines = [
        "# Validation report - LOCAL-RESEARCH-ENGINE",
        "",
        "Generated by `research/btc_eth_sol_playbook/run_validation.py`. All figures are NET of",
        "maker 0.02% / taker 0.06% fees, 1-tick slippage on taker fills, and funding, unless the",
        "row says 0x. Data: Bitget USDT-M 1H candles; funding = Bitget history for the last ~90 days,",
        "Binance USDT-M archive as a proxy before that. Sharpe = " + r["sharpe_definition"] + ".",
        "",
        "## Stage 1 - base selection (train only, " + " .. ".join(s1["window"]) + ")",
        "",
        "Regime time share (fraction of 1H bars):",
        "",
        "| Symbol | TREND | RANGE | SIT_OUT |",
        "|---|---|---|---|",
    ]
    for sym, sh in s1["regime_shares"].items():
        lines.append(f"| {sym} | {_fmt(sh.get('TREND'))} | {_fmt(sh.get('RANGE'))} | {_fmt(sh.get('SIT_OUT'))} |")
    lines += ["", hdr]
    for b, m in s1["candidates"].items():
        lines.append(_row(f"{b} long, default threshold (train)", m))
    lines += ["", f"Chosen base: **{s1['chosen_base']}**", "",
              "## Stage 2 - walk-forward (train 12m / test 6m, step 6m)", "",
              "| Train | Test | Fitted param | Grid (value: train trades / net exp R) |", "|---|---|---|---|"]
    for f in wf["folds"]:
        grid = "; ".join(f"{g['value']}: {g['trades']} / {_fmt(g['net_expectancy_r'])}" for g in f["fit"]["grid"])
        lines.append(f"| {' .. '.join(f['train'])} | {' .. '.join(f['test'])} | "
                     f"{f['fit']['param']}={f['fit']['chosen']} | {grid} |")
    lines += ["", "Out-of-sample per fold (1x costs):", "", hdr]
    for pf in wf["per_fold_oos"]:
        lines.append(_row(" .. ".join(pf["test"]), pf))
    lines.append(_row("**Stitched OOS 24m**", wf["oos_stitched_1x"]))
    o = wf["oos_stitched_1x"]
    lines += ["", f"Exit reasons: {o.get('exit_reasons')}", f"By symbol: {o.get('by_symbol')}",
              f"Risk events (simulated as next-day resume): {o.get('events')}",
              f"Skipped signals: {o.get('skips')}",
              f"Cost breakdown USDT: fees {_fmt(o.get('fees_usdt'), 1)}, slippage {_fmt(o.get('slippage_usdt'), 1)}, "
              f"funding {_fmt(o.get('funding_usdt'), 1)}; gross {_fmt(o.get('gross_pnl_usdt'), 1)}",
              "", "## Stage 3 - cost sensitivity (stitched OOS)", "", hdr]
    for k, m in r["stage3_cost_sensitivity"].items():
        lines.append(_row(f"costs {k}", m))
    s4 = r["stage4_short_side"]
    tb = r["transparency_other_base_oos_1x"]
    lines += ["", "## Stage 4 - short-side test", "", hdr,
              _row(f"short, walk-forward OOS 24m (fits {s4['fits']})", s4["oos_stitched_1x"]),
              _row("short, full 3y, default threshold (reference)", s4["full_3y_default_threshold_1x"]),
              "", "## Transparency - other base, same walk-forward (not used for selection)", "", hdr,
              _row(f"{tb['base']} long OOS 24m (fits {tb['fits']})", tb["oos"]),
              "", "## Reference - selected base, full 3y, default threshold (NOT out-of-sample)", "", hdr,
              _row("long, 2023-10-01 .. 2026-10-01", r["reference_full_3y_default_long_1x"]),
              "", "## Stage 5 - v1 freeze", "",
              f"Refit on {' .. '.join(r['stage5_v1_freeze']['train'])}: "
              f"{r['stage5_v1_freeze']['param']} = {r['stage5_v1_freeze']['chosen']} "
              f"(grid {r['stage5_v1_freeze']['grid']})",
              "", "## Section 6 verdict", "", "```", json.dumps(r["section6_verdict"], indent=2), "```", ""]
    return "\n".join(lines)


if __name__ == "__main__":
    main()
