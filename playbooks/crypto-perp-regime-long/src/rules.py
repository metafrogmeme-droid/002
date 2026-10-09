"""Pure, deterministic rule layer shared by live execution, the Nautilus replay and offline research.

No getagent / network imports here: every function is a function of closed bars and explicit config,
so the same code path produces the signal in backtest and live.
"""
import math
from collections import deque
from dataclasses import dataclass, field
from typing import Optional

import numpy as np
import pandas as pd

HOUR_MS = 3_600_000
FUNDING_SETTLEMENT_HOURS_UTC = (0, 8, 16)

REASON = {
    "NO_SIGNAL": "no_signal",
    "SIGNAL_INVALID": "signal_layer_invalid_or_insufficient_history",
    "REGIME_T": "trend_pullback_long",
    "REGIME_M": "mean_reversion_long",
    "REGIME_B": "breakout_continuation_long",
    "SPREAD": "spread_gate",
    "VOLUME": "volume_gate",
    "FUNDING_WINDOW": "funding_settlement_window",
    "FUNDING_COST": "expected_funding_gt_cap",
    "SIZE_CAP": "size_exceeds_margin_cap",
    "SIZE_MIN": "size_below_exchange_min",
    "CLUSTER": "correlation_cluster_occupied",
    "SYMBOL_OPEN": "symbol_already_open",
    "MAX_CONCURRENT": "max_concurrent_reached",
    "DAILY_PAUSE": "daily_loss_pause",
    "STOP_PLAYBOOK": "playbook_loss_stop",
    "HALT_STREAK": "consecutive_loss_halt",
    "HALT_STALE": "data_stale_halt",
    "HALT_FOREIGN": "foreign_position_halt",
}


@dataclass(frozen=True)
class Config:
    """Every field is read from manifest strategy_config; defaults only apply to unit tests."""

    symbols: tuple = ("BTCUSDT", "ETHUSDT", "SOLUSDT")
    risk_usdt: float = 15.0
    atr_period: int = 14
    stop_atr_mult: float = 1.5
    tp_r_mult: float = 2.0
    adx_period: int = 14
    adx_trend_min: float = 25.0
    adx_range_max: float = 20.0
    atr_pct_window: int = 720
    atr_pct_rank_min: float = 0.20
    atr_pct_rank_max_mr: float = 0.80
    ema_fast: int = 20
    ema_mid: int = 50
    ema_slow: int = 200
    bb_period: int = 20
    bb_std: float = 2.0
    rsi_period: int = 14
    rsi_mr_max: float = 35.0
    enable_trend: bool = True
    enable_mr: bool = True
    enable_break: bool = False
    break_lookback: int = 48
    break_rank_min: float = 0.50
    htf_filter: bool = False
    htf_span: int = 1200
    time_stop_hours_trend: int = 8
    time_stop_hours_mr: int = 2
    entry_cancel_hours: int = 4
    leverage: int = 5
    margin_cap_usdt: float = 1000.0
    max_concurrent: int = 3
    funding_blackout_min: int = 15
    funding_cap_r: float = 0.10
    funding_rate_assumed: float = 0.0001
    min_volume_24h_usdt: float = 10_000_000.0
    max_spread_bps: float = 5.0
    daily_pause_usdt: float = 30.0
    stop_playbook_usdt: float = 40.0
    max_consecutive_losses: int = 5
    stale_seconds: int = 60

    @staticmethod
    def from_mapping(m: dict) -> "Config":
        base = Config()
        kwargs = {}
        if "trading_symbols" in m and "symbols" not in m:
            m = {**m, "symbols": m["trading_symbols"]}
        for f in base.__dataclass_fields__:
            if f in m and m[f] is not None:
                default = getattr(base, f)
                v = m[f]
                if isinstance(default, bool):
                    v = bool(v)
                elif isinstance(default, int):
                    v = int(v)
                elif isinstance(default, float):
                    v = float(v)
                elif isinstance(default, tuple):
                    v = tuple(v)
                kwargs[f] = v
        return Config(**kwargs)


