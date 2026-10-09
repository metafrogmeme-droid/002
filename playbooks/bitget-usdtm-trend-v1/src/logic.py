"""Pure, dependency-free strategy logic for the Bitget USDT-M trend Playbook.

Nothing in this module imports ``getagent`` or ``nautilus_trader``. It can be
imported and unit-tested with plain Python. All timestamps are integer
milliseconds since the Unix epoch (UTC).
"""
import json
import math
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from decimal import ROUND_CEILING, ROUND_FLOOR, Decimal
from enum import Enum
from typing import Any, Iterable, Mapping, Optional

HOUR_MS = 3_600_000
MINUTE_MS = 60_000
DAY_MS = 24 * HOUR_MS


class ReasonCode(str, Enum):
    """Stable reason codes attached to every structured log record."""

    # Entry lifecycle
    SIGNAL_LONG_ENTRY = "SIGNAL_LONG_ENTRY"
    ORDER_PLACED = "ORDER_PLACED"
    ORDER_FILLED = "ORDER_FILLED"
    ORDER_REJECTED = "ORDER_REJECTED"
    ORDER_EXPIRED_UNFILLED = "ORDER_EXPIRED_UNFILLED"
    ORDER_CANCELLED_FUNDING_WINDOW = "ORDER_CANCELLED_FUNDING_WINDOW"
    # Exits
    EXIT_STOP_LOSS = "EXIT_STOP_LOSS"
    EXIT_TAKE_PROFIT = "EXIT_TAKE_PROFIT"
    EXIT_TIME_STOP = "EXIT_TIME_STOP"
    EXIT_UNKNOWN = "EXIT_UNKNOWN"
    EXIT_FORCED_END_OF_TEST = "EXIT_FORCED_END_OF_TEST"
    # Evaluated, no trade
    NO_SIGNAL = "NO_SIGNAL"
    REGIME_WARMUP = "REGIME_WARMUP"
    REGIME_ADX_LOW = "REGIME_ADX_LOW"
    REGIME_ATR_PCT_LOW = "REGIME_ATR_PCT_LOW"
    REGIME_ATR_PCT_HIGH = "REGIME_ATR_PCT_HIGH"
    NO_TRADE_FUNDING_WINDOW = "NO_TRADE_FUNDING_WINDOW"
    SKIP_FUNDING_RATE_ADVERSE = "SKIP_FUNDING_RATE_ADVERSE"
    SKIP_FUNDING_UNAVAILABLE = "SKIP_FUNDING_UNAVAILABLE"
    SKIP_VOLUME_NOT_CONFIRMED = "SKIP_VOLUME_NOT_CONFIRMED"
    SKIP_MAX_CONCURRENT = "SKIP_MAX_CONCURRENT"
    SKIP_SYMBOL_OCCUPIED = "SKIP_SYMBOL_OCCUPIED"
    SKIP_BELOW_MIN_QTY = "SKIP_BELOW_MIN_QTY"
    SKIP_INVALID_STOP = "SKIP_INVALID_STOP"
    SKIP_LEVERAGE_CAP = "SKIP_LEVERAGE_CAP"
    SKIP_MARGIN_INSUFFICIENT = "SKIP_MARGIN_INSUFFICIENT"
    SKIP_SIGNAL_STALE = "SKIP_SIGNAL_STALE"
    SKIP_ALREADY_EVALUATED = "SKIP_ALREADY_EVALUATED"
    SKIP_CONFIG_MISMATCH = "SKIP_CONFIG_MISMATCH"
    SKIP_SL_NOT_ATTACHED = "SKIP_SL_NOT_ATTACHED"
    # Pauses and halts (entries only; positions are never flattened)
    PAUSE_DAILY_LOSS = "PAUSE_DAILY_LOSS"
    HALT_DAILY_LOSS_STOP = "HALT_DAILY_LOSS_STOP"
    HALT_CONSEC_LOSSES = "HALT_CONSEC_LOSSES"
    HALT_STALE_DATA = "HALT_STALE_DATA"
    HALT_FOREIGN_POSITION = "HALT_FOREIGN_POSITION"
    HALT_PNL_UNAVAILABLE = "HALT_PNL_UNAVAILABLE"
    HALT_STATE_UNAVAILABLE = "HALT_STATE_UNAVAILABLE"
    HALT_MARGIN_MODE_MISMATCH = "HALT_MARGIN_MODE_MISMATCH"
    HALT_DATA_ERROR = "HALT_DATA_ERROR"
    RESUME_SIMULATED_MANUAL_RESET = "RESUME_SIMULATED_MANUAL_RESET"


class ConfigError(ValueError):
    pass


# ---------------------------------------------------------------------------
# Contract specifications
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ContractSpec:
    symbol: str
    tick: Decimal
    qty_step: Decimal
    min_qty: Decimal
    min_notional_usdt: Decimal
    price_precision: int
    size_precision: int
    maker_fee: Decimal
    taker_fee: Decimal
    fund_interval_hours: int


