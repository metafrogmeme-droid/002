"""Execution helpers for liquidity checks, funding gates, and order placement."""

from decimal import Decimal
from typing import Any, Dict, Tuple


def check_liquidity_gate(
    bid: float,
    ask: float,
    volume_24h_usdt: float,
    max_spread_bps: float = 5.0,
    min_volume_24h_usdt: float = 50_000_000.0,
) -> Tuple[bool, str]:
    """Verify market passes spread (<5 bps) and 24h volume (>$50M) liquidity gates."""
    if bid <= 0 or ask <= 0:
        return False, "invalid_bid_ask"

    mid = (bid + ask) / 2.0
    spread_bps = ((ask - bid) / mid) * 10_000.0

    if spread_bps > max_spread_bps:
        return False, f"spread_exceeded_{spread_bps:.2f}_bps"

    if volume_24h_usdt < min_volume_24h_usdt:
        return False, f"volume_below_threshold_{volume_24h_usdt:.0f}_usdt"

    return True, "liquidity_gate_passed"


def check_funding_gate(
    current_time_ms: int,
    funding_interval_hours: int = 8,
    funding_rate: float = 0.0,
    expected_hold_hours: int = 8,
    risk_r_usdt: float = 15.0,
    position_notional_usdt: float = 100.0,
    max_funding_drag_r: float = 0.10,
) -> Tuple[bool, str]:
    """Verify not within ±15 min of funding settlement and expected funding < 0.1R."""
    # Funding settlement timestamps are typically at 00:00, 08:00, 16:00 UTC
    interval_ms = funding_interval_hours * 3600 * 1000
    mod_ms = current_time_ms % interval_ms
    fifteen_min_ms = 15 * 60 * 1000

    # Near settlement?
    if mod_ms <= fifteen_min_ms or mod_ms >= (interval_ms - fifteen_min_ms):
        return False, "funding_settlement_blackout_window"

    # Expected funding cost calculation
    intervals_in_hold = max(1, expected_hold_hours // funding_interval_hours)
    expected_funding_cost_usdt = position_notional_usdt * abs(funding_rate) * intervals_in_hold
    max_allowed_cost = risk_r_usdt * max_funding_drag_r

    if expected_funding_cost_usdt > max_allowed_cost:
        return False, f"funding_cost_{expected_funding_cost_usdt:.2f}_exceeds_0.1R"

    return True, "funding_gate_passed"