def _wilder(arr: np.ndarray, n: int) -> np.ndarray:
    out = np.full(len(arr), np.nan)
    if len(arr) < n:
        return out
    seed = np.nanmean(arr[:n])
    out[n - 1] = seed
    a = 1.0 / n
    for i in range(n, len(arr)):
        out[i] = out[i - 1] + a * (arr[i] - out[i - 1])
    return out


def _rolling_rank(x: np.ndarray, window: int) -> np.ndarray:
    """Percentile rank of x[i] within x[i-window+1 .. i] (inclusive); NaN until the window is full."""
    out = np.full(len(x), np.nan)
    for i in range(window - 1, len(x)):
        w = x[i - window + 1 : i + 1]
        if np.isnan(w).any():
            continue
        out[i] = float((w <= x[i]).mean())
    return out


def compute_indicators(df: pd.DataFrame, cfg: Config) -> pd.DataFrame:
    """df: DatetimeIndex (UTC bar open time) + open/high/low/close/volume. Returns copy with feature columns.

    All columns at row i use only bars <= i (bar i is closed).
    """
    d = df.copy()
    o, h, l, c = (d[k].to_numpy(float) for k in ("open", "high", "low", "close"))
    prev_c = np.r_[np.nan, c[:-1]]
    tr = np.maximum.reduce([h - l, np.abs(h - prev_c), np.abs(l - prev_c)])
    tr[0] = h[0] - l[0]
    atr = _wilder(tr, cfg.atr_period)

    up = h - np.r_[np.nan, h[:-1]]
    dn = np.r_[np.nan, l[:-1]] - l
    plus_dm = np.where((up > dn) & (up > 0), up, 0.0)
    minus_dm = np.where((dn > up) & (dn > 0), dn, 0.0)
    plus_dm[0] = minus_dm[0] = 0.0
    n = cfg.adx_period
    atr_n = _wilder(tr, n)
    pdi = 100.0 * _wilder(plus_dm, n) / atr_n
    mdi = 100.0 * _wilder(minus_dm, n) / atr_n
    dx = 100.0 * np.abs(pdi - mdi) / (pdi + mdi)
    adx = np.full(len(c), np.nan)
    first = np.where(~np.isnan(dx))[0]
    if len(first):
        s = first[0]
        seg = _wilder(dx[s:], n)
        adx[s:] = seg

    close_s = pd.Series(c, index=d.index)
    d["atr"] = atr
    d["atr_pct"] = atr / c
    d["atr_pct_rank"] = _rolling_rank(d["atr_pct"].to_numpy(), cfg.atr_pct_window)
    d["adx"] = adx
    d["plus_di"] = pdi
    d["minus_di"] = mdi
    d["ema_fast"] = close_s.ewm(span=cfg.ema_fast, adjust=False).mean().to_numpy()
    d["ema_mid"] = close_s.ewm(span=cfg.ema_mid, adjust=False).mean().to_numpy()
    d["ema_slow"] = close_s.ewm(span=cfg.ema_slow, adjust=False).mean().to_numpy()
    ma = close_s.rolling(cfg.bb_period).mean()
    sd = close_s.rolling(cfg.bb_period).std(ddof=0)
    d["bb_low"] = (ma - cfg.bb_std * sd).to_numpy()
    delta = close_s.diff()
    gain = delta.clip(lower=0).to_numpy()
    loss = (-delta.clip(upper=0)).to_numpy()
    gain[0] = loss[0] = 0.0
    rs_g = _wilder(gain, cfg.rsi_period)
    rs_l = _wilder(loss, cfg.rsi_period)
    d["rsi"] = 100.0 - 100.0 / (1.0 + rs_g / np.where(rs_l == 0, np.nan, rs_l))
    d.loc[rs_l == 0, "rsi"] = 100.0
    d["quote_vol_24h"] = (d["close"] * d["volume"]).rolling(24).sum()
    d["prior_high"] = d["high"].shift(1).rolling(cfg.break_lookback).max()
    d["prior_high_prev"] = d["prior_high"].shift(1)
    htf = close_s.ewm(span=cfg.htf_span, adjust=False).mean()
    htf.iloc[: cfg.htf_span - 1] = np.nan
    d["ema_htf"] = htf.to_numpy()
    return d


