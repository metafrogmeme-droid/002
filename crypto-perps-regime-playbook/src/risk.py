"""Portfolio and contract risk parameters, limits, and circuit breakers."""

from dataclasses import dataclass
from decimal import Decimal


@dataclass
class RiskLimits:
    risk_per_trade_usdt: float = 15.0
    atr_stop_multiple: float = 1.5
    fixed_tp_r_multiple: float = 2.0
    scale_tp_r_multiple: float = 1.5
    trail_atr_multiple: float = 1.0
    max_concurrent_positions: int = 3
    daily_realised_loss_pause: float = -30.0
    daily_cumulative_loss_halt: float = -40.0
    max_consecutive_losses: int = 5
    max_data_staleness_seconds: int = 60
    max_spread_bps: float = 5.0
    min_volume_24h_usdt: float = 50_000_000.0
    max_funding_cost_r: float = 0.10
    funding_blackout_minutes: int = 15
    limit_cancel_hours: int = 4
    trend_time_stop_hours: int = 8
    mean_rev_time_stop_hours: int = 2


def compute_position_qty(
    entry_price: Decimal,
    stop_distance: Decimal,
    risk_usdt: Decimal = Decimal("15.0"),
    min_trade_num: Decimal = Decimal("0.0001"),
    size_precision: int = 4,
) -> Decimal:
    """Calculate position size: Size = 15 USDT / stop distance, quantized to lot size."""
    if stop_distance <= Decimal("0"):
        return Decimal("0")

    raw_qty = risk_usdt / stop_distance
    # Quantize to size_precision
    step = Decimal("10") ** (-size_precision)
    quantized_qty = (raw_qty // step) * step

    if quantized_qty < min_trade_num:
        return Decimal("0")
    return quantized_qty
