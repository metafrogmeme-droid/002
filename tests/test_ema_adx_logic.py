"""Decision-rule tests. These do not produce a backtest and do not import Nautilus."""

import math
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

import yaml

PACKAGE = Path("/workspace/playbooks/usdt-m-ema-adx-long")
sys.path.insert(0, str(PACKAGE / "src"))

from indicators import IndicatorBook, batch_last  # noqa: E402
from logic import AccountState, Snapshot, decide  # noqa: E402
from params import ConfigError, load_config  # noqa: E402
from report import activation_verdict  # noqa: E402
from risk import (  # noqa: E402
    ClosedTrade,
    exposure_hits_blackout,
    funding_page_ignores_window,
    funding_rate_from_managed,
    funding_series_gap_ms,
    in_funding_blackout,
    plan_long_size,
)


def _config():
    manifest = yaml.safe_load((PACKAGE / "manifest.yaml").read_text(encoding="utf-8"))
    return load_config(manifest["strategy_config"])


def _account(**overrides):
    base = dict(
        open_positions=0,
        symbol_busy=False,
        daily_realised=0.0,
        cumulative_realised=0.0,
        consecutive_losses=0,
        margin_remaining=3000.0,
        ticker_age_seconds=1.0,
        apply_ticker_staleness=False,
    )
    base.update(overrides)
    return AccountState(**base)


def _snapshot(**overrides):
    base = dict(
        symbol="BTCUSDT",
        close_ts=datetime(2026, 6, 1, 3, 0, tzinfo=timezone.utc),
        close=100.0,
        atr=2.0,
        atr_pct=50.0,
        adx=30.0,
        plus_di=25.0,
        minus_di=15.0,
        fast_ema=101.0,
        slow_ema=100.0,
        prev_fast_ema=99.0,
        prev_slow_ema=100.0,
        volume=200.0,
        volume_avg_prev=100.0,
        funding_rate=0.0001,
        price_tick=0.1,
        size_step=0.0001,
        min_qty=0.0001,
    )
    base.update(overrides)
    return Snapshot(**base)


class IndicatorTests(unittest.TestCase):
    def test_incremental_book_matches_batch_last(self):
        count = 240
        closes = []
        price = 100.0
        for index in range(count):
            price += math.sin(index / 7.0) + 0.15
            closes.append(price)
        highs = [close + 0.8 + (index % 3) * 0.1 for index, close in enumerate(closes)]
        lows = [close - 0.7 - (index % 4) * 0.05 for index, close in enumerate(closes)]
        volumes = [100.0 + (index % 11) * 3.0 for index in range(count)]
        kwargs = dict(
            ema_fast=8,
            ema_slow=20,
            adx_period=7,
            atr_period=7,
            atr_pct_lookback=30,
            volume_avg_bars=5,
        )
        book = IndicatorBook(**kwargs)
        latest = None
        for high, low, close, volume in zip(highs, lows, closes, volumes):
            latest = book.update(high, low, close, volume)
        oracle = batch_last(highs, lows, closes, volumes, **kwargs)
        self.assertIsNotNone(latest)
        for key, expected in oracle.items():
            actual = latest[key]
            if expected is None:
                self.assertIsNone(actual, key)
            else:
                self.assertIsNotNone(actual, key)
                self.assertAlmostEqual(actual, expected, places=8, msg=key)


class DecisionTests(unittest.TestCase):
    def test_valid_cross_is_long_and_risk_is_capped(self):
        cfg = _config()
        decision = decide(_snapshot(), cfg, _account())
        self.assertEqual(decision.action, "long")
        self.assertEqual(decision.side, "long")
        self.assertLessEqual(decision.risk_usdt, 15.0)
        self.assertGreater(decision.qty, 0)

    def test_missing_funding_is_no_trade(self):
        decision = decide(_snapshot(funding_rate=None), _config(), _account())
        self.assertEqual(decision.action, "hold")
        self.assertEqual(decision.side, "none")
        self.assertEqual(decision.reason_code, "INVALID_SIGNAL")

    def test_nan_indicator_is_no_trade(self):
        decision = decide(_snapshot(adx=float("nan")), _config(), _account())
        self.assertEqual(decision.action, "hold")
        self.assertNotEqual(decision.side, "long")
        self.assertEqual(decision.reason_code, "INVALID_SIGNAL")

    def test_down_cross_does_not_open_a_short(self):
        decision = decide(
            _snapshot(prev_fast_ema=101.0, prev_slow_ema=100.0, fast_ema=99.0, slow_ema=100.0),
            _config(),
            _account(),
        )
        self.assertEqual(decision.action, "hold")
        self.assertEqual(decision.reason_code, "SHORTS_DISABLED")

    def test_low_adx_is_sat_out(self):
        decision = decide(_snapshot(adx=10.0), _config(), _account())
        self.assertEqual(decision.reason_code, "FILTER_REGIME_ADX")

    def test_config_rejects_a_missing_key(self):
        manifest = yaml.safe_load((PACKAGE / "manifest.yaml").read_text(encoding="utf-8"))
        raw = dict(manifest["strategy_config"])
        raw.pop("adx_min")
        with self.assertRaises(ConfigError):
            load_config(raw)


