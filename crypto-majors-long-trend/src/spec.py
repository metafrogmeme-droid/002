"""Live Bitget USDT-FUTURES contract facts captured at authoring time.

Values come from public Bitget contract/ticker/funding endpoints on
2026-10-09T18:30:32Z. User-tier fees and bound-subaccount tradability are
not derivable from public data and stay PENDING.
"""

from typing import Any

SPEC_ASOF_UTC = "2026-10-09T18:30:32Z"
PRODUCT_TYPE = "USDT-FUTURES"
CLUSTER = "crypto_majors"
SLEEVE = "A"

# Public contract config + ticker + current-fund-rate (live spec).
CONTRACTS: dict[str, dict[str, Any]] = {
    "BTCUSDT": {
        "symbol_status": "normal",
        "symbol_type": "perpetual",
        "is_rwa": "NO",
        "max_leverage": 150,
        "min_leverage": 1,
        "playbook_leverage_cap": 5,
        "margin_mode_required": "isolated",
        "funding_interval_hours": 8,
        "trading_hours": "24/7",
        "weekend_holiday_close": "none",
        "off_time": "-1",
        "price_place": 1,
        "price_end_step": 1,
        "tick": "0.1",
        "volume_place": 4,
        "min_size": "0.0001",
        "size_multiplier": "0.0001",
        "min_trade_usdt": "5",
        "listed_maker_fee": "0.0002",
        "listed_taker_fee": "0.0006",
        "user_tier_maker_fee": "PENDING",
        "user_tier_taker_fee": "PENDING",
        "last": "82464.2",
        "bid": "82464.1",
        "ask": "82464.2",
        "spread_bps": "0.0121",
        "volume_24h_usdt": "2254548234.79612",
        "funding_rate": "0.000067",
        "next_funding_time_ms": "1791590400000",
        "min_funding_rate": "-0.003",
        "max_funding_rate": "0.003",
    },
    "ETHUSDT": {
        "symbol_status": "normal",
        "symbol_type": "perpetual",
        "is_rwa": "NO",
        "max_leverage": 150,
        "min_leverage": 1,
        "playbook_leverage_cap": 5,
        "margin_mode_required": "isolated",
        "funding_interval_hours": 8,
        "trading_hours": "24/7",
        "weekend_holiday_close": "none",
        "off_time": "-1",
        "price_place": 2,
        "price_end_step": 1,
        "tick": "0.01",
        "volume_place": 2,
        "min_size": "0.01",
        "size_multiplier": "0.01",
        "min_trade_usdt": "5",
        "listed_maker_fee": "0.0002",
        "listed_taker_fee": "0.0006",
        "user_tier_maker_fee": "PENDING",
        "user_tier_taker_fee": "PENDING",
        "last": "2482.92",
        "bid": "2482.92",
        "ask": "2482.93",
        "spread_bps": "0.0403",
        "volume_24h_usdt": "1519602335.0531",
        "funding_rate": "0.00001",
        "next_funding_time_ms": "1791590400000",
        "min_funding_rate": "-0.003",
        "max_funding_rate": "0.003",
    },
    "SOLUSDT": {
        "symbol_status": "normal",
        "symbol_type": "perpetual",
        "is_rwa": "NO",
        "max_leverage": 100,
        "min_leverage": 1,
        "playbook_leverage_cap": 5,
        "margin_mode_required": "isolated",
        "funding_interval_hours": 8,
        "trading_hours": "24/7",
        "weekend_holiday_close": "none",
        "off_time": "-1",
        "price_place": 3,
        "price_end_step": 1,
        "tick": "0.001",
        "volume_place": 1,
        "min_size": "0.1",
        "size_multiplier": "0.1",
        "min_trade_usdt": "5",
        "listed_maker_fee": "0.0002",
        "listed_taker_fee": "0.0006",
        "user_tier_maker_fee": "PENDING",
        "user_tier_taker_fee": "PENDING",
        "last": "109.502",
        "bid": "109.506",
        "ask": "109.507",
        "spread_bps": "0.0913",
        "volume_24h_usdt": "284611362.9502",
        "funding_rate": "0.00007",
        "next_funding_time_ms": "1791590400000",
        "min_funding_rate": "-0.00375",
        "max_funding_rate": "0.00375",
    },
}

UNIVERSE = ("BTCUSDT", "ETHUSDT", "SOLUSDT")
UNIFIED = {
    "BTCUSDT": "BTC/USDT",
    "ETHUSDT": "ETH/USDT",
    "SOLUSDT": "SOL/USDT",
}


def tick_size(symbol: str) -> float:
    return float(CONTRACTS[symbol]["tick"])


def min_size(symbol: str) -> float:
    return float(CONTRACTS[symbol]["min_size"])


def funding_interval_hours(symbol: str) -> int:
    return int(CONTRACTS[symbol]["funding_interval_hours"])


def price_precision(symbol: str) -> int:
    return int(CONTRACTS[symbol]["price_place"])


def size_precision(symbol: str) -> int:
    return int(CONTRACTS[symbol]["volume_place"])
