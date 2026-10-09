"""Print the v1 frozen-parameter hash (same function the Playbook uses).

Usage: python3 playbooks/tools/param_hash.py
"""
import json
import sys
from pathlib import Path

import yaml

PKG = Path(__file__).resolve().parents[1] / "bitget-usdtm-trend-v1"
sys.path.insert(0, str(PKG / "src"))

import logic  # noqa: E402


def main() -> None:
    manifest = yaml.safe_load((PKG / "manifest.yaml").read_text(encoding="utf-8"))
    params = logic.load_params(manifest["strategy_config"])
    print(json.dumps(dict(params.frozen), sort_keys=True, indent=2, default=str))
    print("param_hash:", logic.param_hash(params))


if __name__ == "__main__":
    main()
