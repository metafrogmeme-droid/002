"""Generate upload-ready copies of the Playbook for the validation runs.

The run API accepts no per-run parameter overrides, so each cost / window
variant is a separate package copy that differs ONLY in non-frozen eval keys
(cost_multiplier, trade_start, trade_end). Frozen trading parameters are never
touched, and each copy is checked to keep the same param_hash as v1.

Usage:
  python3 playbooks/tools/make_validation_variants.py --end 2026-10-01 \
      [--months 24] [--out playbooks/_variants] [--chunks 1]

--chunks N (N>1) additionally splits the window into N consecutive time chunks
at cost multiplier 1 (fallback if a full-window run exceeds the sandbox
timeout). Each variant is also written as <name>.tar.gz containing only
README.md, manifest.yaml, backtest.yaml and src/ (docs/ is local-only). Trade ledgers from chunks must be pooled by hand; walk-forward rows
only make sense on the full window.
"""
import argparse
import re
import shutil
import sys
import tarfile
from datetime import datetime, timezone
from pathlib import Path

import yaml

PKG = Path(__file__).resolve().parents[1] / "bitget-usdtm-trend-v1"
sys.path.insert(0, str(PKG / "src"))

import logic  # noqa: E402

KEYS = ("cost_multiplier", "trade_start", "trade_end")


def _set(text: str, key: str, value: str) -> str:
    pat = re.compile(rf"^(\s+{key}:\s*).*$", re.M)
    if len(pat.findall(text)) != 1:
        raise SystemExit(f"manifest key {key!r} must appear exactly once")
    return pat.sub(lambda m: f"{m.group(1)}{value}", text)


def _make(out: Path, name: str, mult: float, start: str, end: str) -> str:
    dest = out / name
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(PKG, dest, ignore=shutil.ignore_patterns("__pycache__", ".state", "output", "docs"))
    mp = dest / "manifest.yaml"
    text = mp.read_text(encoding="utf-8")
    text = _set(text, "cost_multiplier", repr(float(mult)))
    text = _set(text, "trade_start", f'"{start}"')
    text = _set(text, "trade_end", f'"{end}"')
    text = re.sub(r"^name:\s*.*$", f"name: {name}", text, count=1, flags=re.M)
    mp.write_text(text, encoding="utf-8")
    cfg = yaml.safe_load(text)["strategy_config"]
    h = logic.param_hash(logic.load_params(cfg))
    base = yaml.safe_load((PKG / "manifest.yaml").read_text(encoding="utf-8"))["strategy_config"]
    if h != logic.param_hash(logic.load_params(base)):
        raise SystemExit(f"{name}: frozen parameter hash changed - refusing")
    with tarfile.open(out / f"{name}.tar.gz", "w:gz") as tf:
        for item in ("README.md", "manifest.yaml", "backtest.yaml", "src"):
            tf.add(dest / item, arcname=item, filter=lambda ti: None if "__pycache__" in ti.name else ti)
    return h


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--end", required=True, help="pinned UTC end date YYYY-MM-DD (use one date for every variant)")
    ap.add_argument("--months", type=int, default=24)
    ap.add_argument("--out", default=str(PKG.parent / "_variants"))
    ap.add_argument("--chunks", type=int, default=1)
    a = ap.parse_args()
    if a.months < 24:
        raise SystemExit("spec requires >= 24 months")
    end_ms = logic.parse_iso_ms(a.end + "T00:00:00Z")
    start_ms = logic.add_months(end_ms, -a.months)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    s, e = logic.iso(start_ms), logic.iso(end_ms)
    for mult in (0, 1, 2):
        h = _make(out, f"bitget-usdtm-trend-v1-cost{mult}x", mult, s, e)
        print(f"cost{mult}x  {s} -> {e}  hash={h}")
    if a.chunks > 1:
        step = (end_ms - start_ms) // a.chunks // logic.HOUR_MS * logic.HOUR_MS
        for i in range(a.chunks):
            c0 = start_ms + i * step
            c1 = end_ms if i == a.chunks - 1 else c0 + step
            h = _make(out, f"bitget-usdtm-trend-v1-chunk{i + 1}of{a.chunks}", 1, logic.iso(c0), logic.iso(c1))
            print(f"chunk{i + 1}  {logic.iso(c0)} -> {logic.iso(c1)}  hash={h}")
    print("variants written to", out, "(not uploaded; user must upload with their own key)")


if __name__ == "__main__":
    main()
