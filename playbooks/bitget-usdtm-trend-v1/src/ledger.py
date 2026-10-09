"""Persistent Playbook ledger (``.state/``) and per-run structured action log.

``.state/`` is the only path the sandbox may persist between runs. If the
runner does not hydrate it, the ledger is empty on every run and the foreign
position check fails CLOSED (no new entries) rather than guessing ownership.
"""
import json
from pathlib import Path
from typing import Any, Optional

try:
    from . import logic
except ImportError:  # loaded as a top-level module
    import logic  # type: ignore[no-redef]

STATE_PATH = Path(".state") / "ledger.json"
OUTPUT_DIR = Path("output")


class Ledger:
    def __init__(self, data: Optional[dict[str, Any]] = None, loaded: bool = False) -> None:
        self.data: dict[str, Any] = data or {"version": 1, "owned": {}, "last_bar_ms": {}, "latch": None, "closed": []}
        self.loaded = loaded

    @classmethod
    def load(cls) -> "Ledger":
        try:
            return cls(json.loads(STATE_PATH.read_text(encoding="utf-8")), loaded=True)
        except (OSError, ValueError):
            return cls(None, loaded=False)

    def save(self) -> bool:
        try:
            STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
            self.data["closed"] = self.data.get("closed", [])[-50:]
            STATE_PATH.write_text(json.dumps(self.data, default=str), encoding="utf-8")
            return True
        except OSError:
            return False

    @property
    def owned(self) -> dict[str, dict[str, Any]]:
        return self.data.setdefault("owned", {})

    @property
    def last_bar_ms(self) -> dict[str, int]:
        return self.data.setdefault("last_bar_ms", {})


class RunLog:
    """Collects structured action records; prints compact JSON lines for the runner."""

    def __init__(self) -> None:
        self.records: list[dict[str, Any]] = []
        self.counts: dict[str, int] = {}

    def add(self, ts_ms: int, symbol: str, action: str, reason: "logic.ReasonCode", *, echo: bool = True, **kw: Any) -> dict[str, Any]:
        rec = logic.make_log(ts_ms, symbol, action, reason, **kw)
        self.records.append(rec)
        self.counts[reason.value] = self.counts.get(reason.value, 0) + 1
        if echo:
            print(json.dumps(rec, default=str, separators=(",", ":")))
        return rec

    def flush(self) -> None:
        try:
            OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
            (OUTPUT_DIR / "playbook_actions.json").write_text(
                json.dumps({"fields": list(logic.LOG_FIELDS), "records": self.records}, default=str),
                encoding="utf-8",
            )
        except OSError:
            pass