# Source: GET https://api.bitget.com/api/v2/mix/market/contracts
#   ?productType=USDT-FUTURES&symbol=<SYMBOL>   (code 00000, symbolStatus normal)
# tick = 10^-pricePlace (priceEndStep=1); qty_step = sizeMultiplier;
# min_qty = minTradeNum; min_notional = minTradeUSDT. Fee rates are the
# public *default-tier* makerFeeRate/takerFeeRate, NOT the user's tier.
CONTRACT_SPECS: dict[str, ContractSpec] = {
    "BTCUSDT": ContractSpec("BTCUSDT", Decimal("0.1"), Decimal("0.0001"), Decimal("0.0001"),
                            Decimal("5"), 1, 4, Decimal("0.0002"), Decimal("0.0006"), 8),
    "ETHUSDT": ContractSpec("ETHUSDT", Decimal("0.01"), Decimal("0.01"), Decimal("0.01"),
                            Decimal("5"), 2, 2, Decimal("0.0002"), Decimal("0.0006"), 8),
    "SOLUSDT": ContractSpec("SOLUSDT", Decimal("0.001"), Decimal("0.1"), Decimal("0.1"),
                            Decimal("5"), 3, 1, Decimal("0.0002"), Decimal("0.0006"), 8),
}


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------

# Strategy parameters that define "v1". Changing any of them means a new version.
FROZEN_DEFAULTS: dict[str, Any] = {
    "symbols": ["BTCUSDT", "ETHUSDT", "SOLUSDT"],
    "timeframe": "1h",
    "ema_fast": 20,
    "ema_slow": 50,
    "adx_period": 14,
    "adx_min": 25.0,
    "atr_period": 14,
    "atr_pct_lookback_bars": 2160,
    "atr_pct_min_history_bars": 500,
    "atr_pct_rank_low": 20.0,
    "atr_pct_rank_high": 90.0,
    "volume_lookback_bars": 20,
    "volume_mult": 1.5,
    "entry_offset_atr": 0.0,
    "stop_atr_mult": 1.5,
    "tp_r_mult": 2.0,
    "risk_usdt": 15.0,
    "leverage_cap": 5,
    "margin_mode": "isolated",
    "entry_expiry_hours": 4.0,
    "time_stop_hours": 8.0,
    "funding_window_minutes": 15,
    "funding_hours_utc": [0, 8, 16],
    "funding_adverse_max": 0.0003,
    "max_concurrent": 3,
    "max_per_symbol": 1,
    "daily_pause_usdt": 30.0,
    "hard_stop_usdt": 40.0,
    "max_consecutive_losses": 5,
    "stale_data_seconds": 60,
    "entry_max_signal_age_minutes": 15,
    "allow_short": False,
    "short_enable_min_trades": 30,
    "maker_fee": 0.0002,
    "taker_fee": 0.0006,
    "slippage_ticks": 1,
}

# Evaluation / deployment keys. They do not change trading rules and are NOT
# part of the v1 parameter hash.
EVAL_DEFAULTS: dict[str, Any] = {
    "margin_budget": "1000",
    "halt_reset_after_ts_ms": 0,
    "cost_multiplier": 1.0,
    "trade_start": "",
    "trade_end": "",
    "warmup_days": 100,
    "wf_train_months": 12,
    "wf_test_months": 3,
    "wf_step_months": 3,
    "require_funding_data": True,
    "backtest_halt_resume_hours": 72,
    "bar_ts_convention": "open",
}


@dataclass(frozen=True)
class Params:
    frozen: Mapping[str, Any]
    evalcfg: Mapping[str, Any]

    def __getattr__(self, name: str) -> Any:
        frozen = object.__getattribute__(self, "frozen")
        if name in frozen:
            return frozen[name]
        evalcfg = object.__getattribute__(self, "evalcfg")
        if name in evalcfg:
            return evalcfg[name]
        raise AttributeError(name)

    @property
    def equity_basis(self) -> float:
        return float(self.evalcfg["margin_budget"])


def load_params(raw: Optional[Mapping[str, Any]]) -> Params:
    """Merge manifest ``strategy_config`` over defaults and validate."""
    raw = dict(raw or {})
    frozen = {k: raw.get(k, v) for k, v in FROZEN_DEFAULTS.items()}
    evalcfg = {k: raw.get(k, v) for k, v in EVAL_DEFAULTS.items()}
    frozen["symbols"] = [str(s).upper() for s in raw.get("symbols", raw.get("trading_symbols", frozen["symbols"]))]
    _validate(frozen, evalcfg)
    return Params(frozen=frozen, evalcfg=evalcfg)


def _validate(frozen: Mapping[str, Any], evalcfg: Mapping[str, Any]) -> None:
    if frozen["allow_short"]:
        raise ConfigError(
            "allow_short=true is refused in v1: the short side has no validated "
            "execution path. Enable only in a later version after a separate "
            "short-side test shows >= short_enable_min_trades trades with positive "
            "net expectancy."
        )
    for sym in frozen["symbols"]:
        if sym not in CONTRACT_SPECS:
            raise ConfigError(f"symbol {sym} has no verified contract spec")
    if frozen["margin_mode"] != "isolated":
        raise ConfigError("margin_mode must be 'isolated'")
    if frozen["leverage_cap"] > 5:
        raise ConfigError("leverage_cap is hard-capped at 5")
    if frozen["max_per_symbol"] != 1:
        raise ConfigError("max_per_symbol must be 1")
    if not frozen["ema_fast"] < frozen["ema_slow"]:
        raise ConfigError("ema_fast must be < ema_slow")
    if frozen["risk_usdt"] <= 0 or float(evalcfg["margin_budget"]) <= 0:
        raise ConfigError("risk_usdt and margin_budget must be positive")
    if float(evalcfg["cost_multiplier"]) < 0:
        raise ConfigError("cost_multiplier must be >= 0")
    if evalcfg["bar_ts_convention"] not in ("open", "close"):
        raise ConfigError("bar_ts_convention must be 'open' or 'close'")


