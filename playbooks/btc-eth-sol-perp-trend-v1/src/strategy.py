"""Nautilus replay strategy for the BTC/ETH/SOL perp trend Playbook.

The strategy mirrors the live rule set exactly:

* regime filter: ADX + rolling ATR/price percentile on the 1H bar
* trigger: EMA pullback-resume in the trend direction with volume confirmation
* entry: limit at the signal close, bracketed with an exchange-side stop and
  take-profit (Nautilus bracket order list), cancelled if unfilled after TTL
* risk: fixed USDT loss at the stop, leverage/margin cap, time stop, max
  concurrent positions, daily pause / stop, consecutive-loss halt
* costs: engine commissions (maker/taker from backtest.yaml) plus an explicit
  funding + taker-slippage model recorded per trade for net analytics

Every trade is logged with intended vs filled price, fees, funding, slippage,
and a reason code so main_backtest.py can compute net expectancy, walk-forward
folds, and cost sensitivity from real fills.
"""

import json
from decimal import Decimal
from pathlib import Path
from typing import Any, Optional

from nautilus_trader.config import StrategyConfig
from nautilus_trader.model.data import Bar, BarType
from nautilus_trader.model.enums import LiquiditySide, OrderSide, OrderType, TimeInForce
from nautilus_trader.model.events import OrderCanceled, OrderFilled
from nautilus_trader.model.identifiers import ClientOrderId, InstrumentId
from nautilus_trader.model.instruments import Instrument
from nautilus_trader.trading.strategy import Strategy

try:  # the replay engine may import this module as `strategy` or `src.strategy`
    from . import features as F
except ImportError:  # pragma: no cover - top-level import path
    import features as F  # type: ignore[no-redef]

# Populated in on_stop so main_backtest can read the trade log even when the
# engine imported this module under a different name (file fallback also exists).
LAST_RUN: dict[str, Any] = {}

OUTPUT_DIR = Path("/workspace/output")
CACHE_DIR = Path("/workspace/.replay_cache")
NS = 1_000_000_000


class PerpTrendStrategyConfig(StrategyConfig):
    instrument_id: Optional[InstrumentId] = None
    bar_type: Optional[BarType] = None
    instrument_ids: tuple[InstrumentId, ...] = ()
    bar_types: tuple[BarType, ...] = ()
    params_json: str = "{}"
    first_bar_open_ns: int = 0
    write_outputs: bool = True