def compute_signals(ind: pd.DataFrame, cfg: Config) -> pd.DataFrame:
    """Adds boolean columns sig_trend / sig_mr and `valid` (all inputs finite)."""
    d = ind
    needed = ["atr", "adx", "plus_di", "minus_di", "ema_fast", "ema_mid", "ema_slow", "atr_pct_rank", "bb_low", "rsi"]
    if cfg.htf_filter:
        needed = needed + ["ema_htf"]
    valid = d[needed].notna().all(axis=1)
    htf_ok = (d["close"] > d["ema_htf"]) if cfg.htf_filter else True
    reg_t = (
        (d["adx"] >= cfg.adx_trend_min)
        & (d["plus_di"] > d["minus_di"])
        & (d["ema_mid"] > d["ema_slow"])
        & (d["close"] > d["ema_slow"])
        & (d["atr_pct_rank"] >= cfg.atr_pct_rank_min)
    )
    touch = (d["close"] <= d["ema_fast"]) & (d["close"].shift(1) > d["ema_fast"].shift(1)) & (d["close"] > d["ema_mid"])
    reg_m = (d["adx"] < cfg.adx_range_max) & (d["atr_pct_rank"] >= cfg.atr_pct_rank_min) & (d["atr_pct_rank"] <= cfg.atr_pct_rank_max_mr)
    brk = (d["close"] < d["bb_low"]) & (d["close"].shift(1) >= d["bb_low"].shift(1)) & (d["rsi"] < cfg.rsi_mr_max)
    reg_b = (
        (d["adx"] >= cfg.adx_trend_min)
        & (d["plus_di"] > d["minus_di"])
        & (d["close"] > d["ema_slow"])
        & (d["atr_pct_rank"] >= cfg.break_rank_min)
    )
    donch = (d["close"] > d["prior_high"]) & (d["close"].shift(1) <= d["prior_high_prev"])
    out = d.copy()
    out["valid"] = valid
    out["sig_trend"] = (valid & reg_t & touch & htf_ok & cfg.enable_trend).fillna(False)
    out["sig_mr"] = (valid & reg_m & brk & htf_ok & cfg.enable_mr).fillna(False)
    out["sig_break"] = (valid & reg_b & donch & htf_ok & cfg.enable_break).fillna(False)
    return out


