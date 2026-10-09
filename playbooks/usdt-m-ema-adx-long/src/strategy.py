"""Nautilus replay strategy for the v1 long-only EMA-ADX playbook.

Stops and targets are submitted with the entry as a bracket. If that attached
order cannot be created, the strategy does not open a naked position.
"""

import json
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pandas as pd
from nautilus_trader.config import StrategyConfig
from nautilus_trader.model.data import Bar, BarType
from nautilus_trader.model.enums import OrderSide, OrderType, TimeInForce
from nautilus_trader.model.identifiers import InstrumentId
from nautilus_trader.model.objects import Price, Quantity
from nautilus_trader.trading.strategy import Strategy

try:
    from .action_log import action_row
    from .indicators import IndicatorBook
    from .logic import AccountState, Snapshot, decide
    from .params import Config, ConfigError, load_config
    from .reasons import (
        BACKTEST_SHUTDOWN,
        EXIT_STOP,
        EXIT_TIME,
        EXIT_TP,
        EXIT_UNCLASSIFIED,
        FILL,
        FILTER_FUNDING_WINDOW,
        FUNDING_CHARGE,
        FUNDING_UNKNOWN,
        ORDER_CANCEL_UNFILLED,
        ORDER_LIMIT_SUBMIT,
        ORDER_REJECTED,
    )
    from .risk import (
        ClosedTrade,
        exposure_hits_blackout,
        is_funding_settlement,
        quantize_nearest,
    )
except ImportError:
    from action_log import action_row
    from indicators import IndicatorBook
    from logic import AccountState, Snapshot, decide
    from params import Config, ConfigError, load_config
    from reasons import (
        BACKTEST_SHUTDOWN,
        EXIT_STOP,
        EXIT_TIME,
        EXIT_TP,
        EXIT_UNCLASSIFIED,
        FILL,
        FILTER_FUNDING_WINDOW,
        FUNDING_CHARGE,
        FUNDING_UNKNOWN,
        ORDER_CANCEL_UNFILLED,
        ORDER_LIMIT_SUBMIT,
        ORDER_REJECTED,
    )
    from risk import (
        ClosedTrade,
        exposure_hits_blackout,
        is_funding_settlement,
        quantize_nearest,
    )


class EmaAdxLongConfig(StrategyConfig):
    instrument_id: InstrumentId | None = None
    bar_type: BarType | None = None
    instrument_ids: tuple[InstrumentId, ...] = ()
    bar_types: tuple[BarType, ...] = ()
    order_id_tag: str = "EMAADX"