class PerpTrendStrategy(Strategy):
    def __init__(self, config: PerpTrendStrategyConfig) -> None:
        super().__init__(config)
        self.cfg = config
        self.params = self._load_params(config.params_json)
        self._instruments: dict[InstrumentId, Instrument] = {}
        self._features: dict[InstrumentId, F.FeatureEngine] = {}
        self._funding: dict[str, dict[int, float]] = {}
        self._funding_sorted: dict[str, list[int]] = {}
        self._pending: dict[InstrumentId, dict[str, Any]] = {}
        self._open: dict[InstrumentId, dict[str, Any]] = {}
        self._entry_ids: dict[str, InstrumentId] = {}
        self._exit_reason_by_id: dict[str, str] = {}
        self._forced_reason: dict[InstrumentId, str] = {}
        self._ts_is_open: Optional[bool] = None
        self.trades: list[dict[str, Any]] = []
        self.actions: list[dict[str, Any]] = []
        self.open_at_end: list[dict[str, Any]] = []
        self.daily_pnl: dict[int, float] = {}
        self.consecutive_losses = 0
        self.halt_until_ts = 0
        self.entry_block_until_day = -1
        self.halt_events: list[dict[str, Any]] = []
        self.stats: dict[str, Any] = {
            "bars_processed": 0,
            "bars_warmed": 0,
            "regime_bars": {},
            "triggers_long": 0,
            "triggers_short": 0,
            "entries_submitted": 0,
            "entries_filled": 0,
            "entries_expired": 0,
            "skips": {},
            "funding_lookup_miss": 0,
            "funding_settlements_charged": 0,
            "first_bar_close_ts": None,
            "last_bar_close_ts": None,
            "first_eligible_close_ts": None,
            "ts_semantics": None,
        }
        self.feature_frames: dict[str, Any] = {}

    # ------------------------------------------------------------------ setup
    @staticmethod
    def _load_params(params_json: str) -> F.StrategyParams:
        cfg: dict[str, Any] = {}
        try:
            cfg = json.loads(params_json or "{}") or {}
        except (TypeError, ValueError):
            cfg = {}
        if not cfg:
            try:
                from getagent import runtime

                cfg = dict(runtime.manifest.get("strategy_config", {}) or {})
            except Exception:  # pragma: no cover - replay engine without runtime
                cfg = {}
        return F.StrategyParams.from_config(cfg)

    def set_feature_frames(self, feature_frames: dict[str, Any]) -> None:
        self.feature_frames = dict(feature_frames or {})

    @staticmethod
    def _as_instrument_id(value: Any) -> InstrumentId:
        return value if isinstance(value, InstrumentId) else InstrumentId.from_str(str(value))

    @staticmethod
    def _as_bar_type(value: Any) -> BarType:
        return value if isinstance(value, BarType) else BarType.from_str(str(value))

    def _resolve_instruments(self) -> list[InstrumentId]:
        ids = [self._as_instrument_id(v) for v in (self.cfg.instrument_ids or ())]
        if not ids and self.cfg.instrument_id is not None:
            ids = [self._as_instrument_id(self.cfg.instrument_id)]
        if not ids:
            ids = [inst.id for inst in self.cache.instruments()]
        return ids

    def _bar_type_for(self, instrument_id: InstrumentId) -> BarType:
        for raw in self.cfg.bar_types or ():
            bt = self._as_bar_type(raw)
            if bt.instrument_id == instrument_id:
                return bt
        if self.cfg.bar_type is not None:
            bt = self._as_bar_type(self.cfg.bar_type)
            if bt.instrument_id == instrument_id:
                return bt
        return BarType.from_str(f"{instrument_id}-1-HOUR-LAST-EXTERNAL")

    def _load_funding(self, instrument_id: InstrumentId) -> None:
        symbol = instrument_id.symbol.value
        table: dict[int, float] = {}
        frame = None
        for key, candidate in self.feature_frames.items():
            if str(key).split(".")[0] == symbol or str(key) == str(instrument_id):
                frame = candidate
                break
        if frame is not None and "funding_rate" in getattr(frame, "columns", []):
            series = frame["funding_rate"].dropna()
            for ts, value in series.items():
                table[int(ts.value // NS)] = float(value)
        if not table:
            path = CACHE_DIR / f"funding_{symbol}.json"
            if path.exists():
                try:
                    payload = json.loads(path.read_text(encoding="utf-8"))
                    table = {int(k): float(v) for k, v in payload.items()}
                except (ValueError, TypeError):
                    table = {}
        if not table:
            raise RuntimeError(
                f"funding_rate feature missing for {symbol}: replay requires funding data "
                "(feature frame or cache). Refusing to run with silently-disabled funding."
            )
        self._funding[symbol] = table
        self._funding_sorted[symbol] = sorted(table)

    def _funding_rate_at(self, symbol: str, ts_seconds: int) -> Optional[float]:
        keys = self._funding_sorted.get(symbol)
        if not keys:
            return None
        idx = F.bisect_right(keys, ts_seconds) - 1
        if idx < 0:
            return None
        key = keys[idx]
        if ts_seconds - key > 2 * 8 * 3600:
            self.stats["funding_lookup_miss"] += 1
            return None
        return self._funding[symbol][key]

    def on_start(self) -> None:
        for instrument_id in self._resolve_instruments():
            instrument = self.cache.instrument(instrument_id)
            if instrument is None:
                raise RuntimeError(f"instrument {instrument_id} missing from cache")
            self._instruments[instrument_id] = instrument
            self._features[instrument_id] = F.FeatureEngine(self.params)
            self._load_funding(instrument_id)
            self.subscribe_bars(self._bar_type_for(instrument_id))

    # -------------------------------------------------------------- helpers
    def _close_ts(self, bar: Bar) -> int:
        ts_event = int(bar.ts_event)
        if self._ts_is_open is None:
            first_open = int(self.cfg.first_bar_open_ns or 0)
            if first_open and ts_event == first_open:
                self._ts_is_open = True
            elif first_open and ts_event == first_open + F.INTERVAL_SECONDS * NS:
                self._ts_is_open = False
            else:
                self._ts_is_open = ts_event % (F.INTERVAL_SECONDS * NS) == 0 and first_open == 0
            self.stats["ts_semantics"] = "open_time" if self._ts_is_open else "close_time"
        close_ns = ts_event + (F.INTERVAL_SECONDS * NS if self._ts_is_open else 0)
        return close_ns // NS

    def _log(self, **record: Any) -> None:
        if len(self.actions) < 20000:
            self.actions.append(record)

    def _skip(self, code: str) -> None:
        self.stats["skips"][code] = self.stats["skips"].get(code, 0) + 1

    def _open_count(self) -> int:
        return len(self._open) + len(self._pending)

    def _entries_blocked(self, close_ts: int) -> Optional[str]:
        day = F.utc_day(close_ts)
        if close_ts < self.halt_until_ts:
            return F.RC_SKIP_HALTED
        if day <= self.entry_block_until_day:
            return F.RC_SKIP_HALTED
        if self.daily_pnl.get(day, 0.0) <= -self.params.daily_pause_loss_usdt:
            return F.RC_SKIP_DAILY_PAUSE
        return None

    # -------------------------------------------------------------- on_bar
    def on_bar(self, bar: Bar) -> None:
        instrument_id = bar.bar_type.instrument_id
        instrument = self._instruments.get(instrument_id)
        engine = self._features.get(instrument_id)
        if instrument is None or engine is None:
            return
        close_ts = self._close_ts(bar)
        self.stats["bars_processed"] += 1
        if self.stats["first_bar_close_ts"] is None:
            self.stats["first_bar_close_ts"] = close_ts
        self.stats["last_bar_close_ts"] = close_ts

        snap = engine.update(
            close_ts,
            float(bar.open),
            float(bar.high),
            float(bar.low),
            float(bar.close),
            float(bar.volume),
        )

        self._accrue_funding(instrument_id, instrument, close_ts, float(bar.close))
        self._manage_open(instrument_id, instrument, close_ts)
        self._manage_pending(instrument_id, instrument, close_ts)
        self._check_daily_stop(close_ts)

        if not snap.warmed:
            return
        self.stats["bars_warmed"] += 1
        if self.stats["first_eligible_close_ts"] is None:
            self.stats["first_eligible_close_ts"] = close_ts
        regime_counts = self.stats["regime_bars"]
        regime_counts[snap.regime] = regime_counts.get(snap.regime, 0) + 1

        side = None
        if snap.long_trigger and self.params.side_mode in ("long_only", "both"):
            side = "long"
            self.stats["triggers_long"] += 1
        elif snap.short_trigger and self.params.side_mode in ("short_only", "both"):
            side = "short"
            self.stats["triggers_short"] += 1
        if side is None:
            if snap.skip_reason == F.RC_SKIP_VOLUME:
                self._skip(F.RC_SKIP_VOLUME)
            return
        self._try_enter(instrument_id, instrument, snap, side)

    # -------------------------------------------------------------- entries
    def _try_enter(self, instrument_id: InstrumentId, instrument: Instrument, snap: F.BarSnapshot, side: str) -> None:
        p = self.params
        symbol = instrument_id.symbol.value
        close_ts = snap.close_ts
        base_log = {
            "ts": close_ts,
            "symbol": symbol,
            "side": side,
            "intended_price": snap.close,
            "adx": snap.adx,
            "atr": snap.atr,
            "atr_pct_rank": snap.atr_pct_rank,
            "volume_ratio": snap.volume_ratio,
        }
        if instrument_id in self._open or instrument_id in self._pending:
            self._skip(F.RC_SKIP_PENDING)
            return
        blocked = self._entries_blocked(close_ts)
        if blocked:
            self._skip(blocked)
            self._log(action="skip", reason_code=blocked, **base_log)
            return
        if self._open_count() >= p.max_concurrent_positions:
            self._skip(F.RC_SKIP_MAX_POSITIONS)
            self._log(action="skip", reason_code=F.RC_SKIP_MAX_POSITIONS, **base_log)
            return
        if F.in_funding_window(close_ts, p.funding_window_minutes):
            self._skip(F.RC_SKIP_FUNDING_WINDOW)
            self._log(action="skip", reason_code=F.RC_SKIP_FUNDING_WINDOW, **base_log)
            return
        funding_rate = self._funding_rate_at(symbol, close_ts)
        if F.funding_blocks_entry(side, funding_rate, p.max_funding_rate_pct):
            self._skip(F.RC_SKIP_FUNDING_RATE)
            self._log(action="skip", reason_code=F.RC_SKIP_FUNDING_RATE, funding_rate=funding_rate, **base_log)
            return
        if funding_rate is None:
            self.stats["entries_without_funding_read"] = self.stats.get("entries_without_funding_read", 0) + 1

        assert snap.atr is not None
        tick = float(instrument.price_increment)
        size_step = float(instrument.size_increment)
        # "At or better than signal price": rest one tick inside the signal close so
        # the order is a passive (maker) limit that must be traded through to fill.
        if side == "long":
            entry_price = F.quantize_down(snap.close, tick) - tick
        else:
            entry_price = F.quantize_down(snap.close, tick) + tick
            if entry_price <= snap.close + 1e-12:
                entry_price += tick
        stop_distance = F.quantize_nearest(p.stop_atr_multiple * snap.atr, tick)
        if stop_distance < tick:
            stop_distance = tick
        sizing = F.size_position(
            risk_usdt=p.risk_per_trade_usdt,
            stop_distance=stop_distance,
            price=entry_price,
            leverage=p.leverage,
            margin_cap_usdt=p.margin_budget / p.max_concurrent_positions,
            size_step=size_step,
            min_qty=size_step,
        )
        if not sizing["sizing_ok"]:
            self._skip(F.RC_SKIP_SIZE)
            self._log(action="skip", reason_code=F.RC_SKIP_SIZE, sizing=sizing, **base_log)
            return

        if side == "long":
            sl_price = entry_price - stop_distance
            tp_price = entry_price + p.take_profit_r * stop_distance
            order_side = OrderSide.BUY
        else:
            sl_price = entry_price + stop_distance
            tp_price = entry_price - p.take_profit_r * stop_distance
            order_side = OrderSide.SELL
        if sl_price <= 0:
            self._skip(F.RC_SKIP_SIZE)
            return

        qty = instrument.make_qty(Decimal(repr(round(sizing["qty"], 8))))
        order_list = self.order_factory.bracket(
            instrument_id=instrument_id,
            order_side=order_side,
            quantity=qty,
            entry_order_type=OrderType.LIMIT,
            entry_price=instrument.make_price(Decimal(repr(round(entry_price, 10)))),
            sl_trigger_price=instrument.make_price(Decimal(repr(round(sl_price, 10)))),
            tp_price=instrument.make_price(Decimal(repr(round(tp_price, 10)))),
            time_in_force=TimeInForce.GTC,
            tp_post_only=False,
        )
        entry_order, sl_order, tp_order = order_list.orders[0], order_list.orders[1], order_list.orders[2]
        rec = {
            "symbol": symbol,
            "side": side,
            "signal_ts": close_ts,
            "intended_price": entry_price,
            "stop_price": sl_price,
            "tp_price": tp_price,
            "stop_distance": stop_distance,
            "qty": float(qty),
            "risk_usdt": sizing["risk_usdt"],
            "notional_usdt": sizing["notional_usdt"],
            "margin_usdt": sizing["margin_usdt"],
            "size_reduced": sizing["size_reduced"],
            "atr_at_signal": snap.atr,
            "adx_at_signal": snap.adx,
            "atr_pct_rank_at_signal": snap.atr_pct_rank,
            "volume_ratio_at_signal": snap.volume_ratio,
            "funding_rate_at_signal": funding_rate,
            "funding_filter_applied": funding_rate is not None,
            "entry_order_id": entry_order.client_order_id.value,
            "fees_usdt": 0.0,
            "funding_usdt": 0.0,
            "slippage_usdt": 0.0,
            "funding_settlements": 0,
            "funding_estimated_settlements": 0,
        }
        self._pending[instrument_id] = rec
        self._entry_ids[entry_order.client_order_id.value] = instrument_id
        self._exit_reason_by_id[sl_order.client_order_id.value] = F.RC_EXIT_SL
        self._exit_reason_by_id[tp_order.client_order_id.value] = F.RC_EXIT_TP
        self.submit_order_list(order_list)
        self.stats["entries_submitted"] += 1
        self._log(
            action="entry_submit",
            reason_code=F.RC_ENTRY_SUBMIT,
            qty=float(qty),
            stop_price=sl_price,
            tp_price=tp_price,
            risk_usdt=sizing["risk_usdt"],
            margin_usdt=sizing["margin_usdt"],
            funding_rate=funding_rate,
            **base_log,
        )

    # ----------------------------------------------------------- management
    def _manage_pending(self, instrument_id: InstrumentId, instrument: Instrument, close_ts: int) -> None:
        rec = self._pending.get(instrument_id)
        if rec is None:
            return
        if close_ts - rec["signal_ts"] >= self.params.entry_ttl_hours * 3600:
            rec["expire_requested_ts"] = close_ts
            self.cancel_all_orders(instrument_id)

    def _manage_open(self, instrument_id: InstrumentId, instrument: Instrument, close_ts: int) -> None:
        rec = self._open.get(instrument_id)
        if rec is None or rec.get("exit_requested"):
            return
        # entry_fill_ts is the close of the fill bar; the fill happened somewhere in
        # the preceding hour, so exiting at (time_stop - 1) hours after that close
        # guarantees the position is flat no later than time_stop hours after the fill.
        if close_ts - rec["entry_fill_ts"] >= (self.params.time_stop_hours - 1) * 3600:
            self._force_exit(instrument_id, F.RC_EXIT_TIME, close_ts)

    def _force_exit(self, instrument_id: InstrumentId, reason: str, close_ts: int) -> None:
        rec = self._open.get(instrument_id)
        if rec is None or rec.get("exit_requested"):
            return
        rec["exit_requested"] = True
        rec["exit_requested_ts"] = close_ts
        self._forced_reason[instrument_id] = reason
        self.cancel_all_orders(instrument_id)
        for position in self.cache.positions_open(instrument_id=instrument_id):
            self.close_position(position)

    def _check_daily_stop(self, close_ts: int) -> None:
        day = F.utc_day(close_ts)
        if self.daily_pnl.get(day, 0.0) <= -self.params.daily_stop_loss_usdt and self.entry_block_until_day < day:
            self.entry_block_until_day = day
            self.halt_events.append({"ts": close_ts, "reason_code": F.RC_HALT_DAILY_STOP, "daily_pnl": self.daily_pnl.get(day)})
            self._log(action="halt", reason_code=F.RC_HALT_DAILY_STOP, ts=close_ts, symbol="*", side="", pnl_usdt=self.daily_pnl.get(day))
            for instrument_id in list(self._pending):
                self.cancel_all_orders(instrument_id)
            for instrument_id in list(self._open):
                self._force_exit(instrument_id, F.RC_EXIT_DAILY_STOP, close_ts)

    def _accrue_funding(self, instrument_id: InstrumentId, instrument: Instrument, close_ts: int, close: float) -> None:
        rec = self._open.get(instrument_id)
        if rec is None or not F.is_funding_settlement(close_ts):
            return
        rate = self._funding_rate_at(rec["symbol"], close_ts)
        if rate is None:
            # No historical funding row: charge the labelled fallback rate against
            # the position and count it so the report shows how much cost is estimated.
            rate = self.params.funding_fallback_rate_pct / 100.0 * (1.0 if rec["side"] == "long" else -1.0)
            rec["funding_estimated_settlements"] += 1
            self.stats["funding_settlements_estimated"] = self.stats.get("funding_settlements_estimated", 0) + 1
        sign = 1.0 if rec["side"] == "long" else -1.0
        rec["funding_usdt"] += sign * rate * rec["qty"] * close
        rec["funding_settlements"] += 1
        self.stats["funding_settlements_charged"] += 1

    # ---------------------------------------------------------------- events
    def on_order_filled(self, event: OrderFilled) -> None:
        instrument_id = event.instrument_id
        instrument = self._instruments.get(instrument_id)
        if instrument is None:
            return
        fill_px = float(event.last_px)
        fill_qty = float(event.last_qty)
        commission = float(event.commission.as_double()) if event.commission is not None else 0.0
        # Fill events carry the bar's ts_event; normalise to the close of that bar
        # when bars are stamped by open time so all timestamps share one convention.
        ts = int(event.ts_event) // NS + (F.INTERVAL_SECONDS if self._ts_is_open else 0)
        oid = event.client_order_id.value

        if oid in self._entry_ids:
            rec = self._pending.pop(instrument_id, None)
            if rec is None:
                return
            rec["entry_fill_ts"] = ts
            rec["entry_fill_price"] = fill_px
            rec["qty_filled"] = fill_qty
            rec["fees_usdt"] += commission
            rec["entry_liquidity"] = str(event.liquidity_side)
            self._open[instrument_id] = rec
            self.stats["entries_filled"] += 1
            self._log(
                action="entry_fill",
                reason_code=F.RC_ENTRY_FILL,
                ts=ts,
                symbol=rec["symbol"],
                side=rec["side"],
                intended_price=rec["intended_price"],
                filled_price=fill_px,
                qty=fill_qty,
                fee_usdt=commission,
            )
            return

        rec = self._open.get(instrument_id)
        if rec is None:
            return
        reason = self._exit_reason_by_id.pop(oid, None) or self._forced_reason.pop(instrument_id, None) or "EXIT_OTHER"
        tick = float(instrument.price_increment)
        is_taker = event.liquidity_side == LiquiditySide.TAKER
        slippage = (self.params.slippage_ticks * tick * fill_qty) if is_taker else 0.0
        direction = 1.0 if rec["side"] == "long" else -1.0
        gross = direction * (fill_px - rec["entry_fill_price"]) * fill_qty
        rec["fees_usdt"] += commission
        rec["slippage_usdt"] += slippage
        rec["exit_ts"] = ts
        rec["exit_fill_price"] = fill_px
        rec["exit_reason"] = reason
        rec["exit_liquidity"] = str(event.liquidity_side)
        rec["gross_pnl_usdt"] = gross
        rec["engine_net_pnl_usdt"] = gross - rec["fees_usdt"]
        rec["net_pnl_usdt"] = gross - rec["fees_usdt"] - rec["funding_usdt"] - rec["slippage_usdt"]
        rec["total_cost_usdt"] = rec["fees_usdt"] + rec["funding_usdt"] + rec["slippage_usdt"]
        rec["r_multiple"] = rec["net_pnl_usdt"] / rec["risk_usdt"] if rec["risk_usdt"] else 0.0
        rec["bars_held"] = max(0, (ts - rec["entry_fill_ts"]) // F.INTERVAL_SECONDS)
        self._open.pop(instrument_id, None)
        self.trades.append(rec)

        day = F.utc_day(ts)
        self.daily_pnl[day] = self.daily_pnl.get(day, 0.0) + rec["net_pnl_usdt"]
        if rec["net_pnl_usdt"] < 0:
            self.consecutive_losses += 1
            if self.consecutive_losses >= self.params.max_consecutive_losses:
                self.halt_until_ts = ts + 24 * 3600
                self.halt_events.append({"ts": ts, "reason_code": F.RC_HALT_CONSEC_LOSS, "losses": self.consecutive_losses})
                self._log(action="halt", reason_code=F.RC_HALT_CONSEC_LOSS, ts=ts, symbol="*", side="", note="entries blocked 24h in replay; sticky in live")
                self.consecutive_losses = 0
        else:
            self.consecutive_losses = 0
        self._log(
            action="exit_fill",
            reason_code=reason,
            ts=ts,
            symbol=rec["symbol"],
            side=rec["side"],
            intended_price=rec["tp_price"] if reason == F.RC_EXIT_TP else rec["stop_price"] if reason == F.RC_EXIT_SL else None,
            filled_price=fill_px,
            qty=fill_qty,
            fee_usdt=commission,
            funding_usdt=rec["funding_usdt"],
            slippage_usdt=slippage,
            pnl_usdt=rec["net_pnl_usdt"],
            r_multiple=rec["r_multiple"],
        )

    def on_order_canceled(self, event: OrderCanceled) -> None:
        oid = event.client_order_id.value
        instrument_id = self._entry_ids.get(oid)
        if instrument_id is None:
            return
        rec = self._pending.pop(instrument_id, None)
        if rec is None:
            return
        self.stats["entries_expired"] += 1
        self._log(
            action="entry_cancel",
            reason_code=F.RC_ENTRY_EXPIRED,
            ts=int(event.ts_event) // NS,
            symbol=rec["symbol"],
            side=rec["side"],
            intended_price=rec["intended_price"],
        )

    # ----------------------------------------------------------------- stop
    def on_stop(self) -> None:
        last_ts = self.stats.get("last_bar_close_ts")
        for instrument_id, rec in list(self._open.items()):
            engine = self._features.get(instrument_id)
            mark = engine.last.close if engine and engine.last else rec["entry_fill_price"]
            direction = 1.0 if rec["side"] == "long" else -1.0
            rec["open_at_end"] = True
            rec["mark_price"] = mark
            rec["unrealized_gross_usdt"] = direction * (mark - rec["entry_fill_price"]) * rec["qty"]
            rec["exit_reason"] = F.RC_EXIT_END
            self.open_at_end.append(rec)
        for instrument_id in self._instruments:
            self.cancel_all_orders(instrument_id)
            self.close_all_positions(instrument_id)
        payload = {
            "params": self.params.__dict__,
            "trades": self.trades,
            "open_at_end": self.open_at_end,
            "actions": self.actions[-3000:],
            "actions_total": len(self.actions),
            "stats": self.stats,
            "daily_pnl": {str(k): v for k, v in self.daily_pnl.items()},
            "halt_events": self.halt_events,
        }
        LAST_RUN.clear()
        LAST_RUN.update(payload)
        if self.cfg.write_outputs:
            try:
                OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
                (OUTPUT_DIR / "trade_log.json").write_text(json.dumps(payload, default=str), encoding="utf-8")
            except OSError:
                pass