class RiskTests(unittest.TestCase):
    def test_size_floors_risk_to_fifteen(self):
        plan = plan_long_size(
            close=100.04,
            atr=1.37,
            atr_stop_mult=1.5,
            reward_r=2.0,
            fixed_loss_usdt=15.0,
            price_tick=0.1,
            size_step=0.0001,
            min_qty=0.0001,
            min_notional_usdt=5.0,
            leverage=5,
            margin_remaining=3000.0,
        )
        self.assertEqual(plan.reason, "TRIGGER_LONG")
        self.assertLessEqual(float(plan.risk_usdt), 15.0)
        self.assertGreater(float(plan.risk_usdt), 0.0)
        self.assertGreater(float(plan.take_profit), float(plan.entry))

    def test_blackout_boundaries(self):
        inside = datetime(2026, 10, 9, 0, 15, 0, tzinfo=timezone.utc)
        outside = datetime(2026, 10, 9, 0, 15, 1, tzinfo=timezone.utc)
        before_midnight = datetime(2026, 10, 8, 23, 45, 0, tzinfo=timezone.utc)
        self.assertTrue(in_funding_blackout(inside, 15))
        self.assertFalse(in_funding_blackout(outside, 15))
        self.assertTrue(in_funding_blackout(before_midnight, 15))
        self.assertTrue(in_funding_blackout(datetime(2026, 10, 9, 8, 0, tzinfo=timezone.utc), 15))
        self.assertFalse(in_funding_blackout(datetime(2026, 10, 9, 3, 0, tzinfo=timezone.utc), 15))

    def test_managed_funding_percent_display_is_scaled(self):
        decimal_rate = funding_rate_from_managed(0.004)
        self.assertAlmostEqual(decimal_rate, 0.00004)
        self.assertLess(decimal_rate, 0.0003)
        self.assertGreater(0.004, 0.0003)

    def test_funding_gap_is_reported_and_not_filled(self):
        day = 24 * 60 * 60 * 1000
        daily = [0, day, 2 * day]
        self.assertIsNone(funding_series_gap_ms(daily, 36 * 60 * 60 * 1000))
        hole = [0, day, day + 48 * 60 * 60 * 1000]
        self.assertEqual(funding_series_gap_ms(hole, 36 * 60 * 60 * 1000), 48 * 60 * 60 * 1000)

    def test_repeated_latest_funding_page_is_not_coverage(self):
        # 2026-07-12T00:00:00Z against a cursor parked on that same instant.
        self.assertTrue(funding_page_ignores_window(1783814400000, 1791504000000, 1783814400000, 4 * 60 * 60 * 1000))
        # A page that actually starts before the requested end is usable.
        self.assertFalse(funding_page_ignores_window(1728432000000, 1733616000000, 1733616000000, 4 * 60 * 60 * 1000))

    def test_exposure_window_overlaps_funding(self):
        start = datetime(2026, 10, 9, 7, 0, tzinfo=timezone.utc)
        end = datetime(2026, 10, 9, 8, 0, tzinfo=timezone.utc)
        quiet_start = datetime(2026, 10, 9, 1, 0, tzinfo=timezone.utc)
        quiet_end = datetime(2026, 10, 9, 2, 0, tzinfo=timezone.utc)
        self.assertTrue(exposure_hits_blackout(start, end, 15))
        self.assertFalse(exposure_hits_blackout(quiet_start, quiet_end, 15))


class VerdictTests(unittest.TestCase):
    def test_negative_two_x_expectancy_does_not_activate(self):
        trade = ClosedTrade(
            symbol="BTCUSDT",
            entry_ts="2026-05-01T00:00:00+00:00",
            exit_ts="2026-05-01T04:00:00+00:00",
            side="long",
            qty=1.0,
            entry_price=100.0,
            exit_price=100.2,
            entry_fee_rate=0.0006,
            exit_fee_rate=0.0002,
            slippage_usdt=0.05,
            funding_usdt=0.0,
            funding_known=True,
            risk_usdt=15.0,
            reason_code="EXIT_TP",
        )
        from report import summarize

        full = summarize([trade], 1.0, 3000.0)
        cost_2x = summarize([trade], 2.0, 3000.0)
        self.assertEqual(full["status"], "OK")
        self.assertGreater(full["expectancy_r"], 0)
        self.assertLess(cost_2x["expectancy_r"], 0)
        verdict, reasons = activation_verdict(
            full=full,
            cost_2x=cost_2x,
            fee_tier_status="PENDING",
            engine_sharpe=1.0,
            live_trades=0,
        )
        self.assertEqual(verdict, "do_not_activate")
        self.assertIn("negative_or_missing_expectancy_at_2x_costs", reasons)
        self.assertIn("fee_tier_pending", reasons)
        self.assertIn("forward_sample_below_30", reasons)


if __name__ == "__main__":
    unittest.main()
