"""Shared indicator math for Sleeve A BTC long v1.

Pure-Python Wilder-style indicators so the Nautilus strategy (backtest) and
the live decision path use identical formulas. No third-party imports.
"""

from typing import List, Optional


def ema_update(prev: Optional[float], value: float, period: int) -> float:
    if prev is None:
        return value
    alpha = 2.0 / (period + 1)
    return alpha * value + (1.0 - alpha) * prev


class WilderState:
    """Incremental ATR / ADX / RSI state (Wilder smoothing)."""

    def __init__(self, atr_period: int = 14, adx_period: int = 14, rsi_period: int = 14) -> None:
        self.atr_period = atr_period
        self.adx_period = adx_period
        self.rsi_period = rsi_period
        self.prev_close: Optional[float] = None
        self.prev_high: Optional[float] = None
        self.prev_low: Optional[float] = None
        self.atr: Optional[float] = None
        self.plus_dm_smooth: Optional[float] = None
        self.minus_dm_smooth: Optional[float] = None
        self.adx: Optional[float] = None
        self._dx_count: int = 0
        self.avg_gain: Optional[float] = None
        self.avg_loss: Optional[float] = None
        self.rsi: Optional[float] = None
        self.bars_seen: int = 0
        self.atr_pct_history: List[float] = []

    def update(self, high: float, low: float, close: float):
        self.bars_seen += 1
        if self.prev_close is None:
            self.prev_close = close
            self.prev_high = high
            self.prev_low = low
            return None
        tr = max(
            high - low,
            abs(high - self.prev_close),
            abs(low - self.prev_close),
        )
        up_move = high - (self.prev_high or high)
        down_move = (self.prev_low if self.prev_low is not None else low) - low
        plus_dm = up_move if (up_move > down_move and up_move > 0) else 0.0
        minus_dm = down_move if (down_move > up_move and down_move > 0) else 0.0
        change = close - self.prev_close
        gain = change if change > 0 else 0.0
        loss = -change if change < 0 else 0.0
        n_atr = self.atr_period
        if self.atr is None:
            self.atr = tr
            self.plus_dm_smooth = plus_dm
            self.minus_dm_smooth = minus_dm
            self.avg_gain = gain
            self.avg_loss = loss
        else:
            self.atr = (self.atr * (n_atr - 1) + tr) / n_atr
            self.plus_dm_smooth = (self.plus_dm_smooth * (n_atr - 1) + plus_dm) / n_atr
            self.minus_dm_smooth = (self.minus_dm_smooth * (n_atr - 1) + minus_dm) / n_atr
            self.avg_gain = (self.avg_gain * (self.rsi_period - 1) + gain) / self.rsi_period
            self.avg_loss = (self.avg_loss * (self.rsi_period - 1) + loss) / self.rsi_period
        self.prev_close = close
        self.prev_high = high
        self.prev_low = low
        if self.atr and self.atr > 0:
            if self.plus_dm_smooth is not None and self.minus_dm_smooth is not None:
                plus_di = 100.0 * self.plus_dm_smooth / self.atr
                minus_di = 100.0 * self.minus_dm_smooth / self.atr
                denom = plus_di + minus_di
                dx = (100.0 * abs(plus_di - minus_di) / denom) if denom > 0 else 0.0
                if self.adx is None:
                    self._dx_count += 1
                    if self._dx_count >= self.adx_period:
                        self.adx = dx
                else:
                    self.adx = (self.adx * (self.adx_period - 1) + dx) / self.adx_period
        if self.avg_loss is not None:
            if self.avg_loss == 0:
                self.rsi = 100.0 if (self.avg_gain or 0) > 0 else 50.0
            else:
                rs = (self.avg_gain or 0.0) / self.avg_loss
                self.rsi = 100.0 - (100.0 / (1.0 + rs))
        atr_pct = (self.atr / close * 100.0) if (self.atr and close) else None
        if atr_pct is not None:
            self.atr_pct_history.append(atr_pct)
        return {"atr": self.atr, "adx": self.adx, "rsi": self.rsi, "atr_pct": atr_pct}

    def atr_pct_percentile(self, lookback: int) -> Optional[float]:
        hist = self.atr_pct_history[-lookback:] if lookback > 0 else list(self.atr_pct_history)
        if len(hist) < 10:
            return None
        current = hist[-1]
        le_count = sum(1 for v in hist if v <= current)
        return 100.0 * le_count / len(hist)

    def ready(self, ema_slow: int, atr_pct_lookback: int) -> bool:
        warmup = max(ema_slow + 1, self.adx_period * 2 + 1, 20)
        if self.bars_seen < warmup:
            return False
        if self.adx is None or self.atr is None or self.rsi is None:
            return False
        if len(self.atr_pct_history) < min(atr_pct_lookback, 50):
            return False
        return True