_K = (
    0x428A2F98, 0x71374491, 0xB5C0FBCF, 0xE9B5DBA5, 0x3956C25B, 0x59F111F1, 0x923F82A4, 0xAB1C5ED5,
    0xD807AA98, 0x12835B01, 0x243185BE, 0x550C7DC3, 0x72BE5D74, 0x80DEB1FE, 0x9BDC06A7, 0xC19BF174,
    0xE49B69C1, 0xEFBE4786, 0x0FC19DC6, 0x240CA1CC, 0x2DE92C6F, 0x4A7484AA, 0x5CB0A9DC, 0x76F988DA,
    0x983E5152, 0xA831C66D, 0xB00327C8, 0xBF597FC7, 0xC6E00BF3, 0xD5A79147, 0x06CA6351, 0x14292967,
    0x27B70A85, 0x2E1B2138, 0x4D2C6DFC, 0x53380D13, 0x650A7354, 0x766A0ABB, 0x81C2C92E, 0x92722C85,
    0xA2BFE8A1, 0xA81A664B, 0xC24B8B70, 0xC76C51A3, 0xD192E819, 0xD6990624, 0xF40E3585, 0x106AA070,
    0x19A4C116, 0x1E376C08, 0x2748774C, 0x34B0BCB5, 0x391C0CB3, 0x4ED8AA4A, 0x5B9CCA4F, 0x682E6FF3,
    0x748F82EE, 0x78A5636F, 0x84C87814, 0x8CC70208, 0x90BEFFFA, 0xA4506CEB, 0xBEF9A3F7, 0xC67178F2,
)


def sha256_hex(message: bytes) -> str:
    """Pure-Python SHA-256 (``hashlib`` is not an allowed Playbook import)."""
    h = [0x6A09E667, 0xBB67AE85, 0x3C6EF372, 0xA54FF53A, 0x510E527F, 0x9B05688C, 0x1F83D9AB, 0x5BE0CD19]
    mask = 0xFFFFFFFF
    data = bytearray(message)
    bit_len = len(message) * 8
    data.append(0x80)
    while len(data) % 64 != 56:
        data.append(0)
    data += bit_len.to_bytes(8, "big")

    def rotr(x: int, n: int) -> int:
        return ((x >> n) | (x << (32 - n))) & mask

    for off in range(0, len(data), 64):
        w = [int.from_bytes(data[off + 4 * i: off + 4 * i + 4], "big") for i in range(16)]
        for i in range(16, 64):
            s0 = rotr(w[i - 15], 7) ^ rotr(w[i - 15], 18) ^ (w[i - 15] >> 3)
            s1 = rotr(w[i - 2], 17) ^ rotr(w[i - 2], 19) ^ (w[i - 2] >> 10)
            w.append((w[i - 16] + s0 + w[i - 7] + s1) & mask)
        a, b, c, d, e, f, g, hh = h
        for i in range(64):
            t1 = (hh + (rotr(e, 6) ^ rotr(e, 11) ^ rotr(e, 25)) + ((e & f) ^ (~e & mask & g)) + _K[i] + w[i]) & mask
            t2 = ((rotr(a, 2) ^ rotr(a, 13) ^ rotr(a, 22)) + ((a & b) ^ (a & c) ^ (b & c))) & mask
            hh, g, f, e, d, c, b, a = g, f, e, (d + t1) & mask, c, b, a, (t1 + t2) & mask
        h = [(x + y) & mask for x, y in zip(h, [a, b, c, d, e, f, g, hh])]
    return "".join(f"{x:08x}" for x in h)


def param_hash(params: Params | Mapping[str, Any]) -> str:
    """SHA-256 over the canonical JSON of the frozen v1 trading parameters."""
    if isinstance(params, Params):
        frozen = dict(params.frozen)
    else:
        frozen = {k: params.get(k, v) for k, v in FROZEN_DEFAULTS.items()}
        if "trading_symbols" in params and "symbols" not in params:
            frozen["symbols"] = list(params["trading_symbols"])
    blob = json.dumps(frozen, sort_keys=True, separators=(",", ":"), default=str)
    return sha256_hex(blob.encode("utf-8"))


# ---------------------------------------------------------------------------
# Indicators (incremental, O(1) per bar apart from the rank insert)
# ---------------------------------------------------------------------------


def _bisect_left(values: list[float], x: float) -> int:
    lo, hi = 0, len(values)
    while lo < hi:
        mid = (lo + hi) // 2
        if values[mid] < x:
            lo = mid + 1
        else:
            hi = mid
    return lo


def _bisect_right(values: list[float], x: float) -> int:
    lo, hi = 0, len(values)
    while lo < hi:
        mid = (lo + hi) // 2
        if x < values[mid]:
            hi = mid
        else:
            lo = mid + 1
    return lo


class RollingRank:
    """Percent-rank of a value against the previous ``maxlen`` values."""

    def __init__(self, maxlen: int) -> None:
        self.maxlen = maxlen
        self._order: deque[float] = deque()
        self._sorted: list[float] = []

    def __len__(self) -> int:
        return len(self._order)

    def rank_pct(self, x: float) -> Optional[float]:
        n = len(self._sorted)
        if n == 0:
            return None
        return 100.0 * _bisect_right(self._sorted, x) / n

    def add(self, x: float) -> None:
        self._order.append(x)
        self._sorted.insert(_bisect_right(self._sorted, x), x)
        if len(self._order) > self.maxlen:
            old = self._order.popleft()
            del self._sorted[_bisect_left(self._sorted, old)]


@dataclass
class Features:
    close: float
    ema_fast: Optional[float] = None
    ema_slow: Optional[float] = None
    atr: Optional[float] = None
    atr_pct: Optional[float] = None
    atr_pct_rank: Optional[float] = None
    adx: Optional[float] = None
    plus_di: Optional[float] = None
    minus_di: Optional[float] = None
    vol_ratio: Optional[float] = None
    structure: bool = False
    structure_prev: bool = False
    ready: bool = False

    @property
    def trigger(self) -> bool:
        return self.structure and not self.structure_prev


