"""Incremental indicators shared by the live path and the Nautilus replay.

Both paths feed closed 1H bars one at a time through ``IndicatorState`` so the
decision math is identical in backtest and live.
"""

from collections import deque
from dataclasses import dataclass
from typing import Optional

import numpy as np


@dataclass
class Snapshot:
    close: float
    atr: Optional[float]
    adx: Optional[float]
    plus_di: Optional[float]
    minus_di: Optional[float]
    ema_fast: Optional[float]
    ema_slow: Optional[float]
    atr_pct_rank: Optional[float]
    quote_volume_24h: Optional[float]
    bars_seen: int

    def ready(self) -> bool:
        return None not in (
            self.atr,
            self.adx,
            self.plus_di,
            self.minus_di,
            self.ema_fast,
            self.ema_slow,
            self.atr_pct_rank,
            self.quote_volume_24h,
        )


class IndicatorState:
    def __init__(
        self,
        atr_period: int,
        adx_period: int,
        ema_fast: int,
        ema_slow: int,
        atr_rank_window: int,
        volume_window: int = 24,
    ) -> None:
        self.atr_period = atr_period
        self.adx_period = adx_period
        self.ema_fast_n = ema_fast
        self.ema_slow_n = ema_slow
        self.atr_rank_window = atr_rank_window
        self.volume_window = volume_window

        self._prev_high: Optional[float] = None
        self._prev_low: Optional[float] = None
        self._prev_close: Optional[float] = None
        self._bars = 0

        self._tr_seed: list[float] = []
        self._atr: Optional[float] = None

        self._dm_seed: list[tuple[float, float, float]] = []
        self._sm_tr: Optional[float] = None
        self._sm_pdm: Optional[float] = None
        self._sm_mdm: Optional[float] = None
        self._dx_seed: list[float] = []
        self._adx: Optional[float] = None
        self._pdi: Optional[float] = None
        self._mdi: Optional[float] = None

        self._ema_f: Optional[float] = None
        self._ema_s: Optional[float] = None

        self._atr_pct_buf = np.full(atr_rank_window, np.nan)
        self._atr_pct_n = 0
        self._atr_pct_i = 0

        self._qv: deque[float] = deque(maxlen=volume_window)

    def update(self, high: float, low: float, close: float, volume: float) -> Snapshot:
        self._bars += 1
        self._update_ema(close)
        self._qv.append(volume * close)

        if self._prev_close is not None:
            tr = max(high - low, abs(high - self._prev_close), abs(low - self._prev_close))
            up = high - self._prev_high
            down = self._prev_low - low
            pdm = up if (up > down and up > 0) else 0.0
            mdm = down if (down > up and down > 0) else 0.0
            self._update_atr(tr)
            self._update_adx(tr, pdm, mdm)

        self._prev_high, self._prev_low, self._prev_close = high, low, close

        rank: Optional[float] = None
        if self._atr is not None and close > 0:
            atr_pct = self._atr / close
            self._atr_pct_buf[self._atr_pct_i] = atr_pct
            self._atr_pct_i = (self._atr_pct_i + 1) % self.atr_rank_window
            self._atr_pct_n = min(self._atr_pct_n + 1, self.atr_rank_window)
            if self._atr_pct_n >= self.atr_rank_window:
                rank = float(np.count_nonzero(self._atr_pct_buf <= atr_pct)) / self.atr_rank_window * 100.0

        qv24 = float(sum(self._qv)) if len(self._qv) >= self.volume_window else None
        return Snapshot(
            close=close,
            atr=self._atr,
            adx=self._adx,
            plus_di=self._pdi,
            minus_di=self._mdi,
            ema_fast=self._ema_f if self._bars >= self.ema_slow_n else None,
            ema_slow=self._ema_s if self._bars >= self.ema_slow_n else None,
            atr_pct_rank=rank,
            quote_volume_24h=qv24,
            bars_seen=self._bars,
        )

    def _update_ema(self, close: float) -> None:
        af = 2.0 / (self.ema_fast_n + 1)
        a_s = 2.0 / (self.ema_slow_n + 1)
        self._ema_f = close if self._ema_f is None else af * close + (1 - af) * self._ema_f
        self._ema_s = close if self._ema_s is None else a_s * close + (1 - a_s) * self._ema_s

    def _update_atr(self, tr: float) -> None:
        n = self.atr_period
        if self._atr is None:
            self._tr_seed.append(tr)
            if len(self._tr_seed) == n:
                self._atr = sum(self._tr_seed) / n
                self._tr_seed = []
            return
        self._atr = (self._atr * (n - 1) + tr) / n

    def _update_adx(self, tr: float, pdm: float, mdm: float) -> None:
        n = self.adx_period
        if self._sm_tr is None:
            self._dm_seed.append((tr, pdm, mdm))
            if len(self._dm_seed) < n:
                return
            self._sm_tr = sum(x[0] for x in self._dm_seed)
            self._sm_pdm = sum(x[1] for x in self._dm_seed)
            self._sm_mdm = sum(x[2] for x in self._dm_seed)
            self._dm_seed = []
        else:
            self._sm_tr = self._sm_tr - self._sm_tr / n + tr
            self._sm_pdm = self._sm_pdm - self._sm_pdm / n + pdm
            self._sm_mdm = self._sm_mdm - self._sm_mdm / n + mdm

        if not self._sm_tr:
            return
        pdi = 100.0 * self._sm_pdm / self._sm_tr
        mdi = 100.0 * self._sm_mdm / self._sm_tr
        self._pdi, self._mdi = pdi, mdi
        denom = pdi + mdi
        dx = 100.0 * abs(pdi - mdi) / denom if denom > 0 else 0.0
        if self._adx is None:
            self._dx_seed.append(dx)
            if len(self._dx_seed) == n:
                self._adx = sum(self._dx_seed) / n
                self._dx_seed = []
            return
        self._adx = (self._adx * (n - 1) + dx) / n