class FeatureStream:
    """O(1)-per-bar incremental twin of compute_indicators + compute_signals (verified equal in research/tests).

    Lets the Nautilus strategy compute features without any pre-built replay columns.
    """

    def __init__(self, cfg: Config) -> None:
        self.cfg = cfg
        self.n = 0
        self.prev = None
        self._tr_seed, self._pdm_seed, self._mdm_seed, self._dx_seed = [], [], [], []
        self._g_seed, self._l_seed = [], []
        self.atr = self.atr_n = self.pdm_s = self.mdm_s = self.adx = None
        self.rs_g = self.rs_l = None
        self.ema_f = self.ema_m = self.ema_s = self.ema_h = None
        self.closes = deque(maxlen=cfg.bb_period)
        self.qv = deque(maxlen=24)
        self.atr_pct_win = deque(maxlen=cfg.atr_pct_window)
        self.highs = deque(maxlen=cfg.break_lookback)
        self.prev_prior_high = None
        self.prev_bb_low = None
        self.prev_ema_f = None
        self.prev_close = None
        self._dx_n = 0

    @staticmethod
    def _wstep(prev, x, n):
        return prev + (x - prev) / n

    def push(self, o: float, h: float, l: float, c: float, v: float) -> dict:
        cfg = self.cfg
        i = self.n
        self.n += 1
        nan = float("nan")
        if self.prev is None:
            tr = h - l
            up = dn = 0.0
            pdm = mdm = 0.0
            gain = loss = 0.0
        else:
            pc, ph, pl = self.prev
            tr = max(h - l, abs(h - pc), abs(l - pc))
            up, dn = h - ph, pl - l
            pdm = up if (up > dn and up > 0) else 0.0
            mdm = dn if (dn > up and dn > 0) else 0.0
            d = c - pc
            gain, loss = max(d, 0.0), max(-d, 0.0)
        # Wilder smoothers (seed = mean of first n values)
        atr = self._wilder_push(i, tr, "atr", cfg.atr_period, self._tr_seed)
        atr_n = self._wilder_push(i, tr, "atr_n", cfg.adx_period, self._tr_seed2()) if cfg.adx_period != cfg.atr_period else atr
        pds = self._wilder_push(i, pdm, "pdm_s", cfg.adx_period, self._pdm_seed)
        mds = self._wilder_push(i, mdm, "mdm_s", cfg.adx_period, self._mdm_seed)
        rg = self._wilder_push(i, gain, "rs_g", cfg.rsi_period, self._g_seed)
        rl = self._wilder_push(i, loss, "rs_l", cfg.rsi_period, self._l_seed)
        pdi = mdi = adx = nan
        if atr_n is not None and pds is not None and mds is not None:
            pdi, mdi = 100.0 * pds / atr_n, 100.0 * mds / atr_n
            dx = 100.0 * abs(pdi - mdi) / (pdi + mdi) if (pdi + mdi) != 0 else nan
            if not math.isnan(dx):
                self._dx_n += 1
                if self.adx is None:
                    self._dx_seed.append(dx)
                    if len(self._dx_seed) == cfg.adx_period:
                        self.adx = sum(self._dx_seed) / cfg.adx_period
                else:
                    self.adx = self._wstep(self.adx, dx, cfg.adx_period)
        adx = self.adx if self.adx is not None else nan
        # EMAs (adjust=False)
        def ema(prev, span):
            a = 2.0 / (span + 1)
            return c if prev is None else a * c + (1 - a) * prev
        self.ema_f, self.ema_m, self.ema_s, self.ema_h = (ema(self.ema_f, cfg.ema_fast), ema(self.ema_m, cfg.ema_mid),
                                                         ema(self.ema_s, cfg.ema_slow), ema(self.ema_h, cfg.htf_span))
        self.closes.append(c)
        bb_low = nan
        if len(self.closes) == cfg.bb_period:
            arr = np.fromiter(self.closes, float)
            bb_low = float(arr.mean() - cfg.bb_std * arr.std(ddof=0))
        rsi = nan
        if rg is not None and rl is not None:
            rsi = 100.0 if rl == 0 else 100.0 - 100.0 / (1.0 + rg / rl)
        self.qv.append(c * v)
        qv24 = float(sum(self.qv)) if len(self.qv) == 24 else nan
        atr_pct = atr / c if atr is not None else nan
        rank = nan
        self.atr_pct_win.append(atr_pct)
        if len(self.atr_pct_win) == cfg.atr_pct_window:
            w = np.fromiter(self.atr_pct_win, float)
            if not np.isnan(w).any():
                rank = float((w <= atr_pct).mean())
        prior_high = max(self.highs) if len(self.highs) == cfg.break_lookback else nan
        htf = self.ema_h if i >= cfg.htf_span - 1 else nan
        atr_v = atr if atr is not None else nan

        row = dict(open=o, high=h, low=l, close=c, atr=atr_v, atr_pct=atr_pct, atr_pct_rank=rank, adx=adx, plus_di=pdi, minus_di=mdi,
                   ema_fast=self.ema_f, ema_mid=self.ema_m, ema_slow=self.ema_s, bb_low=bb_low, rsi=rsi, quote_vol_24h=qv24,
                   prior_high=prior_high, prior_high_prev=self.prev_prior_high if self.prev_prior_high is not None else nan,
                   ema_htf=htf)
        needed = ["atr", "adx", "plus_di", "minus_di", "ema_fast", "ema_mid", "ema_slow", "atr_pct_rank", "bb_low", "rsi"]
        if cfg.htf_filter:
            needed.append("ema_htf")
        valid = all(not math.isnan(row[k]) for k in needed)
        htf_ok = (c > htf) if (cfg.htf_filter and not math.isnan(htf)) else (not cfg.htf_filter)
        first = self.prev_close is None
        pc_ = self.prev_close
        reg_t = (adx >= cfg.adx_trend_min and pdi > mdi and self.ema_m > self.ema_s and c > self.ema_s and rank >= cfg.atr_pct_rank_min) if valid else False
        touch = (not first) and c <= self.ema_f and pc_ > self.prev_ema_f and c > self.ema_m
        reg_m = (adx < cfg.adx_range_max and cfg.atr_pct_rank_min <= rank <= cfg.atr_pct_rank_max_mr) if valid else False
        brk = (not first) and (not math.isnan(bb_low)) and self.prev_bb_low is not None and not math.isnan(self.prev_bb_low) \
            and c < bb_low and pc_ >= self.prev_bb_low and rsi < cfg.rsi_mr_max
        reg_b = (adx >= cfg.adx_trend_min and pdi > mdi and c > self.ema_s and rank >= cfg.break_rank_min) if valid else False
        pph = row["prior_high_prev"]
        donch = (not math.isnan(prior_high)) and (not math.isnan(pph)) and c > prior_high and pc_ is not None and pc_ <= pph
        row["valid"] = valid
        row["sig_trend"] = bool(valid and reg_t and touch and htf_ok and cfg.enable_trend)
        row["sig_mr"] = bool(valid and reg_m and brk and htf_ok and cfg.enable_mr)
        row["sig_break"] = bool(valid and reg_b and donch and htf_ok and cfg.enable_break)
        # roll state
        self.highs.append(h)
        self.prev_prior_high = prior_high
        self.prev_bb_low = bb_low
        self.prev_ema_f = self.ema_f
        self.prev_close = c
        self.prev = (c, h, l)
        return row

    def _tr_seed2(self):
        if not hasattr(self, "_tr_seed_b"):
            self._tr_seed_b = []
        return self._tr_seed_b

    def _wilder_push(self, i, x, name, n, seed_list):
        cur = getattr(self, name)
        if cur is None:
            seed_list.append(x)
            if len(seed_list) == n:
                cur = sum(seed_list) / n
                setattr(self, name, cur)
            return cur
        cur = self._wstep(cur, x, n)
        setattr(self, name, cur)
        return cur