class IndicatorEngine:
    """EMA(fast/slow), Wilder ATR/ADX/DI, ATR% percentile rank, volume ratio."""

    def __init__(
        self,
        ema_fast: int = 20,
        ema_slow: int = 50,
        adx_period: int = 14,
        atr_period: int = 14,
        atr_pct_lookback: int = 2160,
        atr_pct_min_history: int = 500,
        volume_lookback: int = 20,
    ) -> None:
        if adx_period != atr_period:
            raise ConfigError("adx_period must equal atr_period (shared Wilder smoothing)")
        self.nf, self.ns, self.p = ema_fast, ema_slow, atr_period
        self.min_hist = atr_pct_min_history
        self.vol_n = volume_lookback
        self.n = 0
        self._closes_f: list[float] = []
        self._closes_s: list[float] = []
        self._ema_f: Optional[float] = None
        self._ema_s: Optional[float] = None
        self._prev: Optional[tuple[float, float, float]] = None
        self._acc_tr = self._acc_p = self._acc_m = 0.0
        self._tr_count = 0
        self._sm_tr = self._sm_p = self._sm_m = 0.0
        self._dx_vals: list[float] = []
        self._adx: Optional[float] = None
        self._rank = RollingRank(atr_pct_lookback)
        self._vols: deque[float] = deque()
        self._vol_sum = 0.0
        self._structure_prev = False

    @staticmethod
    def _ema_step(prev: float, x: float, n: int) -> float:
        a = 2.0 / (n + 1)
        return a * x + (1.0 - a) * prev

    def update(self, high: float, low: float, close: float, volume: float) -> Features:
        self.n += 1
        # EMAs seeded with the SMA of the first N closes.
        if self._ema_f is None:
            self._closes_f.append(close)
            if len(self._closes_f) == self.nf:
                self._ema_f = sum(self._closes_f) / self.nf
        else:
            self._ema_f = self._ema_step(self._ema_f, close, self.nf)
        if self._ema_s is None:
            self._closes_s.append(close)
            if len(self._closes_s) == self.ns:
                self._ema_s = sum(self._closes_s) / self.ns
        else:
            self._ema_s = self._ema_step(self._ema_s, close, self.ns)

        atr = plus_di = minus_di = None
        if self._prev is not None:
            ph, pl, pc = self._prev
            tr = max(high - low, abs(high - pc), abs(low - pc))
            up, down = high - ph, pl - low
            pdm = up if (up > down and up > 0) else 0.0
            mdm = down if (down > up and down > 0) else 0.0
            if self._tr_count < self.p:
                self._acc_tr += tr
                self._acc_p += pdm
                self._acc_m += mdm
                self._tr_count += 1
                if self._tr_count == self.p:
                    self._sm_tr, self._sm_p, self._sm_m = self._acc_tr, self._acc_p, self._acc_m
                    self._dx_step()
            else:
                self._sm_tr = self._sm_tr - self._sm_tr / self.p + tr
                self._sm_p = self._sm_p - self._sm_p / self.p + pdm
                self._sm_m = self._sm_m - self._sm_m / self.p + mdm
                self._dx_step()
            if self._tr_count >= self.p and self._sm_tr > 0:
                atr = self._sm_tr / self.p
                plus_di = 100.0 * self._sm_p / self._sm_tr
                minus_di = 100.0 * self._sm_m / self._sm_tr
        self._prev = (high, low, close)

        atr_pct = atr_rank = None
        if atr is not None and close > 0:
            atr_pct = atr / close
            if len(self._rank) >= self.min_hist:
                atr_rank = self._rank.rank_pct(atr_pct)
            self._rank.add(atr_pct)

        vol_ratio = None
        if len(self._vols) == self.vol_n:
            avg = self._vol_sum / self.vol_n
            vol_ratio = volume / avg if avg > 0 else None
        self._vols.append(volume)
        self._vol_sum += volume
        if len(self._vols) > self.vol_n:
            self._vol_sum -= self._vols.popleft()

        feats = Features(
            close=close, ema_fast=self._ema_f, ema_slow=self._ema_s, atr=atr,
            atr_pct=atr_pct, atr_pct_rank=atr_rank, adx=self._adx,
            plus_di=plus_di, minus_di=minus_di, vol_ratio=vol_ratio,
        )
        have_all = None not in (
            feats.ema_fast, feats.ema_slow, feats.atr, feats.adx, feats.plus_di, feats.minus_di,
        )
        if have_all:
            feats.structure = bool(
                feats.ema_fast > feats.ema_slow
                and close > feats.ema_fast
                and feats.plus_di > feats.minus_di
            )
        feats.structure_prev = self._structure_prev
        self._structure_prev = feats.structure
        feats.ready = bool(
            have_all and feats.atr_pct_rank is not None and feats.vol_ratio is not None
        )
        return feats

    def _dx_step(self) -> None:
        if self._sm_tr <= 0:
            return
        pdi = 100.0 * self._sm_p / self._sm_tr
        mdi = 100.0 * self._sm_m / self._sm_tr
        denom = pdi + mdi
        dx = 100.0 * abs(pdi - mdi) / denom if denom > 0 else 0.0
        if self._adx is None:
            self._dx_vals.append(dx)
            if len(self._dx_vals) == self.p:
                self._adx = sum(self._dx_vals) / self.p
        else:
            self._adx = (self._adx * (self.p - 1) + dx) / self.p


