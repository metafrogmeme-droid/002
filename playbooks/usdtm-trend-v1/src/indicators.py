"""Pure indicator math for the USDT-M Trend v1 Playbook.

No third-party imports. Both the Nautilus backtest strategy
(`strategy.py`) and the live decision path (`main.py`) use these
helpers so historical and live signals share one definition.
"""

from decimal import Decimal


def ema_series(closes, period):
    """Return the EMA series for a list of closes (floats)."""
    if not closes or period <= 0:
        return []
    alpha = 2.0 / (period + 1)
    out = []
    value = float(closes[0])
    out.append(value)
    for price in closes[1:]:
        value = alpha * float(price) + (1.0 - alpha) * value
        out.append(value)
    return out


class TrendState:
    """Incremental EMA / Wilder ATR / Wilder ADX / volume-ratio state.

    Feeding bars oldest-first keeps every value identical between the
    historical replay and the live path for the same bar sequence.
    """

    def __init__(self, ema_fast=20, ema_slow=50, adx_period=14,
                 atr_period=14, volume_lookback=20, atr_rank_lookback=100):
        self.ema_fast_p = ema_fast
        self.ema_slow_p = ema_slow
        self.adx_p = adx_period
        self.atr_p = atr_period
        self.vol_n = volume_lookback
        self.rank_n = atr_rank_lookback
        self.closes = []
        self.ema_fast = None
        self.ema_slow = None
        self.prev_close = None
        self.atr = None
        self.plus_dm_smooth = None
        self.minus_dm_smooth = None
        self.adx = None
        self.adx_bars = 0
        self.dx_seed = []
        self.volumes = []
        self.atr_pct_hist = []

    def update(self, high, low, close, volume):
        high = float(high)
        low = float(low)
        close = float(close)
        volume = float(volume)
        self.closes.append(close)
        self.volumes.append(volume)

        alpha_fast = 2.0 / (self.ema_fast_p + 1)
        alpha_slow = 2.0 / (self.ema_slow_p + 1)
        self.ema_fast = close if self.ema_fast is None else alpha_fast * close + (1 - alpha_fast) * self.ema_fast
        self.ema_slow = close if self.ema_slow is None else alpha_slow * close + (1 - alpha_slow) * self.ema_slow

        if self.prev_close is None:
            self.prev_close = close
            return self.snapshot(ready=False)

        prev_close = self.prev_close
        tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
        up_move = high - self._prev_high if hasattr(self, "_prev_high") else 0.0
        down_move = self._prev_low - low if hasattr(self, "_prev_low") else 0.0
        self._prev_high = high
        self._prev_low = low
        plus_dm = up_move if (up_move > down_move and up_move > 0) else 0.0
        minus_dm = down_move if (down_move > up_move and down_move > 0) else 0.0

        n_atr = self.atr_p
        if self.atr is None:
            self.atr = tr
            self.plus_dm_smooth = plus_dm
            self.minus_dm_smooth = minus_dm
        else:
            self.atr = (self.atr * (n_atr - 1) + tr) / n_atr
            self.plus_dm_smooth = (self.plus_dm_smooth * (n_atr - 1) + plus_dm) / n_atr
            self.minus_dm_smooth = (self.minus_dm_smooth * (n_atr - 1) + minus_dm) / n_atr

        if self.atr and self.atr > 0:
            plus_di = 100.0 * self.plus_dm_smooth / self.atr
            minus_di = 100.0 * self.minus_dm_smooth / self.atr
            di_sum = plus_di + minus_di
            dx = 100.0 * abs(plus_di - minus_di) / di_sum if di_sum > 0 else 0.0
            n_adx = self.adx_p
            if self.adx is None:
                self.dx_seed.append(dx)
                if len(self.dx_seed) >= n_adx:
                    self.adx = sum(self.dx_seed) / len(self.dx_seed)
                    self.adx_bars = len(self.dx_seed)
            else:
                self.adx = (self.adx * (n_adx - 1) + dx) / n_adx
                self.adx_bars += 1
            atr_pct = self.atr / close if close > 0 else 0.0
            self.atr_pct_hist.append(atr_pct)
            if len(self.atr_pct_hist) > self.rank_n:
                self.atr_pct_hist = self.atr_pct_hist[-self.rank_n:]

        self.prev_close = close
        return self.snapshot()

    def snapshot(self, ready=None):
        vol_ratio = None
        if len(self.volumes) > self.vol_n:
            mean_vol = sum(self.volumes[-self.vol_n - 1:-1]) / self.vol_n
            vol_ratio = (self.volumes[-1] / mean_vol) if mean_vol > 0 else None
        atr_pct_rank = None
        if self.atr_pct_hist:
            current = self.atr_pct_hist[-1]
            below = sum(1 for v in self.atr_pct_hist if v <= current)
            atr_pct_rank = below / len(self.atr_pct_hist)
        atr_pct = self.atr_pct_hist[-1] if self.atr_pct_hist else None
        warmup = max(self.ema_slow_p, self.adx_p * 2 + 1, self.vol_n + 1, self.atr_p + 1)
        is_ready = len(self.closes) >= warmup and self.adx is not None
        return {
            "bars": len(self.closes),
            "ready": is_ready if ready is None else ready and is_ready,
            "close": self.closes[-1] if self.closes else None,
            "ema_fast": self.ema_fast,
            "ema_slow": self.ema_slow,
            "adx": self.adx,
            "atr": self.atr,
            "atr_pct": atr_pct,
            "atr_pct_rank": atr_pct_rank,
            "volume_ratio": vol_ratio,
        }


def crossed_up(fast_now, slow_now, fast_prev, slow_prev):
    return fast_prev <= slow_prev and fast_now > slow_now


def quantize_to_step(price, step):
    """Round a trigger price down to the instrument price step."""
    price = Decimal(str(price))
    step = Decimal(str(step))
    if step <= 0:
        return price
    steps = (price // step)
    return steps * step
