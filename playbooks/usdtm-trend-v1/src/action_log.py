"""Per-action log rows for the USDT-M Trend v1 Playbook.

Every live decision emits one JSON row to stdout with the schema
required by the Playbook spec: timestamp, symbol, side, intended vs
filled price, fees, funding, and reason code.
"""

import json
from datetime import datetime, timezone


def log_action(action, symbol, side, intended_price, filled_price,
               fees_usdt, funding_usdt, reason_code, extra=None):
    row = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "symbol": symbol,
        "side": side,
        "intended_price": str(intended_price),
        "filled_price": str(filled_price),
        "fees_usdt": str(fees_usdt),
        "funding_usdt": str(funding_usdt),
        "reason_code": reason_code,
    }
    if extra:
        for key, value in extra.items():
            row[key] = value
    print(json.dumps({"playbook_action_log": row}), flush=True)
    return row