class EmaAdxLongStrategy(Strategy):
    def __init__(self, config: EmaAdxLongConfig) -> None:
        super().__init__(config)
        self.cfg_model = config
        self.playbook: Config | None = None
        self._config_error = ""
        self._books: dict[str, IndicatorBook] = {}
        self._instruments: dict[str, Any] = {}
        self._pending: dict[str, dict[str, Any]] = {}
        self._open: dict[str, dict[str, Any]] = {}
        self._closed: list[ClosedTrade] = []
        self._daily: dict[str, float] = {}
        self._cumulative = 0.0
        self._consecutive_losses = 0
        self._funding_blocked = False
        self._stopping = False
        self._skip_engine = False
        self._halt_logged: set[str] = set()
        self._funding_maps: dict[str, list[tuple[int, float]]] = {}
        self.feature_frames: dict[Any, Any] | None = None
        self._output = Path("/workspace/output")

    def set_feature_frames(self, feature_frames: dict[Any, Any]) -> None:
        self.feature_frames = feature_frames
        for key, frame in feature_frames.items():
            points = _funding_points(frame)
            if not points:
                continue
            self._funding_maps[str(key)] = points
            self._funding_maps[_symbol(key)] = points

    def on_start(self) -> None:
        self._output.mkdir(parents=True, exist_ok=True)
        marker = Path("/tmp/ema_adx_long_engine.lock")
        if marker.exists():
            self._skip_engine = True
            return
        try:
            marker.write_text("1", encoding="utf-8")
        except OSError:
            pass
        try:
            from getagent import runtime

            raw = (runtime.manifest.get("strategy_config") or {}) if runtime.manifest else {}
            self.playbook = load_config(raw)
        except ConfigError as exc:
            self._config_error = str(exc)
            return
        except Exception as exc:
            self._config_error = f"config unreadable: {type(exc).__name__}"
            return
        cfg = self.playbook
        assert cfg is not None
        bar_types = list(self.cfg_model.bar_types)
        if self.cfg_model.bar_type is not None:
            bar_types.append(self.cfg_model.bar_type)
        instrument_ids = list(self.cfg_model.instrument_ids)
        if self.cfg_model.instrument_id is not None:
            instrument_ids.append(self.cfg_model.instrument_id)
        if not instrument_ids:
            instrument_ids = [
                InstrumentId.from_str(f"{symbol}.BITGET") for symbol in cfg.trading_symbols
            ]
        if not bar_types:
            bar_types = [
                BarType.from_str(f"{symbol}.BITGET-1-HOUR-LAST-EXTERNAL")
                for symbol in cfg.trading_symbols
            ]
        if not bar_types:
            raise RuntimeError("bar_type or bar_types must be set")
        for bar_type in bar_types:
            self.subscribe_bars(bar_type)
        for instrument_id in instrument_ids:
            instrument = self.cache.instrument(instrument_id)
            if instrument is not None:
                self._instruments[_symbol(instrument_id)] = instrument
        self._ensure_funding(cfg)
        for symbol in cfg.trading_symbols:
            self._books[symbol] = IndicatorBook(
                ema_fast=cfg.ema_fast,
                ema_slow=cfg.ema_slow,
                adx_period=cfg.adx_period,
                atr_period=cfg.atr_period,
                atr_pct_lookback=cfg.atr_pct_lookback,
                volume_avg_bars=cfg.volume_avg_bars,
            )

    def on_bar(self, bar: Bar) -> None:
        if self._skip_engine or self.playbook is None:
            return
        symbol = _symbol(bar.bar_type.instrument_id)
        if symbol not in self.playbook.trading_symbols:
            return
        instrument = self._instruments.get(symbol) or self.cache.instrument(bar.bar_type.instrument_id)
        if instrument is None:
            return
        self._instruments[symbol] = instrument
        book = self._books.setdefault(
            symbol,
            IndicatorBook(
                ema_fast=self.playbook.ema_fast,
                ema_slow=self.playbook.ema_slow,
                adx_period=self.playbook.adx_period,
                atr_period=self.playbook.atr_period,
                atr_pct_lookback=self.playbook.atr_pct_lookback,
                volume_avg_bars=self.playbook.volume_avg_bars,
            ),
        )
        values = book.update(
            _num(bar.high),
            _num(bar.low),
            _num(bar.close),
            _num(bar.volume),
        )
        open_ts = datetime.fromtimestamp(bar.ts_event / 1_000_000_000, tz=timezone.utc)
        close_ts = open_ts + timedelta(hours=self.playbook.bar_hours)
        self._charge_funding(symbol, open_ts, instrument)
        self._manage_symbol(symbol, instrument, close_ts)
        self._maybe_enter(symbol, instrument, close_ts, values)

    def on_order_filled(self, event: Any) -> None:
        symbol = _symbol(event.instrument_id)
        side = str(getattr(event, "order_side", ""))
        price = _num(getattr(event, "last_px", None))
        qty = _num(getattr(event, "last_qty", None))
        fee = _money(getattr(event, "commission", None))
        fill_ts = datetime.fromtimestamp(event.ts_event / 1_000_000_000, tz=timezone.utc)
        is_buy = side.endswith("BUY") or side == "1"
        if symbol in self._pending and is_buy and symbol not in self._open:
            pending = self._pending.pop(symbol)
            same_bar = fill_ts <= pending["submit_ts"] + timedelta(hours=1)
            self._open[symbol] = {
                "fill_ts": fill_ts,
                "qty": qty,
                "entry_notional": price * qty,
                "entry_fee": fee or 0.0,
                "entry_fee_rate": self.playbook.taker_fee if same_bar and self.playbook else 0.0,
                "exit_notional": 0.0,
                "exit_qty": 0.0,
                "exit_fee": 0.0,
                "stop": pending["stop"],
                "take_profit": pending["take_profit"],
                "risk_usdt": pending["risk_usdt"],
                "tick": pending["tick"],
                "funding_usdt": 0.0,
                "funding_known": True,
                "submit_ts": pending["submit_ts"],
            }
            if self.playbook and not same_bar:
                self._open[symbol]["entry_fee_rate"] = self.playbook.maker_fee
            self._append(
                action_row(
                    timestamp=fill_ts,
                    symbol=symbol,
                    side="long",
                    reason_code=FILL,
                    intended_price=pending["entry"],
                    filled_price=price,
                    fees=fee,
                    funding=0.0,
                )
            )
            return
        position = self._open.get(symbol)
        if position is not None and not is_buy:
            position["exit_notional"] += price * qty
            position["exit_qty"] += qty
            position["exit_fee"] += fee or 0.0

    def on_position_closed(self, event: Any) -> None:
        symbol = _symbol(event.instrument_id)
        position = self._open.pop(symbol, None)
        if position is None or self.playbook is None:
            return
        exit_qty = position["exit_qty"] or position["qty"]
        if exit_qty <= 0:
            return
        entry_price = position["entry_notional"] / position["qty"] if position["qty"] else 0.0
        exit_price = (
            position["exit_notional"] / position["exit_qty"]
            if position["exit_qty"]
            else _num(getattr(event, "avg_px_close", None) or getattr(event, "last_px", None))
        )
        if self._stopping:
            reason = BACKTEST_SHUTDOWN
            exit_fee_rate = self.playbook.taker_fee
        else:
            reason = self._classify_exit(position, exit_price)
            exit_fee_rate = self.playbook.maker_fee if reason == EXIT_TP else self.playbook.taker_fee
        tick = position["tick"]
        slippage = self.playbook.slippage_ticks * tick * exit_qty * 2
        trade = ClosedTrade(
            symbol=symbol,
            entry_ts=position["fill_ts"].isoformat(),
            exit_ts=datetime.fromtimestamp(event.ts_event / 1_000_000_000, tz=timezone.utc).isoformat(),
            side="long",
            qty=float(exit_qty),
            entry_price=float(entry_price),
            exit_price=float(exit_price),
            entry_fee_rate=float(position["entry_fee_rate"]),
            exit_fee_rate=float(exit_fee_rate),
            slippage_usdt=float(slippage),
            funding_usdt=float(position["funding_usdt"]),
            funding_known=bool(position["funding_known"]),
            risk_usdt=float(position["risk_usdt"]),
            reason_code=reason,
        )
        self._closed.append(trade)
        net = trade.net(1.0)
        if reason != BACKTEST_SHUTDOWN:
            if net is None:
                self._funding_blocked = True
            else:
                day = trade.exit_ts[:10]
                self._daily[day] = self._daily.get(day, 0.0) + net
                self._cumulative += net
                if net < 0:
                    self._consecutive_losses += 1
                elif net > 0:
                    self._consecutive_losses = 0
        self._append(
            action_row(
                timestamp=datetime.fromisoformat(trade.exit_ts),
                symbol=symbol,
                side="long",
                reason_code=reason,
                intended_price=position["take_profit"] if reason == EXIT_TP else position["stop"],
                filled_price=float(exit_price),
                fees=trade.fee_usdt(),
                funding=trade.funding_usdt if trade.funding_known else None,
            )
        )

    def on_stop(self) -> None:
        self._stopping = True
        if self._skip_engine:
            return
        instrument_ids = list(self.cfg_model.instrument_ids)
        if self.cfg_model.instrument_id is not None:
            instrument_ids.append(self.cfg_model.instrument_id)
        if not instrument_ids:
            instrument_ids = [
                instrument.id for instrument in self._instruments.values() if getattr(instrument, "id", None)
            ]
        for instrument_id in instrument_ids:
            self.cancel_all_orders(instrument_id)
            self.close_all_positions(instrument_id)
        self._write_closed_trades()

    def _maybe_enter(
        self,
        symbol: str,
        instrument: Any,
        close_ts: datetime,
        values: dict[str, float | None],
    ) -> None:
        cfg = self.playbook
        if cfg is None:
            return
        if self._funding_blocked:
            self._log_halt(symbol, close_ts, FUNDING_UNKNOWN)
            return
        upcoming = exposure_hits_blackout(
            close_ts,
            close_ts + timedelta(hours=cfg.bar_hours),
            cfg.funding_blackout_minutes,
        )
        if upcoming and symbol in self._pending:
            self.cancel_all_orders(instrument.id)
            self._pending.pop(symbol, None)
            self._append(
                action_row(
                    timestamp=close_ts,
                    symbol=symbol,
                    side="none",
                    reason_code=FILTER_FUNDING_WINDOW,
                    detail="cancelled resting entry before funding blackout",
                )
            )
        snapshot = Snapshot(
            symbol=symbol,
            close_ts=close_ts,
            close=values.get("close"),
            atr=values.get("atr"),
            atr_pct=values.get("atr_pct"),
            adx=values.get("adx"),
            plus_di=values.get("plus_di"),
            minus_di=values.get("minus_di"),
            fast_ema=values.get("fast_ema"),
            slow_ema=values.get("slow_ema"),
            prev_fast_ema=values.get("prev_fast_ema"),
            prev_slow_ema=values.get("prev_slow_ema"),
            volume=values.get("volume"),
            volume_avg_prev=values.get("volume_avg_prev"),
            funding_rate=self._funding_at(instrument.id, close_ts - timedelta(hours=cfg.bar_hours)),
            price_tick=_num(instrument.price_increment),
            size_step=_num(instrument.size_increment),
            min_qty=_num(getattr(instrument, "lot_size", None) or instrument.size_increment),
        )
        account = AccountState(
            open_positions=len(self._open) + len(self._pending),
            symbol_busy=symbol in self._open or symbol in self._pending,
            daily_realised=self._daily.get(close_ts.date().isoformat(), 0.0),
            cumulative_realised=self._cumulative,
            consecutive_losses=self._consecutive_losses,
            margin_remaining=self._margin_remaining(),
            ticker_age_seconds=None,
            apply_ticker_staleness=False,
        )
        decision = decide(snapshot, cfg, account)
        if decision.reason_code in {"FILTER_NO_CROSS", "INSUFFICIENT_HISTORY"}:
            return
        if decision.action != "long":
            self._append(
                action_row(
                    timestamp=close_ts,
                    symbol=symbol,
                    side="none",
                    reason_code=decision.reason_code,
                )
            )
            return
        if upcoming:
            self._append(
                action_row(
                    timestamp=close_ts,
                    symbol=symbol,
                    side="none",
                    reason_code=FILTER_FUNDING_WINDOW,
                    detail="next bar overlaps a funding blackout",
                )
            )
            return
        self._submit_bracket(symbol, instrument, close_ts, decision)

    def _submit_bracket(
        self,
        symbol: str,
        instrument: Any,
        close_ts: datetime,
        decision: Any,
    ) -> None:
        cfg = self.playbook
        if cfg is None or decision.qty is None or decision.entry is None:
            return
        try:
            entry = Price.from_str(_price_text(decision.entry, instrument))
            stop = Price.from_str(_price_text(decision.stop, instrument))
            target = Price.from_str(_price_text(decision.take_profit, instrument))
            qty = Quantity(Decimal(str(decision.qty)), instrument.size_precision)
            order_list = self.order_factory.bracket(
                instrument_id=instrument.id,
                order_side=OrderSide.BUY,
                quantity=qty,
                time_in_force=TimeInForce.GTC,
                entry_price=entry,
                sl_trigger_price=stop,
                tp_price=target,
                entry_order_type=OrderType.LIMIT,
            )
            self.submit_order_list(order_list)
        except Exception as exc:
            self._append(
                action_row(
                    timestamp=close_ts,
                    symbol=symbol,
                    side="none",
                    reason_code=ORDER_REJECTED,
                    intended_price=decision.entry,
                    detail=type(exc).__name__,
                )
            )
            return
        self._pending[symbol] = {
            "submit_ts": close_ts,
            "expire_ts": close_ts + timedelta(hours=cfg.limit_timeout_hours),
            "entry": decision.entry,
            "stop": decision.stop,
            "take_profit": decision.take_profit,
            "risk_usdt": decision.risk_usdt,
            "margin": decision.margin or 0.0,
            "tick": _num(instrument.price_increment),
        }
        self._append(
            action_row(
                timestamp=close_ts,
                symbol=symbol,
                side="long",
                reason_code=ORDER_LIMIT_SUBMIT,
                intended_price=decision.entry,
            )
        )

    def _manage_symbol(self, symbol: str, instrument: Any, close_ts: datetime) -> None:
        cfg = self.playbook
        if cfg is None:
            return
        pending = self._pending.get(symbol)
        if pending is not None and symbol not in self._open:
            if close_ts >= pending["expire_ts"]:
                self.cancel_all_orders(instrument.id)
                self._pending.pop(symbol, None)
                self._append(
                    action_row(
                        timestamp=close_ts,
                        symbol=symbol,
                        side="none",
                        reason_code=ORDER_CANCEL_UNFILLED,
                        intended_price=pending["entry"],
                    )
                )
        position = self._open.get(symbol)
        if position is not None:
            deadline = position["fill_ts"] + timedelta(hours=cfg.time_stop_hours)
            if close_ts >= deadline:
                position["exit_intent"] = EXIT_TIME
                self.cancel_all_orders(instrument.id)
                self.close_all_positions(instrument.id)

    def _charge_funding(self, symbol: str, open_ts: datetime, instrument: Any) -> None:
        position = self._open.get(symbol)
        cfg = self.playbook
        if position is None or cfg is None or not is_funding_settlement(open_ts):
            return
        if position["fill_ts"] > open_ts:
            return
        rate = self._funding_at(instrument.id, open_ts)
        if rate is None:
            position["funding_known"] = False
            self._funding_blocked = True
            self._append(
                action_row(
                    timestamp=open_ts,
                    symbol=symbol,
                    side="long",
                    reason_code=FUNDING_UNKNOWN,
                )
            )
            return
        entry = position["entry_notional"] / position["qty"]
        charge = position["qty"] * entry * rate
        position["funding_usdt"] += charge
        self._append(
            action_row(
                timestamp=open_ts,
                symbol=symbol,
                side="long",
                reason_code=FUNDING_CHARGE,
                funding=charge,
            )
        )

    def _ensure_funding(self, cfg: Config) -> None:
        """Use injected frames. If they have no funding points, fetch the series."""
        if any(self._funding_maps.values()):
            return
        start_ms = _iso_ms(cfg.backtest_start)
        end_ms = _iso_ms(cfg.backtest_end)
        try:
            from .features import DataCoverageError, fetch_funding
        except ImportError:
            from features import DataCoverageError, fetch_funding
        for symbol in cfg.trading_symbols:
            try:
                rows, _argument = fetch_funding(symbol, start_ms, end_ms)
            except (DataCoverageError, Exception):
                self._funding_blocked = True
                continue
            points = _funding_points_from_rows(rows)
            if not points:
                self._funding_blocked = True
                continue
            self._funding_maps[symbol] = points
            self._funding_maps[f"{symbol}.BITGET"] = points

    def _funding_at(self, instrument_id: Any, moment: datetime) -> float | None:
        points = self._funding_maps.get(str(instrument_id))
        if not points and self.feature_frames:
            for key, frame in self.feature_frames.items():
                if _symbol(key) == _symbol(instrument_id) or str(key) == str(instrument_id):
                    points = _funding_points(frame)
                    self._funding_maps[str(instrument_id)] = points
                    break
        if not points:
            return None
        target = int(moment.timestamp() * 1000)
        chosen: float | None = None
        for stamp, rate in points:
            if stamp <= target:
                chosen = rate
            else:
                break
        return chosen

    def _margin_remaining(self) -> float:
        cfg = self.playbook
        if cfg is None:
            return 0.0
        used = 0.0
        for pending in self._pending.values():
            used += float(pending.get("margin") or 0.0)
        for position in self._open.values():
            entry = position["entry_notional"] / position["qty"] if position["qty"] else 0.0
            used += (entry * position["qty"]) / cfg.applied_leverage
        return cfg.margin_budget - used

    def _classify_exit(self, position: dict[str, Any], exit_price: float) -> str:
        if position.get("exit_intent") == EXIT_TIME:
            return EXIT_TIME
        tick = float(position["tick"])
        if exit_price <= float(position["stop"]) + tick:
            return EXIT_STOP
        if exit_price >= float(position["take_profit"]) - tick:
            return EXIT_TP
        return EXIT_UNCLASSIFIED

    def _log_halt(self, symbol: str, moment: datetime, reason: str) -> None:
        if reason in self._halt_logged:
            return
        self._halt_logged.add(reason)
        self._append(
            action_row(
                timestamp=moment,
                symbol=symbol,
                side="none",
                reason_code=reason,
            )
        )

    def _append(self, row: dict[str, Any]) -> None:
        self._output.mkdir(parents=True, exist_ok=True)
        path = self._output / "action_log.jsonl"
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(row, ensure_ascii=True) + "\n")

    def _write_closed_trades(self) -> None:
        path = self._output / "closed_trades.json"
        payload = [
            {
                "symbol": trade.symbol,
                "entry_ts": trade.entry_ts,
                "exit_ts": trade.exit_ts,
                "side": trade.side,
                "qty": trade.qty,
                "entry_price": trade.entry_price,
                "exit_price": trade.exit_price,
                "entry_fee_rate": trade.entry_fee_rate,
                "exit_fee_rate": trade.exit_fee_rate,
                "slippage_usdt": trade.slippage_usdt,
                "funding_usdt": trade.funding_usdt,
                "funding_known": trade.funding_known,
                "risk_usdt": trade.risk_usdt,
                "reason_code": trade.reason_code,
            }
            for trade in self._closed
        ]
        path.write_text(json.dumps(payload), encoding="utf-8")