# ---------------------------------------------------------------------------
# Regime, signal, funding
# ---------------------------------------------------------------------------


def regime_ok(f: Features, p: Params) -> tuple[bool, ReasonCode]:
    """Regime gate: trend strength (ADX) and volatility band (ATR% rank)."""
    if not f.ready:
        return False, ReasonCode.REGIME_WARMUP
    if f.adx < p.adx_min:
        return False, ReasonCode.REGIME_ADX_LOW
    if f.atr_pct_rank < p.atr_pct_rank_low:
        return False, ReasonCode.REGIME_ATR_PCT_LOW
    if f.atr_pct_rank > p.atr_pct_rank_high:
        return False, ReasonCode.REGIME_ATR_PCT_HIGH
    return True, ReasonCode.SIGNAL_LONG_ENTRY


def evaluate_signal(f: Features, p: Params) -> ReasonCode:
    """Return SIGNAL_LONG_ENTRY or the reason there is no trade."""
    if not f.ready:
        return ReasonCode.REGIME_WARMUP
    if not f.trigger:
        return ReasonCode.NO_SIGNAL
    ok, reason = regime_ok(f, p)
    if not ok:
        return reason
    if f.vol_ratio < p.volume_mult:
        return ReasonCode.SKIP_VOLUME_NOT_CONFIRMED
    return ReasonCode.SIGNAL_LONG_ENTRY


def funding_adverse(rate: float, side: str, max_abs: float) -> bool:
    """True when the funding rate is adverse to the position beyond the cap."""
    if side == "long":
        return rate > max_abs
    return rate < -max_abs


# ---------------------------------------------------------------------------
# Time helpers
# ---------------------------------------------------------------------------


def floor_hour_ms(ts_ms: int) -> int:
    return ts_ms - (ts_ms % HOUR_MS)


def day_key(ts_ms: int) -> str:
    return datetime.fromtimestamp(ts_ms / 1000.0, tz=timezone.utc).strftime("%Y-%m-%d")