def floor_to_step(x: float, step: float) -> float:
    if step <= 0:
        return x
    return math.floor(round(x / step, 9)) * step


def ceil_to_step(x: float, step: float) -> float:
    if step <= 0:
        return x
    return math.ceil(round(x / step, 9)) * step


@dataclass
class OrderPlan:
    ok: bool
    reason: str
    side: str = "long"
    module: str = ""
    limit_price: float = 0.0
    stop_price: float = 0.0
    tp_price: float = 0.0
    qty: float = 0.0
    notional: float = 0.0
    margin: float = 0.0
    stop_distance: float = 0.0
    risk_usdt: float = 0.0
    time_stop_hours: int = 0
    details: dict = field(default_factory=dict)


def settlements_between(start_ms: int, end_ms: int) -> int:
    """Number of 8h funding settlements (00/08/16 UTC) in (start_ms, end_ms]."""
    first = (start_ms // HOUR_MS) * HOUR_MS
    n = 0
    t = first
    while t <= end_ms:
        if t > start_ms and (t // HOUR_MS) % 24 in FUNDING_SETTLEMENT_HOURS_UTC:
            n += 1
        t += HOUR_MS
    return n


def in_funding_window(ts_ms: int, minutes: int) -> bool:
    """True when ts is within +-minutes of a settlement."""
    hour_ms = HOUR_MS
    day_ms = 24 * hour_ms
    pos = ts_ms % day_ms
    for h in FUNDING_SETTLEMENT_HOURS_UTC + (24,):
        if abs(pos - h * hour_ms) <= minutes * 60_000:
            return True
    return False


def build_plan(
    *,
    module: str,
    close: float,
    atr: float,
    decision_ts_ms: int,
    cfg: Config,
    tick: float,
    size_step: float,
    min_qty: float,
    min_notional: float,
    funding_rate: float,
) -> OrderPlan:
    """Turn a fired signal into a sized long limit order with attached stop and take-profit."""
    if not (math.isfinite(close) and math.isfinite(atr)) or atr <= 0 or close <= 0:
        return OrderPlan(False, REASON["SIGNAL_INVALID"])
    limit_price = floor_to_step(close, tick)
    stop_dist_raw = cfg.stop_atr_mult * atr
    stop_price = floor_to_step(limit_price - stop_dist_raw, tick)
    stop_dist = limit_price - stop_price
    if stop_price <= 0 or stop_dist <= 0:
        return OrderPlan(False, REASON["SIGNAL_INVALID"])
    tp_price = ceil_to_step(limit_price + cfg.tp_r_mult * stop_dist, tick)
    qty = floor_to_step(cfg.risk_usdt / stop_dist, size_step)
    hold_h = cfg.time_stop_hours_mr if module == "mr" else cfg.time_stop_hours_trend
    if qty < min_qty:
        return OrderPlan(False, REASON["SIZE_MIN"], details={"qty": qty})
    notional = qty * limit_price
    if notional < min_notional:
        return OrderPlan(False, REASON["SIZE_MIN"], details={"notional": notional})
    margin = notional / cfg.leverage
    if margin > cfg.margin_cap_usdt:
        return OrderPlan(False, REASON["SIZE_CAP"], details={"margin": margin})
    n_settle = settlements_between(decision_ts_ms, decision_ts_ms + hold_h * HOUR_MS)
    exp_funding = max(funding_rate, 0.0) * notional * n_settle
    if exp_funding > cfg.funding_cap_r * cfg.risk_usdt:
        return OrderPlan(False, REASON["FUNDING_COST"], details={"expected_funding": exp_funding})
    return OrderPlan(
        True,
        {"trend": REASON["REGIME_T"], "mr": REASON["REGIME_M"], "break": REASON["REGIME_B"]}[module],
        module=module,
        limit_price=limit_price,
        stop_price=stop_price,
        tp_price=tp_price,
        qty=qty,
        notional=notional,
        margin=margin,
        stop_distance=stop_dist,
        risk_usdt=qty * stop_dist,
        time_stop_hours=hold_h,
        details={"expected_funding": exp_funding, "n_settlements": n_settle},
    )


def blackout_for_order_bar(bar_open_ms: int, cfg: Config) -> bool:
    """True when an order resting during the bar [open, open+1h) overlaps a +-blackout window.

    Live trading cancels resting entries at the window start; the replay approximates this by
    forbidding fills in any bar that overlaps a window.
    """
    start, end = bar_open_ms, bar_open_ms + HOUR_MS
    day = 24 * HOUR_MS
    base = (bar_open_ms // day) * day
    for dd in (-day, 0, day):
        for h in FUNDING_SETTLEMENT_HOURS_UTC:
            t = base + dd + h * HOUR_MS
            ws, we = t - cfg.funding_blackout_min * 60_000, t + cfg.funding_blackout_min * 60_000
            if start < we and end > ws:
                return True
    return False


@dataclass
class RiskState:
    """Rebuilt each cycle from exchange fills; see main_live."""

    realised_today: float = 0.0
    realised_total: float = 0.0
    consecutive_losses: int = 0
    open_symbols: tuple = ()
    foreign_positions: tuple = ()
    stopped: bool = False


def risk_gate(state: RiskState, cfg: Config) -> Optional[str]:
    if state.foreign_positions:
        return REASON["HALT_FOREIGN"]
    if state.realised_total <= -cfg.stop_playbook_usdt:
        return REASON["STOP_PLAYBOOK"]
    if state.consecutive_losses >= cfg.max_consecutive_losses:
        return REASON["HALT_STREAK"]
    if state.realised_today <= -cfg.daily_pause_usdt:
        return REASON["DAILY_PAUSE"]
    return None


def cluster_gate(state: RiskState, symbol: str, cfg: Config) -> Optional[str]:
    """Sleeve A has a single correlation cluster (crypto majors), so one open/pending position blocks all symbols."""
    if symbol in state.open_symbols:
        return REASON["SYMBOL_OPEN"]
    if len(state.open_symbols) >= cfg.max_concurrent:
        return REASON["MAX_CONCURRENT"]
    if state.open_symbols:
        return REASON["CLUSTER"]
    return None