def _symbol(value: Any) -> str:
    text = str(value)
    return text.split(".", 1)[0]


def _num(value: Any) -> float:
    if value is None:
        return 0.0
    if hasattr(value, "as_double"):
        return float(value.as_double())
    return float(value)


def _money(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return abs(_num(value))
    except (TypeError, ValueError):
        return None


def _price_text(value: float, instrument: Any) -> str:
    tick = _num(instrument.price_increment)
    quantized = quantize_nearest(value, tick)
    return format(quantized, "f")


def _iso_ms(value: str) -> int:
    text = value.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(text)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return int(parsed.timestamp() * 1000)


def _funding_points_from_rows(rows: list[dict[str, Any]]) -> list[tuple[int, float]]:
    points: list[tuple[int, float]] = []
    for row in rows:
        raw_time = row.get("time") or row.get("timestamp") or row.get("date") or row.get("funding_ts")
        try:
            stamp = int(float(raw_time))
        except (TypeError, ValueError):
            continue
        if stamp < 10_000_000_000:
            stamp *= 1000
        try:
            rate = float(row.get("funding_rate"))
        except (TypeError, ValueError):
            continue
        if rate == rate and rate not in (float("inf"), float("-inf")):
            points.append((stamp, rate))
    points.sort(key=lambda item: item[0])
    return points


def _funding_points(frame: Any) -> list[tuple[int, float]]:
    if frame is None or not hasattr(frame, "columns") or "funding_rate" not in frame.columns:
        return []
    points: list[tuple[int, float]] = []
    for ts, row in frame.iterrows():
        try:
            stamp = int(pd.Timestamp(ts).timestamp() * 1000)
            rate = float(row["funding_rate"])
        except (TypeError, ValueError, OverflowError):
            continue
        if rate == rate and rate not in (float("inf"), float("-inf")):
            points.append((stamp, rate))
    points.sort(key=lambda item: item[0])
    return points