def iso(ts_ms: int) -> str:
    return datetime.fromtimestamp(ts_ms / 1000.0, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_iso_ms(text: str) -> int:
    t = text.strip().replace("Z", "+00:00")
    dt = datetime.fromisoformat(t)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return int(dt.timestamp() * 1000)


def funding_settlements(t0_ms: int, t1_ms: int, hours: Iterable[int] = (0, 8, 16)) -> list[int]:
    """Funding settlement instants S with t0 < S <= t1."""
    out: list[int] = []
    day0 = t0_ms - (t0_ms % DAY_MS)
    day = day0
    while day <= t1_ms:
        for h in hours:
            s = day + h * HOUR_MS
            if t0_ms < s <= t1_ms:
                out.append(s)
        day += DAY_MS
    return sorted(out)


def in_funding_window(ts_ms: int, window_min: int, hours: Iterable[int] = (0, 8, 16)) -> bool:
    """True when ``ts`` is within +-window_min (inclusive) of a settlement."""
    w = window_min * MINUTE_MS
    day0 = ts_ms - (ts_ms % DAY_MS)
    for day in (day0 - DAY_MS, day0, day0 + DAY_MS):
        for h in hours:
            if abs(ts_ms - (day + h * HOUR_MS)) <= w:
                return True
    return False


def next_window_start_ms(ts_ms: int, window_min: int, hours: Iterable[int] = (0, 8, 16)) -> int:
    """Start of the next funding no-trade window at or after ``ts``."""
    w = window_min * MINUTE_MS
    day0 = ts_ms - (ts_ms % DAY_MS)
    best: Optional[int] = None
    for day in (day0 - DAY_MS, day0, day0 + DAY_MS, day0 + 2 * DAY_MS):
        for h in hours:
            start = day + h * HOUR_MS - w
            end = day + h * HOUR_MS + w
            if start <= ts_ms <= end:
                return ts_ms
            if start > ts_ms and (best is None or start < best):
                best = start
    assert best is not None
    return best


def bar_freshness(now_ms: int, latest_open_ms: Optional[int], stale_seconds: int) -> str:
    """'fresh', 'not_yet' (bar still within the publish grace) or 'stale'."""
    if latest_open_ms is None:
        return "stale"
    expected_open = floor_hour_ms(now_ms) - HOUR_MS
    if latest_open_ms >= expected_open:
        return "fresh"
    lateness_ms = now_ms - floor_hour_ms(now_ms)
    return "not_yet" if lateness_ms <= stale_seconds * 1000 else "stale"


def classify_exit(exit_px: float, stop: float, tp: float, tick: float, time_stop_requested: bool) -> ReasonCode:
    """Infer why a position closed from the exit price (exchange-side exits)."""
    if exit_px <= stop + 2 * tick:
        return ReasonCode.EXIT_STOP_LOSS
    if exit_px >= tp - 2 * tick:
        return ReasonCode.EXIT_TAKE_PROFIT
    return ReasonCode.EXIT_TIME_STOP if time_stop_requested else ReasonCode.EXIT_UNKNOWN


def entry_expiry_ms(decision_ms: int, p: Params) -> int:
    """Unfilled entry expiry: 4h, shortened so no fill lands in a funding window."""
    base = decision_ms + int(p.entry_expiry_hours * HOUR_MS)
    return min(base, next_window_start_ms(decision_ms, int(p.funding_window_minutes), p.funding_hours_utc))


# ---------------------------------------------------------------------------
# Sizing
# ---------------------------------------------------------------------------


def q_down(value: Any, step: Decimal) -> Decimal:
    return (Decimal(str(value)) / step).to_integral_value(rounding=ROUND_FLOOR) * step


def q_up(value: Any, step: Decimal) -> Decimal:
    return (Decimal(str(value)) / step).to_integral_value(rounding=ROUND_CEILING) * step


@dataclass(frozen=True)
class EntryPlan:
    symbol: str
    entry: Decimal
    stop: Decimal
    take_profit: Decimal
    stop_dist: Decimal
    qty: Decimal
    notional: float
    risk_at_stop_usdt: float
    required_leverage: float


def plan_long_entry(
    *,
    close: float,
    atr: float,
    spec: ContractSpec,
    p: Params,
    equity: float,
    open_notional: float = 0.0,
) -> tuple[Optional[EntryPlan], ReasonCode]:
    """Fixed-loss sizing: qty = risk / stop distance, rounded DOWN to the lot step.

    Prices are rounded conservatively: entry and stop DOWN, take-profit UP.
    """
    entry = q_down(close - p.entry_offset_atr * atr, spec.tick)
    stop = q_down(float(entry) - p.stop_atr_mult * atr, spec.tick)
    stop_dist = entry - stop
    if stop <= 0 or stop_dist <= 0:
        return None, ReasonCode.SKIP_INVALID_STOP
    tp = q_up(float(entry) + p.tp_r_mult * float(stop_dist), spec.tick)
    qty = q_down(p.risk_usdt / float(stop_dist), spec.qty_step)
    if qty < spec.min_qty or qty * entry < spec.min_notional_usdt:
        return None, ReasonCode.SKIP_BELOW_MIN_QTY
    notional = float(qty * entry)
    req_lev = notional / equity
    if req_lev > p.leverage_cap:
        return None, ReasonCode.SKIP_LEVERAGE_CAP
    if (open_notional + notional) / p.leverage_cap > equity:
        return None, ReasonCode.SKIP_MARGIN_INSUFFICIENT
    return (
        EntryPlan(spec.symbol, entry, stop, tp, stop_dist, qty, notional,
                  float(qty * stop_dist), req_lev),
        ReasonCode.SIGNAL_LONG_ENTRY,
    )


# ---------------------------------------------------------------------------
# Risk state (daily pause, daily hard stop, consecutive-loss halt)
# ---------------------------------------------------------------------------


@dataclass
class RiskState:
    p: Params
    resume_after_hours: Optional[float] = None
    day_pnl: dict[str, float] = field(default_factory=dict)
    consecutive_losses: int = 0
    halt_reason: Optional[ReasonCode] = None
    halt_ts_ms: int = 0
    events: list[tuple[int, ReasonCode, str]] = field(default_factory=list)
    halts: int = 0

    def record_trade(self, exit_ts_ms: int, net_pnl: float) -> None:
        key = day_key(exit_ts_ms)
        self.day_pnl[key] = self.day_pnl.get(key, 0.0) + net_pnl
        self.consecutive_losses = self.consecutive_losses + 1 if net_pnl < 0 else 0
        if self.halt_reason is None:
            if self.day_pnl[key] <= -self.p.hard_stop_usdt:
                self._latch(exit_ts_ms, ReasonCode.HALT_DAILY_LOSS_STOP, f"day_pnl={self.day_pnl[key]:.2f}")
            elif self.consecutive_losses >= self.p.max_consecutive_losses:
                self._latch(exit_ts_ms, ReasonCode.HALT_CONSEC_LOSSES, f"streak={self.consecutive_losses}")

    def _latch(self, ts_ms: int, reason: ReasonCode, detail: str) -> None:
        self.halt_reason, self.halt_ts_ms = reason, ts_ms
        self.halts += 1
        self.events.append((ts_ms, reason, detail))

    def entry_gate(self, ts_ms: int) -> Optional[ReasonCode]:
        """Return the reason new entries are blocked now, or None."""
        if self.halt_reason is not None:
            if (
                self.resume_after_hours is not None
                and ts_ms >= self.halt_ts_ms + int(self.resume_after_hours * HOUR_MS)
            ):
                self.events.append((ts_ms, ReasonCode.RESUME_SIMULATED_MANUAL_RESET, self.halt_reason.value))
                self.halt_reason = None
                self.consecutive_losses = 0
            else:
                return self.halt_reason
        if self.day_pnl.get(day_key(ts_ms), 0.0) <= -self.p.daily_pause_usdt:
            return ReasonCode.PAUSE_DAILY_LOSS
        return None


# ---------------------------------------------------------------------------
# Costs and metrics
# ---------------------------------------------------------------------------


def trade_costs_1x(
    *, entry_px: float, exit_px: float, qty: float, tick: float,
    maker_fee: float, taker_fee: float, slippage_ticks: float, funding_paid: float,
) -> dict[str, float]:
    """Unscaled cost components for one long round trip.

    Entry is a limit order (maker fee); every exit is exchange-triggered or
    market (taker fee). Slippage is charged conservatively on BOTH fills.
    Positive ``funding_paid`` is money paid by the position.
    """
    fee_entry = entry_px * qty * maker_fee
    fee_exit = exit_px * qty * taker_fee
    slip = 2.0 * slippage_ticks * tick * qty
    return {
        "fee_entry": fee_entry,
        "fee_exit": fee_exit,
        "slippage": slip,
        "funding": funding_paid,
        "total": fee_entry + fee_exit + slip + funding_paid,
    }


def reprice_trades(trades: list[dict[str, Any]], multiplier: float) -> list[dict[str, Any]]:
    out = []
    for t in trades:
        net = t["gross_pnl"] - multiplier * t["costs_1x_total"]
        r = t["r_usdt"]
        out.append({**t, "net_pnl": net, "net_r": net / r if r else 0.0})
    return out


def compute_metrics(
    trades: list[dict[str, Any]], *, equity_basis: float, start_ms: int, end_ms: int,
    min_trades: int = 30,
) -> dict[str, Any]:
    """Net-of-cost metrics from a trade ledger. All results are net unless named gross."""
    n = len(trades)
    out: dict[str, Any] = {"trades": n, "min_trades_for_verdict": min_trades}
    if n == 0:
        out.update(verdict="NO_TRADES", win_rate=None, avg_r_gross=None, expectancy_r_net=None,
                   profit_factor=None, max_drawdown_usdt=None, max_drawdown_pct_of_equity=None,
                   sharpe_daily_annualised=None, net_pnl=0.0)
        return out
    ordered = sorted(trades, key=lambda t: t["exit_ts_ms"])
    net = [t["net_pnl"] for t in ordered]
    wins = [x for x in net if x > 0]
    losses = [x for x in net if x < 0]
    cum = peak = max_dd = 0.0
    peak_at_dd = 0.0
    for x in net:
        cum += x
        if cum > peak:
            peak = cum
        if peak - cum > max_dd:
            max_dd, peak_at_dd = peak - cum, peak
    daily: dict[str, float] = {}
    for t in ordered:
        daily[day_key(t["exit_ts_ms"])] = daily.get(day_key(t["exit_ts_ms"]), 0.0) + t["net_pnl"]
    n_days = max(1, int((end_ms - start_ms) // DAY_MS))
    series = [daily.get(day_key(start_ms + i * DAY_MS), 0.0) / equity_basis for i in range(n_days)]
    sharpe = None
    if len(series) >= 2:
        mean = sum(series) / len(series)
        var = sum((x - mean) ** 2 for x in series) / (len(series) - 1)
        if var > 0:
            sharpe = mean / math.sqrt(var) * math.sqrt(365.0)
    out.update(
        win_rate=len(wins) / n,
        avg_r_gross=sum(t["gross_pnl"] / t["r_usdt"] for t in ordered) / n,
        expectancy_r_net=sum(t["net_r"] for t in ordered) / n,
        profit_factor=(sum(wins) / abs(sum(losses))) if losses else None,
        profit_factor_note=None if losses else "no losing trades; PF undefined",
        max_drawdown_usdt=max_dd,
        max_drawdown_pct_of_equity=100.0 * max_dd / (equity_basis + peak_at_dd),
        drawdown_basis="realised-equity, closed trades only (no intra-trade mark-to-market)",
        sharpe_daily_annualised=sharpe,
        sharpe_basis="daily realised net PnL / equity_basis, zero-filled calendar days, sqrt(365)",
        net_pnl=sum(net),
        gross_pnl=sum(t["gross_pnl"] for t in ordered),
        costs_total=sum(t["gross_pnl"] - t["net_pnl"] for t in ordered),
        verdict="INSUFFICIENT_TRADES_NO_VERDICT" if n < min_trades else "VERDICT_ELIGIBLE",
    )
    return out


def add_months(ts_ms: int, months: int) -> int:
    dt = datetime.fromtimestamp(ts_ms / 1000.0, tz=timezone.utc)
    total = dt.year * 12 + (dt.month - 1) + months
    year, month0 = divmod(total, 12)
    day = min(dt.day, 28)
    return int(dt.replace(year=year, month=month0 + 1, day=day).timestamp() * 1000)


def walk_forward_windows(
    origin_ms: int, end_ms: int, train_m: int, test_m: int, step_m: int,
) -> list[dict[str, int]]:
    """Rolling windows: ``train_m`` months train then ``test_m`` months test, step ``step_m``."""
    wins: list[dict[str, int]] = []
    k = 0
    while True:
        tr0 = add_months(origin_ms, k * step_m)
        tr1 = add_months(tr0, train_m)
        te1 = add_months(tr1, test_m)
        if te1 > end_ms:
            break
        wins.append({"train_start": tr0, "train_end": tr1, "test_start": tr1, "test_end": te1})
        k += 1
    return wins


def trades_in(trades: list[dict[str, Any]], start_ms: int, end_ms: int) -> list[dict[str, Any]]:
    return [t for t in trades if start_ms <= t["entry_ts_ms"] < end_ms]


# ---------------------------------------------------------------------------
# Structured log records
# ---------------------------------------------------------------------------

LOG_FIELDS = (
    "timestamp", "ts_ms", "symbol", "side", "action", "reason_code",
    "intended_price", "filled_price", "qty", "fee_usdt", "funding_usdt", "pnl_usdt", "detail",
)


def make_log(
    ts_ms: int, symbol: str, action: str, reason: ReasonCode, *, side: str = "long",
    intended_price: Any = None, filled_price: Any = None, qty: Any = None,
    fee_usdt: Optional[float] = None, funding_usdt: Optional[float] = None,
    pnl_usdt: Optional[float] = None, **detail: Any,
) -> dict[str, Any]:
    def num(x: Any) -> Any:
        return None if x is None else float(x)

    return {
        "timestamp": iso(ts_ms),
        "ts_ms": int(ts_ms),
        "symbol": symbol,
        "side": side,
        "action": action,
        "reason_code": reason.value,
        "intended_price": num(intended_price),
        "filled_price": num(filled_price),
        "qty": num(qty),
        "fee_usdt": fee_usdt,
        "funding_usdt": funding_usdt,
        "pnl_usdt": pnl_usdt,
        "detail": detail,
    }


# ---------------------------------------------------------------------------
# Live-payload helpers (defensive: SDK response shapes are not fully documented)
# ---------------------------------------------------------------------------


def to_plain(obj: Any) -> Any:
    if obj is None or isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, Mapping):
        return {str(k): to_plain(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [to_plain(v) for v in obj]
    for attr in ("model_dump", "dict"):
        fn = getattr(obj, attr, None)
        if callable(fn):
            try:
                return to_plain(fn())
            except Exception:  # noqa: BLE001
                pass
    if hasattr(obj, "__dict__"):
        return to_plain(vars(obj))
    return str(obj)


_LIST_KEYS = ("fillList", "entrustedList", "orderList", "list", "positions", "data", "rows", "items")


def extract_records(payload: Any) -> list[dict[str, Any]]:
    """Find the list of record dicts inside an SDK/exchange envelope."""
    p = to_plain(payload)
    if isinstance(p, list):
        return [r for r in p if isinstance(r, dict)]
    if isinstance(p, dict):
        for key in _LIST_KEYS:
            if key in p:
                found = extract_records(p[key])
                if found or isinstance(p[key], list):
                    return found
        if any(k in p for k in ("symbol", "orderId", "holdSide")):
            return [p]
    return []


def deep_find(obj: Any, names: Iterable[str]) -> Any:
    """First non-empty value stored under any of ``names`` at any depth."""
    wanted = tuple(names)
    p = to_plain(obj)
    stack = [p]
    while stack:
        cur = stack.pop(0)
        if isinstance(cur, dict):
            for n in wanted:
                if n in cur and cur[n] not in (None, ""):
                    return cur[n]
            stack.extend(cur.values())
        elif isinstance(cur, list):
            stack.extend(cur)
    return None


def pick(rec: Mapping[str, Any], *names: str, default: Any = None) -> Any:
    for n in names:
        if n in rec and rec[n] not in (None, ""):
            return rec[n]
    return default


def to_float(x: Any) -> Optional[float]:
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    return v if math.isfinite(v) else None


def to_ms(x: Any) -> Optional[int]:
    v = to_float(x)
    if v is None:
        return None
    return int(v if v > 1e11 else v * 1000)


def normalize_fill(rec: Mapping[str, Any]) -> dict[str, Any]:
    fee = to_float(pick(rec, "fee", "totalFee"))
    if fee is None:
        detail = pick(rec, "feeDetail", default=[])
        if isinstance(detail, list) and detail:
            fee = sum(to_float(d.get("totalFee")) or 0.0 for d in detail if isinstance(d, Mapping))
    trade_side = str(pick(rec, "tradeSide", "trade_side", default="")).lower()
    return {
        "symbol": str(pick(rec, "symbol", default="")),
        "order_id": str(pick(rec, "orderId", "order_id", default="")),
        "ts_ms": to_ms(pick(rec, "cTime", "ctime", "ts", "createTime", "time")),
        "price": to_float(pick(rec, "priceAvg", "price")),
        "qty": to_float(pick(rec, "baseVolume", "size", "qty")),
        "profit": to_float(pick(rec, "profit", "pnl", "realizedPnl")),
        "has_profit_field": any(k in rec for k in ("profit", "pnl", "realizedPnl")),
        "fee": abs(fee) if fee is not None else 0.0,
        "trade_side": trade_side,
        "is_close": "close" in trade_side,
    }


def normalize_position(rec: Mapping[str, Any]) -> dict[str, Any]:
    size = to_float(pick(rec, "total", "size", "holdSize", "available", "qty", default=0)) or 0.0
    return {
        "symbol": str(pick(rec, "symbol", default="")),
        "hold_side": str(pick(rec, "holdSide", "hold_side", "posSide", default="")).lower(),
        "size": size,
        "open_px": to_float(pick(rec, "openPriceAvg", "open_price", "avgPrice", "entryPrice")),
        "ctime_ms": to_ms(pick(rec, "cTime", "ctime", "createTime")),
        "margin_mode": str(pick(rec, "marginMode", "margin_mode", default="")).lower(),
        "leverage": to_float(pick(rec, "leverage")),
    }


def realised_summary(
    fills: Iterable[Mapping[str, Any]], *, owned_symbols: set[str], now_ms: int,
    reset_after_ms: int = 0,
) -> dict[str, Any]:
    """Day PnL (UTC day of ``now``) and trailing loss streak from exchange fills.

    Fails closed: ``pnl_available`` is False if a closing fill has no profit field.
    """
    norm = [normalize_fill(r) for r in fills]
    norm = [f for f in norm if f["symbol"] in owned_symbols and f["ts_ms"] is not None]
    today = day_key(now_ms)
    available = all(f["has_profit_field"] for f in norm if f["is_close"])
    day = 0.0
    for f in norm:
        if day_key(f["ts_ms"]) != today:
            continue
        day -= f["fee"]
        if f["is_close"] and f["profit"] is not None:
            day += f["profit"]
    per_order: dict[str, dict[str, float]] = {}
    for f in norm:
        if f["is_close"] and f["ts_ms"] >= reset_after_ms and f["profit"] is not None:
            slot = per_order.setdefault(f["order_id"], {"ts": f["ts_ms"], "net": 0.0})
            slot["ts"] = max(slot["ts"], f["ts_ms"])
            slot["net"] += f["profit"] - f["fee"]
    streak = 0
    for slot in sorted(per_order.values(), key=lambda s: s["ts"], reverse=True):
        if slot["net"] < 0:
            streak += 1
        else:
            break
    return {"day_pnl": day, "loss_streak": streak, "pnl_available": available, "closing_orders": len(per_order)}
