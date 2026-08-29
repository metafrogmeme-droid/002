#!/usr/bin/env python3
"""Best-effort anonymous telemetry shared by validator and API examples."""

from __future__ import annotations

import json
import os
import platform
import re
import sys
import urllib.request
import uuid
from datetime import UTC, datetime
from pathlib import Path

DEFAULT_URL = "https://api.bitget.com/api/v1/playbook/events"
TIMEOUT_SECONDS = 0.8


def _config_path() -> Path:
    root = os.environ.get("XDG_CONFIG_HOME", "").strip()
    base = Path(root).expanduser() if root else Path.home() / ".config"
    return base / "getagent" / "telemetry.json"


def install_id() -> str:
    if os.environ.get("GETAGENT_TELEMETRY_DISABLED") == "1":
        return ""
    try:
        value = json.loads(_config_path().read_text(encoding="utf-8")).get("install_id", "")
        return str(uuid.UUID(str(value)))
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return ""


def _skill_version() -> str:
    try:
        text = (Path(__file__).resolve().parent.parent / "SKILL.md").read_text(encoding="utf-8")
        match = re.search(r"^\s*version:\s*v?([^\s]+)\s*$", text, re.MULTILINE)
        return match.group(1) if match else ""
    except OSError:
        return ""


def _client_name() -> str:
    path_text = str(Path(__file__).resolve()).lower()
    for client in ("claude", "cursor", "codex"):
        if f".{client}" in path_text:
            return client
    return "unknown"


def report_validation(*, passed: bool, errors: int, warnings: int) -> None:
    anonymous_id = install_id()
    if not anonymous_id or os.environ.get("GETAGENT_TELEMETRY_DISABLED") == "1":
        return
    payload = {
        "event_id": str(uuid.uuid4()),
        "event_name": "skill.validation",
        "install_id": anonymous_id,
        "outcome": "success" if passed else "failure",
        "error_category": "" if passed else "VALIDATION_FAILED",
        "occurred_at": datetime.now(UTC).isoformat(),
        "properties": {
            "client": _client_name(),
            "skill_version": _skill_version(),
            "error_count": max(0, int(errors)),
            "warning_count": max(0, int(warnings)),
            "python": platform.python_version(),
            "os": platform.system().lower(),
        },
    }
    try:
        request = urllib.request.Request(
            os.environ.get("GETAGENT_TELEMETRY_URL", "").strip() or DEFAULT_URL,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            response.read(1)
    except Exception:
        pass


def main() -> None:
    if len(sys.argv) == 2 and sys.argv[1] == "install-id":
        print(install_id())
        return
    raise SystemExit("Usage: telemetry.py install-id")


if __name__ == "__main__":
    main()
