#!/usr/bin/env python3
"""Playbook package Local validation script。

Usage:
    python3 scripts/validate.py ./my-strategy/

Requires Python 3.11+. PyYAML is recommended (`pip install pyyaml`);
without it the script falls back to a weaker built-in parser.

Checks:
    1. Directory structure complete（manifest.yaml, src/main.py）
    2. manifest.yaml Required fields and public contract
    3. optional backtest.yaml shape
    4. all Python files under src/ compile and pass the import allowlist
    5. Nautilus lifecycle calls match the runner's installed API
    6. local-only directories are not included in the upload package
"""

from __future__ import annotations

import ast
import re
import sys
from pathlib import Path, PurePosixPath
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

try:
    from telemetry import report_validation
except ImportError:
    def report_validation(*, passed: bool, errors: int, warnings: int) -> None:
        return

try:
    import yaml
except ImportError:
    print("WARNING: PyYAML not installed, falling back to basic parsing")
    yaml = None  # type: ignore[assignment]


REQUIRED_FILES = [
    "README.md",
    "manifest.yaml",
    "src/main.py",
]

MANIFEST_REQUIRED_FIELDS = [
    "name",
    "display_name",
    "version",
    "description",
    "long_description",
    "market_type",
    "trading_symbols",
    "decision_mode",
    "backtest_support",
    "runtime_profile",
    "follow_trade_supported",
]

NAME_PATTERN = re.compile(r"^[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?$")
BACKTEST_BAR_FIELD_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")
PUBLIC_SYMBOL_TOKEN_PATTERN = re.compile(r"\b[A-Z0-9]{2,20}(?:USDT|USDC|USD|BTC|ETH)\b")
CRON_EVERY_MINUTES_PATTERN = re.compile(r"^\*/(\d+)$")
CJK_TEXT_PATTERN = re.compile(
    r"[\u3000-\u303f"
    r"\u3040-\u309f"
    r"\u30a0-\u30ff"
    r"\u3400-\u4dbf"
    r"\u4e00-\u9fff"
    r"\uf900-\ufaff"
    r"\uff00-\uffef]"
)
MIN_SCHEDULE_INTERVAL_MINUTES = 15
DEFAULT_SCHEDULE_TZ = "Asia/Shanghai"
DECISION_MODES = {"deterministic", "llm_assisted", "agentic"}
BACKTEST_SUPPORT_VALUES = {"full", "none"}
RUNTIME_PROFILES = {"deterministic", "llm_bounded", "agentic"}
EXECUTION_MODES = {"follow_trade", "grid"}
OUTPUT_KINDS = {"trade_strategy", "selection_basket", "grid"}
GRID_PRODUCT_USER_CONFIG_REQUIREMENTS = {
    "trade_type": {"type": "string", "options": {"spot", "contract"}},
    "style": {"type": "string", "options": {"balanced", "aggressive"}},
    "leverage": {"type": "integer", "min": 1, "max": 100},
    "capital_pct": {"type": "number", "min": 1, "max": 100},
    "max_bots": {"type": "integer", "min": 1, "max": 8},
    "trading_symbols": {"type": "array", "item_type": "string"},
    "auto_follow_new_coins": {"type": "boolean"},
}
REQUIRED_I18N_LOCALES = ("en", "zh", "zh-tw", "es", "ja", "vi")
LOCAL_ONLY_TOP_LEVEL = {
    "tests",
    "notebooks",
    "research",
    "data",
    "backtest_results",
    "logs",
    "output",
    ".venv",
    "__pycache__",
    ".pytest_cache",
}

ALLOWED_IMPORTS = {
    "getagent", "getclaw", "nautilus_trader", "pandas", "numpy", "json", "math",
    "datetime", "pathlib", "asyncio", "typing",
    "dataclasses", "collections", "functools",
    "re", "decimal", "statistics", "itertools",
    "operator", "copy", "enum", "abc", "numbers",
    "fractions",
}

BACKTEST_INSTRUMENT_KINDS = {"spot", "currency_pair", "perpetual", "perpetual_contract", "perp"}
NAUTILUS_INSTRUMENT_REQUIRED_METHODS = {"cancel_all_orders", "close_all_positions"}
README_REQUIRED_PHRASES = ("策略", "开仓", "平仓", "风险")

LONG_DESCRIPTION_MIN_WORDS = 250
LONG_DESCRIPTION_MAX_WORDS = 500
LONG_DESCRIPTION_TARGET_RANGE = (300, 400)

LONG_DESCRIPTION_SECTION_KEYWORDS: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "what it captures (§1 thesis)",
        (
            "capture", "captures", "tries to", "thesis", "aim", "aims",
            "objective", "designed", "seeks", "intended", "goal", "approach",
            "built on", "assumption", "purpose",
        ),
    ),
    (
        "entry logic (§2 entry)",
        (
            "enter", "enters", "entry", "entering", "opens", "go long",
            "go short", "going long", "going short", "long position",
            "short position",
        ),
    ),
    (
        "exit / stop logic (§3 exit)",
        (
            "exit", "exits", "close", "closes", "closing", "stop",
            "take profit", "take-profit", "stop-loss", "stop loss",
        ),
    ),
    (
        "tunable parameters (§4 tunables)",
        (
            "parameter", "parameters", "tunable", "leverage", "margin",
            "configurable", "adjust", "adjusts", "tune", "subscriber",
            "subscribers",
        ),
    ),
    (
        "risks / unsuitable conditions (§5 risks)",
        (
            "risk", "risks", "drawdown", "drawdowns", "lose money",
            "loses money", "lost money", "loss", "losses", "underperform",
            "underperforms", "unsuitable", "fails", "weakness", "worst",
            "warning",
        ),
    ),
)

LONG_DESCRIPTION_FORBIDDEN_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (
        re.compile(
            r"\b(?:EMA|SMA|WMA|MA|RSI|MACD|ATR|VWAP|ADX|Stoch(?:astic)?|Bollinger|MFI|CCI|OBV|DMI|TRIX|KDJ)"
            r"[\s_/-]*\d+",
            re.IGNORECASE,
        ),
        "indicator with a numeric period (e.g. 'EMA 12', 'RSI 14') leaks strategy parameters; "
        "describe the indicator category instead",
    ),
    (
        re.compile(
            r"\b\d+(?:\.\d+)?[\s/-]*"
            r"(?:bar|bars|candle|candles|period|periods|day|days|hour|hours|"
            r"minute|minutes|week|weeks|second|seconds|tick|ticks)\b",
            re.IGNORECASE,
        ),
        "numeric lookback window (e.g. '14 bars', '20 days', '5-minute') leaks strategy parameters; "
        "describe the timeframe qualitatively",
    ),
    (
        re.compile(r"(?<![\w.])(?:>=|<=|>|<|==)\s*-?\d"),
        "explicit numeric threshold (e.g. '> 30', '<= 0.7') leaks decision boundaries; "
        "describe direction without numbers",
    ),
    (
        re.compile(r"\b\d+(?:\.\d+)?\s*%"),
        "explicit percentage threshold (e.g. '3%', '10%') leaks decision boundaries; "
        "describe direction without numbers",
    ),
    (
        re.compile(r"\b\d+(?:\.\d+)?\s*x\b", re.IGNORECASE),
        "explicit multiplier (e.g. '1.5x', '10x') leaks parameter; describe behavior qualitatively",
    ),
    (
        re.compile(r"\b\d+\s*:\s*\d+\b"),
        "explicit ratio (e.g. '3:1', '2:1') leaks decision boundary; describe behavior qualitatively",
    ),
)
POSITION_SELECTION_HELPERS = {"select_contract_position", "find_contract_position"}
POSITION_SELECTION_INVALID_ATTRS = {
    "open_price",
    "openPrice",
    "entry_price",
    "entryPrice",
    "avg_price",
    "avgPrice",
    "average_open_price",
    "averageOpenPrice",
}
CONTRACT_ORDER_HELPERS = {
    "open_long_market",
    "open_short_market",
}
CONTRACT_TPSL_HELPER = "resolve_contract_tpsl"
CONTRACT_TPSL_HELPER_KEYWORDS = {
    "symbol",
    "side",
    "leverage",
    "tp_trigger_price",
    "sl_trigger_price",
    "reference_price",
    "product_type",
}
TRADE_MUTATION_METHODS = {
    "add_investment",
    "cancel_order",
    "change_leverage",
    "close_bot",
    "close_position",
    "create_bot",
    "limit_order",
    "market_buy",
    "market_sell",
    "modify_bot",
    "modify_grid_interval",
    "modify_limit_order",
    "modify_stop_loss",
    "modify_take_profit",
    "open_long_limit",
    "open_long_market",
    "open_short_limit",
    "open_short_market",
    "place_order",
    "transfer",
}
CONTRACT_TRIGGER_PRICE_KEYWORDS = {"tp_trigger_price", "sl_trigger_price"}

# runtime.emit_progress / runtime.emit_decision protocol (grid playbooks).
# 2026-07-20 contract revision: block types converged to
# title / subTitle / content; ctx is a plain markdown string (the legacy
# text/table span protocol was removed).
PROGRESS_BLOCK_TYPES = {"title", "subTitle", "content"}
LEGACY_PROGRESS_BLOCK_TYPES = {"text", "table"}
MAX_PROGRESS_BLOCKS_PER_CALL = 8
DECISION_ACTIONS = {"create", "modify", "shutdown", "watch"}
DECISION_WATCH_SUB_ACTIONS = {"watch.ok", "watch.warn", "watch.action"}
GRID_MUTATION_METHODS = {
    "add_investment",
    "close_bot",
    "create_bot",
    "modify_bot",
    "modify_grid_interval",
}
GRID_ACTION_MUTATION_METHODS = {
    "create": {"create_bot"},
    "modify": {"add_investment", "modify_bot", "modify_grid_interval"},
    "shutdown": {"close_bot"},
}

BLOCKED_IMPORTS = {
    "requests", "httpx", "trade_sdk", "ccxt", "subprocess",
    "os", "sys", "importlib", "socket", "urllib",
    "http", "ftplib", "smtplib", "shutil",
    "sqlalchemy", "redis", "pymongo", "fastapi", "flask",
    "telegram", "slack_sdk", "discord", "multiprocessing",
}


class ValidationResult:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def error(self, msg: str) -> None:
        self.errors.append(msg)

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)

    @property
    def passed(self) -> bool:
        return len(self.errors) == 0


def _validate_exchange_native_symbol(
    symbol: object,
    *,
    prefix: str,
    result: ValidationResult,
) -> None:
    value = str(symbol or "").strip()
    if not value:
        return
    if "/" in value or ":" in value or any(char.isspace() for char in value):
        result.error(
            f"{prefix}: symbols must use exchange-native tradable pair format "
            "(for example BTCUSDT, RAAPLUSDT, AAPLUSDT), not CCXT unified or spaced symbols"
        )


def _normalized_symbol_list(value: object) -> list[str]:
    if isinstance(value, str):
        value = [value]
    if not isinstance(value, list):
        return []
    symbols: list[str] = []
    for item in value:
        symbol = str(item or "").strip().upper()
        if symbol and symbol not in symbols:
            symbols.append(symbol)
    return symbols


def _normalized_backtest_symbols(manifest: dict[str, object]) -> list[str]:
    strategy_config = manifest.get("strategy_config")
    if not isinstance(strategy_config, dict):
        strategy_config = {}
    return _normalized_symbol_list(
        strategy_config.get("trading_symbols", manifest.get("trading_symbols", []))
    )


def _load_yaml(path: Path) -> dict | None:
    if yaml is None:
        return {}
    try:
        with open(path) as f:
            return yaml.safe_load(f) or {}
    except Exception:
        return None


def _validate_grid_strategy_config(
    strategy_config: object,
    user_config_schema: object,
    result: ValidationResult,
) -> None:
    if not isinstance(strategy_config, dict):
        result.error(
            "manifest.yaml: output_kind 'grid' requires strategy_config "
            "with the standard Grid product fields"
        )
        return

    def error(field: str, message: str) -> None:
        result.error(f"manifest.yaml: strategy_config.{field} {message}")

    for field in GRID_PRODUCT_USER_CONFIG_REQUIREMENTS:
        if field not in strategy_config:
            error(field, "is required by the Grid product contract")

    trade_type = strategy_config.get("trade_type")
    if not isinstance(trade_type, str) or trade_type not in {"spot", "contract"}:
        error("trade_type", "must be 'spot' or 'contract'")

    style = strategy_config.get("style")
    if not isinstance(style, str) or style not in {"balanced", "aggressive"}:
        error("style", "must be 'balanced' or 'aggressive'")

    for field, minimum, maximum in (
        ("leverage", 1, 100),
        ("max_bots", 1, 8),
    ):
        value = strategy_config.get(field)
        if not isinstance(value, int) or isinstance(value, bool):
            error(field, f"must be an integer in range {minimum}..{maximum}")
        elif not minimum <= value <= maximum:
            error(field, f"must be in range {minimum}..{maximum}")

    capital_pct = strategy_config.get("capital_pct")
    if (
        not isinstance(capital_pct, (int, float))
        or isinstance(capital_pct, bool)
        or not 1 <= capital_pct <= 100
    ):
        error("capital_pct", "must be a number in range 1..100")

    trading_symbols = strategy_config.get("trading_symbols")
    if not isinstance(trading_symbols, list) or not all(
        isinstance(item, str) and item.strip() for item in trading_symbols
    ):
        error("trading_symbols", "must be an array of non-empty strings")

    if not isinstance(strategy_config.get("auto_follow_new_coins"), bool):
        error("auto_follow_new_coins", "must be a boolean")

    if isinstance(user_config_schema, dict):
        for field in GRID_PRODUCT_USER_CONFIG_REQUIREMENTS:
            spec = user_config_schema.get(field)
            if not isinstance(spec, dict) or "default" not in spec or field not in strategy_config:
                continue
            if spec["default"] != strategy_config[field]:
                result.error(
                    f"manifest.yaml: user_config_schema.{field}.default must equal "
                    f"strategy_config.{field} ({strategy_config[field]!r})"
                )


def validate_structure(pkg_dir: Path, result: ValidationResult) -> None:
    for rel in REQUIRED_FILES:
        if not (pkg_dir / rel).exists():
            result.error(f"Missing required file: {rel}")

    for child in pkg_dir.iterdir():
        if child.name in LOCAL_ONLY_TOP_LEVEL:
            result.error(f"Local-only path must not be included in upload package: {child.name}")

    readme_path = pkg_dir / "README.md"
    if readme_path.exists():
        text = readme_path.read_text(encoding="utf-8", errors="ignore").strip()
        if len(text) < 200:
            result.error("README.md: must be a human-readable strategy explanation of at least 200 characters")
        normalized_text = text.lower()
        missing = [phrase for phrase in README_REQUIRED_PHRASES if phrase not in normalized_text]
        if missing:
            result.error(f"README.md: missing required plain-language sections or keywords: {', '.join(missing)}")


def _validate_long_description(
    raw_value: object,
    description: str,
    result: ValidationResult,
) -> None:
    """Hard-fail manifest.long_description authoring rules.

    Rules:
      - present, string, non-empty
      - 250..500 words (target 300..400)
      - covers all 5 required sections by keyword cluster
      - does not leak indicator periods, lookback windows, numeric thresholds,
        percentages, multipliers, or ratios
      - is not a near-duplicate of `description`
    """

    if raw_value is None:
        return

    if not isinstance(raw_value, str):
        result.error("manifest.yaml: 'long_description' must be a string")
        return

    text = raw_value.strip()
    if not text:
        result.error("manifest.yaml: 'long_description' must not be empty")
        return

    word_count = len(text.split())
    if word_count < LONG_DESCRIPTION_MIN_WORDS:
        result.error(
            f"manifest.yaml: 'long_description' is {word_count} words; "
            f"must be at least {LONG_DESCRIPTION_MIN_WORDS} (target "
            f"{LONG_DESCRIPTION_TARGET_RANGE[0]}-{LONG_DESCRIPTION_TARGET_RANGE[1]})"
        )
    elif word_count > LONG_DESCRIPTION_MAX_WORDS:
        result.error(
            f"manifest.yaml: 'long_description' is {word_count} words; "
            f"must be at most {LONG_DESCRIPTION_MAX_WORDS} (target "
            f"{LONG_DESCRIPTION_TARGET_RANGE[0]}-{LONG_DESCRIPTION_TARGET_RANGE[1]})"
        )
    elif not (
        LONG_DESCRIPTION_TARGET_RANGE[0] <= word_count <= LONG_DESCRIPTION_TARGET_RANGE[1]
    ):
        result.warn(
            f"manifest.yaml: 'long_description' is {word_count} words; "
            f"target range is {LONG_DESCRIPTION_TARGET_RANGE[0]}-{LONG_DESCRIPTION_TARGET_RANGE[1]}"
        )

    for label, keywords in LONG_DESCRIPTION_SECTION_KEYWORDS:
        keyword_re = re.compile(
            r"\b(?:" + "|".join(re.escape(k) for k in keywords) + r")\b",
            re.IGNORECASE,
        )
        if not keyword_re.search(text):
            result.error(
                f"manifest.yaml: 'long_description' is missing required section coverage: {label}. "
                f"At least one of these must appear: {', '.join(keywords)}"
            )

    for pattern, reason in LONG_DESCRIPTION_FORBIDDEN_PATTERNS:
        match = pattern.search(text)
        if match:
            snippet = match.group(0)
            result.error(
                f"manifest.yaml: 'long_description' contains forbidden content {snippet!r}: {reason}"
            )

    if description and isinstance(description, str):
        d_norm = " ".join(description.lower().split())
        l_norm = " ".join(text.lower().split())
        if d_norm and (d_norm in l_norm) and len(d_norm) > 30 and len(l_norm) < 2 * len(d_norm):
            result.error(
                "manifest.yaml: 'long_description' appears to be a near-duplicate of 'description'; "
                "rewrite it as a 300-400 word strategy summary covering thesis, entry, exit, "
                "tunables, and risks"
            )


def validate_manifest(pkg_dir: Path, result: ValidationResult) -> dict:
    path = pkg_dir / "manifest.yaml"
    if not path.exists():
        return {}

    data = _load_yaml(path)
    if data is None:
        result.error("manifest.yaml: invalid YAML syntax")
        return {}

    for field in MANIFEST_REQUIRED_FIELDS:
        if field not in data:
            result.error(f"manifest.yaml: missing required field '{field}'")

    output_kind = data.get("output_kind", "") or "trade_strategy"
    if output_kind != "selection_basket" and "execution_mode" not in data:
        result.error("manifest.yaml: missing required field 'execution_mode'")

    name = data.get("name", "")
    if name and not NAME_PATTERN.match(name):
        result.error(
            f"manifest.yaml: 'name' must be lowercase alphanumeric with hyphens "
            f"(DNS label format), got: '{name}'"
        )

    market_type = data.get("market_type", "")
    if market_type and market_type not in ("spot", "contract"):
        result.error(f"manifest.yaml: 'market_type' must be 'spot' or 'contract', got: '{market_type}'")

    symbols = data.get("trading_symbols", [])
    if not isinstance(symbols, list) or not all(isinstance(item, str) and item.strip() for item in symbols):
        result.error("manifest.yaml: 'trading_symbols' must be a list of non-empty strings")
    else:
        normalized_symbols = {str(item).strip().upper() for item in symbols}
        for index, symbol in enumerate(symbols):
            _validate_exchange_native_symbol(
                symbol,
                prefix=f"manifest.yaml: trading_symbols[{index}]",
                result=result,
            )
        if normalized_symbols:
            for field in ("display_name", "description"):
                text = str(data.get(field, "") or "")
                unknown_symbols = sorted(
                    token
                    for token in PUBLIC_SYMBOL_TOKEN_PATTERN.findall(text.upper())
                    if token not in normalized_symbols
                )
                if unknown_symbols:
                    result.error(
                        f"manifest.yaml: '{field}' mentions symbols {unknown_symbols} "
                        f"outside trading_symbols {sorted(normalized_symbols)}; "
                        "if you corrected a typo or changed the fallback symbol, update all display text"
                    )

    strategy_config = data.get("strategy_config")
    if isinstance(strategy_config, dict):
        config_symbols = strategy_config.get("trading_symbols")
        if isinstance(config_symbols, list):
            manifest_symbol_list = _normalized_symbol_list(symbols)
            config_symbol_list = _normalized_symbol_list(config_symbols)
            if manifest_symbol_list and config_symbol_list and config_symbol_list != manifest_symbol_list:
                result.error(
                    "manifest.yaml: strategy_config.trading_symbols must match "
                    "top-level trading_symbols exactly"
                )
            for index, symbol in enumerate(config_symbols):
                _validate_exchange_native_symbol(
                    symbol,
                    prefix=f"manifest.yaml: strategy_config.trading_symbols[{index}]",
                    result=result,
                )

    user_config_schema = data.get("user_config_schema")
    if isinstance(user_config_schema, dict):
        trading_symbol_schema = user_config_schema.get("trading_symbols")
        if isinstance(trading_symbol_schema, dict):
            default_symbols = trading_symbol_schema.get("default")
            if isinstance(default_symbols, list):
                for index, symbol in enumerate(default_symbols):
                    _validate_exchange_native_symbol(
                        symbol,
                        prefix=(
                            "manifest.yaml: user_config_schema.trading_symbols."
                            f"default[{index}]"
                        ),
                        result=result,
                    )
            option_symbols = trading_symbol_schema.get("options")
            if isinstance(option_symbols, list):
                for index, symbol in enumerate(option_symbols):
                    _validate_exchange_native_symbol(
                        symbol,
                        prefix=(
                            "manifest.yaml: user_config_schema.trading_symbols."
                            f"options[{index}]"
                        ),
                        result=result,
                    )

    decision_mode = data.get("decision_mode", "")
    if decision_mode and decision_mode not in DECISION_MODES:
        result.error(f"manifest.yaml: 'decision_mode' must be one of {sorted(DECISION_MODES)}")

    backtest_support = data.get("backtest_support", "")
    if backtest_support and backtest_support not in BACKTEST_SUPPORT_VALUES:
        result.error(
            f"manifest.yaml: 'backtest_support' must be one of {sorted(BACKTEST_SUPPORT_VALUES)}"
        )

    runtime_profile = data.get("runtime_profile", "")
    if runtime_profile and runtime_profile not in RUNTIME_PROFILES:
        result.error(
            f"manifest.yaml: 'runtime_profile' must be one of {sorted(RUNTIME_PROFILES)}"
        )

    execution_mode = data.get("execution_mode", "")
    if execution_mode and execution_mode not in EXECUTION_MODES:
        result.error(
            f"manifest.yaml: 'execution_mode' must be one of {sorted(EXECUTION_MODES)}"
        )

    if output_kind and output_kind not in OUTPUT_KINDS:
        result.error(f"manifest.yaml: 'output_kind' must be one of {sorted(OUTPUT_KINDS)}")

    follow_trade_supported = data.get("follow_trade_supported")
    if follow_trade_supported is not None and not isinstance(follow_trade_supported, bool):
        result.error("manifest.yaml: 'follow_trade_supported' must be a boolean")

    if execution_mode == "grid" and output_kind != "grid":
        result.error("manifest.yaml: 'execution_mode=grid' requires 'output_kind=grid'")
    if execution_mode == "grid" and follow_trade_supported is not False:
        result.error("manifest.yaml: 'execution_mode=grid' requires 'follow_trade_supported=false'")

    if decision_mode == "agentic" and runtime_profile != "agentic":
        result.error("manifest.yaml: 'decision_mode=agentic' requires 'runtime_profile=agentic'")
    if runtime_profile == "llm_bounded" and backtest_support == "full":
        result.error("manifest.yaml: 'runtime_profile=llm_bounded' requires 'backtest_support=none'")

    if execution_mode == "follow_trade" and follow_trade_supported is not True:
        result.error("manifest.yaml: 'execution_mode=follow_trade' requires 'follow_trade_supported=true'")

    if output_kind == "trade_strategy" and execution_mode != "follow_trade":
        result.error("manifest.yaml: output_kind 'trade_strategy' requires execution_mode = 'follow_trade'")

    if (
        backtest_support == "none"
        and execution_mode == "follow_trade"
        and runtime_profile != "llm_bounded"
    ):
        result.error(
            "manifest.yaml: live-only playbooks cannot default to 'execution_mode=follow_trade' "
            "unless runtime_profile is 'llm_bounded'"
        )

    if output_kind == "selection_basket":
        if backtest_support != "none":
            result.error("manifest.yaml: output_kind 'selection_basket' requires backtest_support = 'none'")
        if "execution_mode" in data:
            result.error("manifest.yaml: output_kind 'selection_basket' must not declare execution_mode")
        if follow_trade_supported is not False:
            result.error("manifest.yaml: output_kind 'selection_basket' requires follow_trade_supported = false")
        evidence_kind = str(data.get("official_evidence_kind", "") or "").strip()
        if evidence_kind and evidence_kind != "paper":
            result.error(
                "manifest.yaml: output_kind 'selection_basket' only supports "
                "official_evidence_kind 'paper'"
            )

    if output_kind == "grid":
        if backtest_support != "none":
            result.error("manifest.yaml: output_kind 'grid' requires backtest_support = 'none'")
        if execution_mode != "grid":
            result.error("manifest.yaml: output_kind 'grid' requires execution_mode = 'grid'")
        if follow_trade_supported is not False:
            result.error("manifest.yaml: output_kind 'grid' requires follow_trade_supported = false")
        schedule = data.get("schedule")
        if not isinstance(schedule, dict) or not str(schedule.get("cron", "") or "").strip():
            result.error(
                "manifest.yaml: output_kind 'grid' requires 'schedule.cron' "
                "(suggested default: '0 */4 * * *'); grid Playbooks run on a recurring schedule"
            )
        if not str(schedule.get("tz") or schedule.get("timezone") or "").strip():
            result.error(
                "manifest.yaml: output_kind 'grid' requires 'schedule.tz' "
                "(suggested default: 'Asia/Shanghai')"
            )
        if not isinstance(user_config_schema, dict):
            result.error(
                "manifest.yaml: output_kind 'grid' requires user_config_schema "
                "with the standard Grid product fields"
            )
        else:
            for field, required in GRID_PRODUCT_USER_CONFIG_REQUIREMENTS.items():
                spec = user_config_schema.get(field)
                prefix = f"manifest.yaml: user_config_schema.{field}"
                if not isinstance(spec, dict):
                    result.error(f"{prefix} is required by the Grid product contract")
                    continue
                for constraint, expected in required.items():
                    actual = spec.get(constraint)
                    if constraint == "options":
                        actual = set(actual) if isinstance(actual, list) else actual
                    if actual != expected:
                        rendered = sorted(expected) if isinstance(expected, set) else expected
                        result.error(f"{prefix}.{constraint} must be {rendered!r}")
        _validate_grid_strategy_config(
            strategy_config,
            user_config_schema,
            result,
        )

    schedule = data.get("schedule")
    if isinstance(schedule, dict):
        cron_expr = str(schedule.get("cron", "") or "").strip()
        schedule_tz = str(schedule.get("tz") or schedule.get("timezone") or "").strip()
        if cron_expr:
            if not schedule_tz:
                result.error(
                    "manifest.yaml.schedule.tz: scheduled Playbooks must declare "
                    f"an instance-default IANA timezone, e.g. {DEFAULT_SCHEDULE_TZ}"
                )
            else:
                try:
                    ZoneInfo(schedule_tz)
                except (ZoneInfoNotFoundError, KeyError):
                    result.error(
                        "manifest.yaml.schedule.tz: must be a valid IANA timezone "
                        f"(for example {DEFAULT_SCHEDULE_TZ})"
                    )
            parts = cron_expr.split()
            if len(parts) not in (5, 6):
                result.error("manifest.yaml.schedule.cron: must be a 5- or 6-field cron expression")
            else:
                minute_field = parts[0]
                match = CRON_EVERY_MINUTES_PATTERN.fullmatch(minute_field)
                if match and int(match.group(1)) < MIN_SCHEDULE_INTERVAL_MINUTES:
                    result.error(
                        "manifest.yaml.schedule.cron: scheduled Playbooks must not run more often "
                        f"than every {MIN_SCHEDULE_INTERVAL_MINUTES} minutes"
                    )
                elif minute_field == "*":
                    result.error(
                        "manifest.yaml.schedule.cron: scheduled Playbooks must not run every minute; "
                        f"minimum interval is {MIN_SCHEDULE_INTERVAL_MINUTES} minutes"
                    )

    _validate_long_description(
        data.get("long_description"),
        str(data.get("description") or ""),
        result,
    )

    return data


def validate_backtest_yaml(pkg_dir: Path, manifest: dict, result: ValidationResult) -> None:
    def _is_number(value: object) -> bool:
        return isinstance(value, (int, float)) and not isinstance(value, bool)

    def _string_field(payload: dict, field: str, *, prefix: str) -> None:
        if not str(payload.get(field, "") or "").strip():
            result.error(f"{prefix}: missing '{field}'")

    def _instrument_symbol(item: dict) -> str:
        raw = str(
            item.get("raw_symbol")
            or item.get("symbol")
            or str(item.get("id", "") or "").split(".", 1)[0]
            or ""
        ).strip().upper()
        return raw

    def _validate_instrument(item: dict, *, prefix: str) -> None:
        kind = str(item.get("kind", "") or "").strip().lower()
        if kind not in BACKTEST_INSTRUMENT_KINDS:
            result.error(f"{prefix}: 'kind' must be one of {sorted(BACKTEST_INSTRUMENT_KINDS)}")
        _string_field(item, "id", prefix=prefix)
        _string_field(item, "bar_type", prefix=prefix)
        _string_field(item, "base_currency", prefix=prefix)
        _string_field(item, "quote_currency", prefix=prefix)
        if not str(item.get("raw_symbol", "") or item.get("symbol", "")).strip():
            result.error(f"{prefix}: either 'raw_symbol' or 'symbol' is required")
        for field in ("price_precision", "size_precision"):
            if not isinstance(item.get(field), int):
                result.error(f"{prefix}: '{field}' must be an integer")
        for field in ("price_increment", "size_increment"):
            if not str(item.get(field, "") or "").strip():
                result.error(f"{prefix}: missing '{field}'")
        for field in ("maker_fee", "taker_fee"):
            if field not in item:
                result.error(f"{prefix}: missing '{field}' (set explicit exchange fee rate; do not rely on zero-fee backtests)")
            elif not _is_number(item.get(field)) and not str(item.get(field, "") or "").strip():
                result.error(f"{prefix}: '{field}' must be a numeric fee rate")
        if kind in {"perpetual", "perpetual_contract", "perp"}:
            _string_field(item, "settlement_currency", prefix=prefix)

    def _validate_required_bar_fields(payload: object) -> None:
        if payload is None:
            return
        if not isinstance(payload, list) or not payload:
            result.error(
                "backtest.yaml.data_requirements.required_bar_fields: must be a non-empty list when provided"
            )
            return

        seen: set[str] = set()
        for index, raw_field in enumerate(payload):
            field = str(raw_field or "").strip()
            prefix = f"backtest.yaml.data_requirements.required_bar_fields[{index}]"
            if not field:
                result.error(f"{prefix}: field name must be a non-empty string")
                continue
            if not BACKTEST_BAR_FIELD_PATTERN.fullmatch(field):
                result.error(f"{prefix}: must use lower_snake_case, got '{field}'")
                continue
            if field in seen:
                result.error(f"{prefix}: duplicate field '{field}'")
                continue
            seen.add(field)

    def _record_backtest_symbol(item: dict, *, prefix: str) -> None:
        symbol = _instrument_symbol(item)
        if symbol:
            _validate_exchange_native_symbol(
                symbol,
                prefix=f"{prefix}: symbol",
                result=result,
            )
            backtest_symbols.append((prefix, symbol))

    path = pkg_dir / "backtest.yaml"
    if not path.exists():
        return

    data = _load_yaml(path)
    if data is None:
        result.error("backtest.yaml: invalid YAML syntax")
        return

    backtest_symbols: list[tuple[str, str]] = []

    if manifest.get("backtest_support") != "full":
        result.error("backtest.yaml is only allowed when manifest.yaml sets backtest_support: full")

    if manifest.get("output_kind") == "grid":
        result.error("backtest.yaml: grid Playbooks do not support backtests; remove backtest.yaml")

    venue = data.get("venue")
    if not isinstance(venue, dict):
        result.error("backtest.yaml: 'venue' must be a mapping")
    else:
        for field in ("name", "account_type", "oms_type"):
            _string_field(venue, field, prefix="backtest.yaml.venue")
        balances = venue.get("starting_balances")
        if not isinstance(balances, list) or not balances:
            result.error("backtest.yaml.venue: 'starting_balances' must be a non-empty list")
        else:
            for index, balance in enumerate(balances):
                if isinstance(balance, str):
                    if len(balance.strip().split()) < 2:
                        result.error(
                            f"backtest.yaml.venue.starting_balances[{index}]: "
                            "string balances must look like '<amount> <CURRENCY>'"
                        )
                elif isinstance(balance, dict):
                    if not _is_number(balance.get("amount")):
                        result.error(
                            f"backtest.yaml.venue.starting_balances[{index}]: 'amount' must be a number"
                        )
                    if not str(balance.get("currency", "") or "").strip():
                        result.error(
                            f"backtest.yaml.venue.starting_balances[{index}]: 'currency' is required"
                        )
                else:
                    result.error(
                        f"backtest.yaml.venue.starting_balances[{index}]: entry must be a string or mapping"
                    )

    strategy = data.get("strategy")
    if not isinstance(strategy, dict):
        result.error("backtest.yaml: 'strategy' must be a mapping")
    else:
        for field in ("module", "class"):
            _string_field(strategy, field, prefix="backtest.yaml.strategy")
        strategy_config = strategy.get("config", {})
        if strategy_config is not None and not isinstance(strategy_config, dict):
            result.error("backtest.yaml.strategy: 'config' must be a mapping when provided")

    has_single = isinstance(data.get("instrument"), dict)
    has_many = isinstance(data.get("instruments"), list)
    if has_single and has_many:
        result.error("backtest.yaml: use either 'instrument' or 'instruments', not both")
    elif has_single:
        _validate_instrument(data["instrument"], prefix="backtest.yaml.instrument")
        _record_backtest_symbol(data["instrument"], prefix="backtest.yaml.instrument")
    elif has_many:
        instruments = data.get("instruments") or []
        if not instruments:
            result.error("backtest.yaml: 'instruments' must not be empty")
        for index, item in enumerate(instruments):
            if not isinstance(item, dict):
                result.error(f"backtest.yaml.instruments[{index}] must be a mapping")
                continue
            _validate_instrument(item, prefix=f"backtest.yaml.instruments[{index}]")
            _record_backtest_symbol(item, prefix=f"backtest.yaml.instruments[{index}]")
    else:
        result.error("backtest.yaml: missing 'instrument' or 'instruments'")

    manifest_symbols = set(_normalized_backtest_symbols(manifest))
    if manifest_symbols and backtest_symbols:
        actual_symbols = {symbol for _, symbol in backtest_symbols}
        extra_symbols = [
            f"{prefix}={symbol}"
            for prefix, symbol in backtest_symbols
            if symbol not in manifest_symbols
        ]
        missing_symbols = sorted(manifest_symbols - actual_symbols)
        if extra_symbols or missing_symbols:
            result.error(
                "backtest.yaml: instruments must match manifest.yaml trading_symbols; "
                f"unexpected backtest symbols={extra_symbols or []}, "
                f"missing manifest symbols={missing_symbols or []}"
            )

    # The replay window is the author's call: execution.start/end are optional
    # bar filters. The platform never polices window presence, length, recency,
    # or ordering — anti-fraud checks (real evidence) are the only backtest gate.
    execution = data.get("execution")
    if execution is not None and not isinstance(execution, dict):
        result.error("backtest.yaml: 'execution' must be a mapping when provided")

    data_requirements = data.get("data_requirements")
    if data_requirements is not None and not isinstance(data_requirements, dict):
        result.error("backtest.yaml: 'data_requirements' must be a mapping")
    elif isinstance(data_requirements, dict):
        _validate_required_bar_fields(data_requirements.get("required_bar_fields"))
        required_fields = data_requirements.get("required_bar_fields")
        if isinstance(required_fields, list):
            source_text = "\n".join(
                path.read_text(encoding="utf-8", errors="ignore")
                for path in (pkg_dir / "src").rglob("*.py")
            )
            for field in required_fields:
                if isinstance(field, str) and field.strip() and field.strip() not in source_text:
                    result.error(
                        "backtest.yaml.data_requirements.required_bar_fields: "
                        f"declares '{field.strip()}' but src/** never references it; "
                        "build the feature column with backtest.build_feature_frame(...) "
                        "or remove the declaration"
                    )


def _local_import_roots(pkg_dir: Path) -> set[str]:
    roots = {"src"}
    src_root = pkg_dir / "src"
    if not src_root.exists():
        return roots

    for path in src_root.rglob("*.py"):
        rel_parts = PurePosixPath(path.relative_to(src_root).as_posix()).parts
        if not rel_parts:
            continue
        first = rel_parts[0]
        if first.endswith(".py"):
            stem = first[:-3]
            if stem:
                roots.add(stem)
            continue
        roots.add(first)

    return roots


def _call_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return ""


def _attribute_path(node: ast.AST) -> list[str]:
    if isinstance(node, ast.Name):
        return [node.id]
    if isinstance(node, ast.Attribute):
        return [*_attribute_path(node.value), node.attr]
    if isinstance(node, ast.Call):
        return _attribute_path(node.func)
    return []


class _GetAgentNameResolver:
    """Resolve public getagent imports without matching comments or strings."""

    def __init__(self, tree: ast.AST) -> None:
        self.aliases: dict[str, list[str]] = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if not alias.name.startswith("getagent"):
                        continue
                    if alias.asname:
                        self.aliases[alias.asname] = alias.name.split(".")
                    else:
                        self.aliases[alias.name.split(".", 1)[0]] = ["getagent"]
            elif isinstance(node, ast.ImportFrom) and node.module:
                if not node.module.startswith("getagent"):
                    continue
                module_path = node.module.split(".")
                for alias in node.names:
                    if alias.name == "*":
                        continue
                    self.aliases[alias.asname or alias.name] = [*module_path, alias.name]
        for _ in range(3):
            changed = False
            for node in ast.walk(tree):
                value: ast.AST | None = None
                target: ast.AST | None = None
                if isinstance(node, ast.Assign) and len(node.targets) == 1:
                    target, value = node.targets[0], node.value
                elif isinstance(node, ast.AnnAssign):
                    target, value = node.target, node.value
                if not isinstance(target, ast.Name) or value is None:
                    continue
                path = self.path(value)
                if path[:1] != ["getagent"] or self.aliases.get(target.id) == path:
                    continue
                self.aliases[target.id] = path
                changed = True
            if not changed:
                break

    def path(self, node: ast.AST) -> list[str]:
        if isinstance(node, ast.Name):
            return self.aliases.get(node.id, [node.id])
        if isinstance(node, ast.Attribute):
            return [*self.path(node.value), node.attr]
        if isinstance(node, ast.Call):
            return self.path(node.func)
        return []

    def public_path(self, node: ast.AST) -> list[str]:
        path = self.path(node)
        if path[:1] == ["getagent"]:
            return path[1:]
        return path


def _call_argument(
    node: ast.Call,
    *,
    position: int,
    keyword: str,
) -> ast.AST | None:
    if len(node.args) > position:
        return node.args[position]
    for item in node.keywords:
        if item.arg == keyword:
            return item.value
    return None


def _function_definitions(tree: ast.AST) -> dict[str, ast.FunctionDef | ast.AsyncFunctionDef]:
    return {
        node.name: node
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }


def _static_bindings(tree: ast.AST) -> dict[str, ast.AST]:
    candidates: dict[str, list[ast.AST]] = {}
    for node in ast.walk(tree):
        value: ast.AST | None = None
        targets: list[ast.AST] = []
        if isinstance(node, ast.Assign):
            value = node.value
            targets = list(node.targets)
        elif isinstance(node, ast.AnnAssign):
            value = node.value
            targets = [node.target]
        if value is None:
            continue
        for target in targets:
            if isinstance(target, ast.Name):
                candidates.setdefault(target.id, []).append(value)
    return {
        name: values[0]
        for name, values in candidates.items()
        if len(values) == 1
    }


def _resolve_static_expression(
    node: ast.AST | None,
    bindings: dict[str, ast.AST],
    *,
    visited: set[str] | None = None,
) -> ast.AST | None:
    visited = set(visited or ())
    while isinstance(node, ast.Name) and node.id in bindings and node.id not in visited:
        visited.add(node.id)
        node = bindings[node.id]
    return node


def _combine_call_paths(
    left: list[list[ast.Call]],
    right: list[list[ast.Call]],
) -> list[list[ast.Call]]:
    combined = [a + b for a in left for b in right]
    return combined[:64]


def _expression_call_paths(
    node: ast.AST | None,
    *,
    functions: dict[str, ast.FunctionDef | ast.AsyncFunctionDef],
    stack: tuple[str, ...],
) -> list[list[ast.Call]] | None:
    if node is None:
        return [[]]
    if isinstance(node, (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)):
        return None
    if isinstance(node, ast.IfExp):
        test_paths = _expression_call_paths(node.test, functions=functions, stack=stack)
        body_paths = _expression_call_paths(node.body, functions=functions, stack=stack)
        else_paths = _expression_call_paths(node.orelse, functions=functions, stack=stack)
        if test_paths is None or body_paths is None or else_paths is None:
            return None
        return _combine_call_paths(test_paths, [*body_paths, *else_paths])
    if isinstance(node, (ast.BoolOp, ast.Lambda)):
        return None
    if isinstance(node, ast.Call):
        paths = [[]]
        for child in [*node.args, *(item.value for item in node.keywords)]:
            child_paths = _expression_call_paths(
                child,
                functions=functions,
                stack=stack,
            )
            if child_paths is None:
                return None
            paths = _combine_call_paths(paths, child_paths)
        if isinstance(node.func, ast.Name) and node.func.id in functions:
            helper_name = node.func.id
            if helper_name in stack:
                return None
            helper_paths = _function_call_paths(
                functions[helper_name],
                functions=functions,
                stack=(*stack, helper_name),
            )
            if helper_paths is None:
                return None
            return _combine_call_paths(paths, helper_paths)
        return [path + [node] for path in paths]

    paths = [[]]
    for child in ast.iter_child_nodes(node):
        child_paths = _expression_call_paths(
            child,
            functions=functions,
            stack=stack,
        )
        if child_paths is None:
            return None
        paths = _combine_call_paths(paths, child_paths)
    return paths


def _statement_flow_paths(
    statement: ast.stmt,
    *,
    functions: dict[str, ast.FunctionDef | ast.AsyncFunctionDef],
    stack: tuple[str, ...],
) -> list[tuple[list[ast.Call], str]] | None:
    if isinstance(statement, ast.If):
        test_paths = _expression_call_paths(
            statement.test,
            functions=functions,
            stack=stack,
        )
        body_paths = _body_flow_paths(
            statement.body,
            functions=functions,
            stack=stack,
        )
        else_paths = _body_flow_paths(
            statement.orelse,
            functions=functions,
            stack=stack,
        ) if statement.orelse else [([], "continue")]
        if test_paths is None or body_paths is None or else_paths is None:
            return None
        return [
            (test_path + branch_path, status)
            for test_path in test_paths
            for branch_path, status in [*body_paths, *else_paths]
        ][:64]
    if isinstance(
        statement,
        (ast.For, ast.AsyncFor, ast.While, ast.Try, ast.TryStar, ast.With, ast.AsyncWith, ast.Match),
    ):
        return None
    if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        return [([], "continue")]
    if isinstance(statement, ast.Return):
        paths = _expression_call_paths(
            statement.value,
            functions=functions,
            stack=stack,
        )
        return None if paths is None else [(path, "return") for path in paths]
    if isinstance(statement, ast.Expr):
        paths = _expression_call_paths(
            statement.value,
            functions=functions,
            stack=stack,
        )
        return None if paths is None else [(path, "continue") for path in paths]
    if isinstance(statement, ast.Assign):
        paths = _expression_call_paths(
            statement.value,
            functions=functions,
            stack=stack,
        )
        return None if paths is None else [(path, "continue") for path in paths]
    if isinstance(statement, ast.AnnAssign):
        paths = _expression_call_paths(
            statement.value,
            functions=functions,
            stack=stack,
        )
        return None if paths is None else [(path, "continue") for path in paths]
    if isinstance(statement, ast.Raise):
        paths = _expression_call_paths(
            statement.exc,
            functions=functions,
            stack=stack,
        )
        return None if paths is None else [(path, "raise") for path in paths]
    if isinstance(statement, (ast.Pass, ast.Break, ast.Continue)):
        return [([], "continue")]
    return None


def _body_flow_paths(
    statements: list[ast.stmt],
    *,
    functions: dict[str, ast.FunctionDef | ast.AsyncFunctionDef],
    stack: tuple[str, ...],
) -> list[tuple[list[ast.Call], str]] | None:
    paths: list[tuple[list[ast.Call], str]] = [([], "continue")]
    for statement in statements:
        statement_paths = _statement_flow_paths(
            statement,
            functions=functions,
            stack=stack,
        )
        if statement_paths is None:
            return None
        combined: list[tuple[list[ast.Call], str]] = []
        for current_calls, current_status in paths:
            if current_status != "continue":
                combined.append((current_calls, current_status))
                continue
            for statement_calls, statement_status in statement_paths:
                combined.append(
                    (current_calls + statement_calls, statement_status)
                )
        paths = combined[:64]
    return paths


def _body_call_paths(
    statements: list[ast.stmt],
    *,
    functions: dict[str, ast.FunctionDef | ast.AsyncFunctionDef],
    stack: tuple[str, ...],
) -> list[list[ast.Call]] | None:
    flows = _body_flow_paths(statements, functions=functions, stack=stack)
    if flows is None:
        return None
    return [calls for calls, status in flows if status != "raise"]


def _function_call_paths(
    function: ast.FunctionDef | ast.AsyncFunctionDef,
    *,
    functions: dict[str, ast.FunctionDef | ast.AsyncFunctionDef],
    stack: tuple[str, ...],
) -> list[list[ast.Call]] | None:
    return _body_call_paths(function.body, functions=functions, stack=stack)


def _callback_flow_paths(
    callback: ast.AST,
    *,
    functions: dict[str, ast.FunctionDef | ast.AsyncFunctionDef],
) -> list[tuple[list[ast.Call], str]] | None:
    """Return every statically verifiable call path through one callback."""

    if isinstance(callback, ast.Lambda):
        paths = _expression_call_paths(callback.body, functions=functions, stack=())
        return None if paths is None else [(path, "return") for path in paths]
    if isinstance(callback, ast.Name) and callback.id in functions:
        return _body_flow_paths(
            functions[callback.id].body,
            functions=functions,
            stack=(callback.id,),
        )
    return None


def _reachable_callback_functions(
    callback: ast.AST,
    *,
    functions: dict[str, ast.FunctionDef | ast.AsyncFunctionDef],
) -> list[tuple[str, ast.FunctionDef | ast.AsyncFunctionDef]]:
    pending: list[str] = []
    if isinstance(callback, ast.Name) and callback.id in functions:
        pending.append(callback.id)
    elif isinstance(callback, ast.Lambda):
        pending.extend(
            node.func.id
            for node in ast.walk(callback.body)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id in functions
        )

    reachable: list[tuple[str, ast.FunctionDef | ast.AsyncFunctionDef]] = []
    visited: set[str] = set()
    while pending:
        name = pending.pop()
        if name in visited:
            continue
        visited.add(name)
        function = functions[name]
        reachable.append((name, function))
        pending.extend(
            node.func.id
            for node in _direct_function_nodes(function)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id in functions
            and node.func.id not in visited
        )
    return reachable


def _trade_call(
    node: ast.Call,
    resolver: _GetAgentNameResolver,
) -> tuple[str, str] | None:
    path = resolver.public_path(node.func)
    if len(path) < 3 or path[-3] != "trade":
        return None
    namespace, method = path[-2], path[-1]
    if namespace not in {"account", "contract", "grid", "spot"}:
        return None
    return namespace, method


def _is_trade_mutation(namespace: str, method: str) -> bool:
    if namespace == "grid":
        return method in GRID_MUTATION_METHODS
    return namespace in {"account", "contract", "spot"} and method in TRADE_MUTATION_METHODS


def _is_strategy_bot_wrapper(node: ast.Call, resolver: _GetAgentNameResolver) -> bool:
    return resolver.public_path(node.func)[-2:] == [
        "runtime",
        "execute_strategy_bot_action",
    ]


def _is_emit_decision(node: ast.Call, resolver: _GetAgentNameResolver) -> bool:
    return resolver.public_path(node.func)[-2:] == ["runtime", "emit_decision"]


class _BotIdScope:
    def __init__(
        self,
        parent: "_BotIdScope | None",
        owner: ast.FunctionDef | ast.AsyncFunctionDef | None = None,
    ) -> None:
        self.parent = parent
        self.owner = owner
        self.assignments: dict[str, list[tuple[int, ast.AST]]] = {}
        self.iterations: dict[str, list[tuple[int, ast.AST]]] = {}
        self.bound_names: set[str] = set()
        self.parameters: set[str] = set()
        self.parameter_defaults: dict[str, tuple[ast.AST, "_BotIdScope", int]] = {}


class _BotIdScopeIndex(ast.NodeVisitor):
    """Index bot-ID data flow without crossing Python lexical shadowing."""

    def __init__(self, tree: ast.AST) -> None:
        self.tree = tree
        self.root = _BotIdScope(None)
        self.current = self.root
        self.scope_by_node: dict[int, _BotIdScope] = {}
        self.visit(tree)
        for scope in set(self.scope_by_node.values()):
            for values in scope.assignments.values():
                values.sort(key=lambda item: item[0])
            for values in scope.iterations.values():
                values.sort(key=lambda item: item[0])

    def generic_visit(self, node: ast.AST) -> None:
        self.scope_by_node[id(node)] = self.current
        super().generic_visit(node)

    def _bind_target(self, target: ast.AST, value: ast.AST | None = None) -> None:
        for name in _target_names(target):
            self.current.bound_names.add(name)
            if value is not None:
                self.current.assignments.setdefault(name, []).append(
                    (getattr(target, "lineno", getattr(value, "lineno", 0)), value)
                )

    def visit_Assign(self, node: ast.Assign) -> None:
        self.scope_by_node[id(node)] = self.current
        self.visit(node.value)
        for target in node.targets:
            self._bind_target(target, node.value)
            self.visit(target)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        self.scope_by_node[id(node)] = self.current
        if node.value is not None:
            self.visit(node.value)
        self._bind_target(node.target, node.value)
        self.visit(node.target)
        self.visit(node.annotation)

    def visit_NamedExpr(self, node: ast.NamedExpr) -> None:
        self.scope_by_node[id(node)] = self.current
        self.visit(node.value)
        self._bind_target(node.target, node.value)
        self.visit(node.target)

    def visit_For(self, node: ast.For) -> None:
        self.scope_by_node[id(node)] = self.current
        self.visit(node.iter)
        self._bind_target(node.target)
        for name in _target_names(node.target):
            self.current.iterations.setdefault(name, []).append(
                (node.lineno, node.iter)
            )
        self.visit(node.target)
        for statement in [*node.body, *node.orelse]:
            self.visit(statement)

    visit_AsyncFor = visit_For

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._visit_function(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._visit_function(node)

    def _visit_function(
        self,
        node: ast.FunctionDef | ast.AsyncFunctionDef,
    ) -> None:
        self.scope_by_node[id(node)] = self.current
        self.current.bound_names.add(node.name)
        for item in [*node.decorator_list, *node.args.defaults]:
            self.visit(item)
        for item in node.args.kw_defaults:
            if item is not None:
                self.visit(item)
        if node.returns is not None:
            self.visit(node.returns)

        parent = self.current
        scope = _BotIdScope(parent, node)
        positional = [*node.args.posonlyargs, *node.args.args]
        defaults = [None] * (len(positional) - len(node.args.defaults)) + list(
            node.args.defaults
        )
        for argument, default in zip(positional, defaults):
            scope.parameters.add(argument.arg)
            scope.bound_names.add(argument.arg)
            if default is not None:
                scope.parameter_defaults[argument.arg] = (
                    default,
                    parent,
                    node.lineno,
                )
        for argument, default in zip(node.args.kwonlyargs, node.args.kw_defaults):
            scope.parameters.add(argument.arg)
            scope.bound_names.add(argument.arg)
            if default is not None:
                scope.parameter_defaults[argument.arg] = (
                    default,
                    parent,
                    node.lineno,
                )
        for argument in (node.args.vararg, node.args.kwarg):
            if argument is not None:
                scope.parameters.add(argument.arg)
                scope.bound_names.add(argument.arg)

        self.current = scope
        for statement in node.body:
            self.visit(statement)
        self.current = parent

    def visit_Lambda(self, node: ast.Lambda) -> None:
        self.scope_by_node[id(node)] = self.current
        for item in [*node.args.defaults, *node.args.kw_defaults]:
            if item is not None:
                self.visit(item)

        parent = self.current
        scope = _BotIdScope(parent)
        positional = [*node.args.posonlyargs, *node.args.args]
        defaults = [None] * (len(positional) - len(node.args.defaults)) + list(
            node.args.defaults
        )
        for argument, default in zip(positional, defaults):
            scope.parameters.add(argument.arg)
            scope.bound_names.add(argument.arg)
            if default is not None:
                scope.parameter_defaults[argument.arg] = (
                    default,
                    parent,
                    node.lineno,
                )
        for argument, default in zip(node.args.kwonlyargs, node.args.kw_defaults):
            scope.parameters.add(argument.arg)
            scope.bound_names.add(argument.arg)
            if default is not None:
                scope.parameter_defaults[argument.arg] = (
                    default,
                    parent,
                    node.lineno,
                )
        for argument in (node.args.vararg, node.args.kwarg):
            if argument is not None:
                scope.parameters.add(argument.arg)
                scope.bound_names.add(argument.arg)

        self.current = scope
        self.visit(node.body)
        self.current = parent


def _direct_function_nodes(
    function: ast.FunctionDef | ast.AsyncFunctionDef,
) -> list[ast.AST]:
    nodes: list[ast.AST] = []
    pending: list[ast.AST] = list(function.body)
    while pending:
        node = pending.pop()
        nodes.append(node)
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
                continue
            pending.append(child)
    return nodes


def _is_runtime_strategy_bot_call(
    node: ast.AST,
    *,
    method: str,
    resolver: _GetAgentNameResolver,
) -> bool:
    return (
        isinstance(node, ast.Call)
        and resolver.public_path(node.func)[-2:] == ["runtime", method]
    )


def _parameter_call_values(
    *,
    name: str,
    scope: _BotIdScope,
    scopes: _BotIdScopeIndex,
) -> list[tuple[ast.AST, _BotIdScope, int]]:
    owner = scope.owner
    if owner is None:
        return []
    positional = [*owner.args.posonlyargs, *owner.args.args]
    position = next(
        (index for index, argument in enumerate(positional) if argument.arg == name),
        None,
    )
    values: list[tuple[ast.AST, _BotIdScope, int]] = []
    for node in ast.walk(scopes.tree):
        if (
            not isinstance(node, ast.Call)
            or not isinstance(node.func, ast.Name)
            or node.func.id != owner.name
        ):
            continue
        value: ast.AST | None = None
        if position is not None and len(node.args) > position:
            value = node.args[position]
        else:
            value = next(
                (
                    keyword.value
                    for keyword in node.keywords
                    if keyword.arg == name
                ),
                None,
            )
        if value is not None:
            values.append(
                (
                    value,
                    scopes.scope_by_node.get(id(value), scopes.root),
                    node.lineno,
                )
            )
    return values


def _strategy_bot_collection_has_trusted_source(
    node: ast.AST | None,
    *,
    scopes: _BotIdScopeIndex,
    resolver: _GetAgentNameResolver,
    functions: dict[str, ast.FunctionDef | ast.AsyncFunctionDef],
    before_line: int,
    scope: _BotIdScope | None = None,
    visiting: set[tuple[str, int, str]] | None = None,
) -> bool:
    if node is None:
        return False
    if _is_runtime_strategy_bot_call(
        node,
        method="list_strategy_bots",
        resolver=resolver,
    ):
        return True
    if isinstance(node, ast.Call):
        if (
            isinstance(node.func, ast.Name)
            and node.func.id in {"list", "tuple", "set"}
            and len(node.args) == 1
            and not node.keywords
        ):
            return _strategy_bot_collection_has_trusted_source(
                node.args[0],
                scopes=scopes,
                resolver=resolver,
                functions=functions,
                before_line=before_line,
                scope=scope,
                visiting=visiting,
            )
        if (
            isinstance(node.func, ast.Attribute)
            and node.func.attr == "values"
            and not node.args
            and not node.keywords
        ):
            return _strategy_bot_collection_has_trusted_source(
                node.func.value,
                scopes=scopes,
                resolver=resolver,
                functions=functions,
                before_line=before_line,
                scope=scope,
                visiting=visiting,
            )
        if isinstance(node.func, ast.Name) and node.func.id in functions:
            function = functions[node.func.id]
            visiting = set(visiting or ())
            key = ("function", id(function), node.func.id)
            if key in visiting:
                return False
            visiting.add(key)
            returns = [
                item
                for item in _direct_function_nodes(function)
                if isinstance(item, ast.Return) and item.value is not None
            ]
            if not returns:
                return False
            for returned in returns:
                value = returned.value
                if isinstance(value, ast.Name):
                    writes = [
                        item
                        for item in _direct_function_nodes(function)
                        if isinstance(item, ast.Assign)
                        and any(
                            isinstance(target, ast.Subscript)
                            and isinstance(target.value, ast.Name)
                            and target.value.id == value.id
                            for target in item.targets
                        )
                    ]
                    if writes and all(
                        _strategy_bot_object_has_trusted_source(
                            item.value,
                            scopes=scopes,
                            resolver=resolver,
                            functions=functions,
                            before_line=item.lineno,
                            scope=scopes.scope_by_node.get(id(item.value)),
                            visiting=visiting,
                        )
                        for item in writes
                    ):
                        continue
                if not _strategy_bot_collection_has_trusted_source(
                    value,
                    scopes=scopes,
                    resolver=resolver,
                    functions=functions,
                    before_line=returned.lineno,
                    scope=scopes.scope_by_node.get(id(value)),
                    visiting=visiting,
                ):
                    return False
            return True
    if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
        return bool(node.elts) and all(
            _strategy_bot_object_has_trusted_source(
                item,
                scopes=scopes,
                resolver=resolver,
                functions=functions,
                before_line=getattr(item, "lineno", before_line),
                scope=scopes.scope_by_node.get(id(item), scope),
                visiting=visiting,
            )
            for item in node.elts
        )
    if isinstance(node, ast.Name):
        visiting = set(visiting or ())
        scope = scope or scopes.scope_by_node.get(id(node), scopes.root)
        key = ("collection", id(scope), node.id)
        if key in visiting:
            return False
        visiting.add(key)
        if node.id in scope.parameter_defaults:
            default, default_scope, default_line = scope.parameter_defaults[node.id]
            return _strategy_bot_collection_has_trusted_source(
                default,
                scopes=scopes,
                resolver=resolver,
                functions=functions,
                before_line=default_line,
                scope=default_scope,
                visiting=visiting,
            )
        if node.id in scope.parameters:
            call_values = _parameter_call_values(
                name=node.id,
                scope=scope,
                scopes=scopes,
            )
            return bool(call_values) and all(
                _strategy_bot_collection_has_trusted_source(
                    value,
                    scopes=scopes,
                    resolver=resolver,
                    functions=functions,
                    before_line=call_line,
                    scope=call_scope,
                    visiting=visiting,
                )
                for value, call_scope, call_line in call_values
            )
        candidates = [
            (line, value)
            for line, value in scope.assignments.get(node.id, [])
            if line < before_line
        ]
        if candidates:
            line, value = candidates[-1]
            return _strategy_bot_collection_has_trusted_source(
                value,
                scopes=scopes,
                resolver=resolver,
                functions=functions,
                before_line=line,
                scope=scopes.scope_by_node.get(id(value), scope),
                visiting=visiting,
            )
        if node.id in scope.bound_names or scope.parent is None:
            return False
        return _strategy_bot_collection_has_trusted_source(
            node,
            scopes=scopes,
            resolver=resolver,
            functions=functions,
            before_line=before_line,
            scope=scope.parent,
            visiting=visiting,
        )
    return False


def _strategy_bot_object_has_trusted_source(
    node: ast.AST | None,
    *,
    scopes: _BotIdScopeIndex,
    resolver: _GetAgentNameResolver,
    functions: dict[str, ast.FunctionDef | ast.AsyncFunctionDef],
    before_line: int,
    scope: _BotIdScope | None = None,
    visiting: set[tuple[str, int, str]] | None = None,
) -> bool:
    if node is None:
        return False
    if _is_runtime_strategy_bot_call(
        node,
        method="execute_strategy_bot_action",
        resolver=resolver,
    ):
        return True
    if isinstance(node, ast.Subscript):
        return _strategy_bot_collection_has_trusted_source(
            node.value,
            scopes=scopes,
            resolver=resolver,
            functions=functions,
            before_line=before_line,
            scope=scope,
            visiting=visiting,
        )
    if isinstance(node, ast.Name):
        visiting = set(visiting or ())
        scope = scope or scopes.scope_by_node.get(id(node), scopes.root)
        key = ("object", id(scope), node.id)
        if key in visiting:
            return False
        visiting.add(key)
        if node.id in scope.parameter_defaults:
            default, default_scope, default_line = scope.parameter_defaults[node.id]
            return _strategy_bot_object_has_trusted_source(
                default,
                scopes=scopes,
                resolver=resolver,
                functions=functions,
                before_line=default_line,
                scope=default_scope,
                visiting=visiting,
            )
        if node.id in scope.parameters:
            call_values = _parameter_call_values(
                name=node.id,
                scope=scope,
                scopes=scopes,
            )
            return bool(call_values) and all(
                _strategy_bot_object_has_trusted_source(
                    value,
                    scopes=scopes,
                    resolver=resolver,
                    functions=functions,
                    before_line=call_line,
                    scope=call_scope,
                    visiting=visiting,
                )
                for value, call_scope, call_line in call_values
            )
        assignments = [
            (line, value)
            for line, value in scope.assignments.get(node.id, [])
            if line < before_line
        ]
        iterations = [
            (line, value)
            for line, value in scope.iterations.get(node.id, [])
            if line < before_line
        ]
        candidates = [
            *[(line, "assignment", value) for line, value in assignments],
            *[(line, "iteration", value) for line, value in iterations],
        ]
        if candidates:
            line, kind, value = max(candidates, key=lambda item: item[0])
            if kind == "iteration":
                return _strategy_bot_collection_has_trusted_source(
                    value,
                    scopes=scopes,
                    resolver=resolver,
                    functions=functions,
                    before_line=line,
                    scope=scopes.scope_by_node.get(id(value), scope),
                    visiting=visiting,
                )
            return _strategy_bot_object_has_trusted_source(
                value,
                scopes=scopes,
                resolver=resolver,
                functions=functions,
                before_line=line,
                scope=scopes.scope_by_node.get(id(value), scope),
                visiting=visiting,
            )
        if node.id in scope.bound_names or scope.parent is None:
            return False
        return _strategy_bot_object_has_trusted_source(
            node,
            scopes=scopes,
            resolver=resolver,
            functions=functions,
            before_line=before_line,
            scope=scope.parent,
            visiting=visiting,
        )
    return False


def _bot_id_has_trusted_source(
    node: ast.AST | None,
    *,
    scopes: _BotIdScopeIndex,
    resolver: _GetAgentNameResolver,
    functions: dict[str, ast.FunctionDef | ast.AsyncFunctionDef],
    before_line: int,
    scope: _BotIdScope | None = None,
    visiting: set[tuple[str, int, str]] | None = None,
) -> bool:
    if node is None:
        return False
    if isinstance(node, ast.Attribute):
        return (
            node.attr == "strategy_bot_id"
            and _strategy_bot_object_has_trusted_source(
                node.value,
                scopes=scopes,
                resolver=resolver,
                functions=functions,
                before_line=before_line,
                scope=scope,
                visiting=visiting,
            )
        )
    if (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "str"
        and len(node.args) == 1
    ):
        return _bot_id_has_trusted_source(
            node.args[0],
            scopes=scopes,
            resolver=resolver,
            functions=functions,
            before_line=before_line,
            scope=scope,
            visiting=visiting,
        )
    if isinstance(node, ast.Name):
        visiting = set(visiting or ())
        scope = scope or scopes.scope_by_node.get(id(node), scopes.root)
        key = ("bot_id", id(scope), node.id)
        if key in visiting:
            return False
        visiting.add(key)
        if node.id in scope.parameter_defaults:
            default, default_scope, default_line = scope.parameter_defaults[node.id]
            return _bot_id_has_trusted_source(
                default,
                scopes=scopes,
                resolver=resolver,
                functions=functions,
                before_line=default_line,
                scope=default_scope,
                visiting=visiting,
            )
        if node.id in scope.parameters:
            call_values = _parameter_call_values(
                name=node.id,
                scope=scope,
                scopes=scopes,
            )
            return bool(call_values) and all(
                _bot_id_has_trusted_source(
                    value,
                    scopes=scopes,
                    resolver=resolver,
                    functions=functions,
                    before_line=call_line,
                    scope=call_scope,
                    visiting=visiting,
                )
                for value, call_scope, call_line in call_values
            )
        candidates = [
            (line, value)
            for line, value in scope.assignments.get(node.id, [])
            if line < before_line
        ]
        if candidates:
            line, value = candidates[-1]
            return _bot_id_has_trusted_source(
                value,
                scopes=scopes,
                resolver=resolver,
                functions=functions,
                before_line=line,
                scope=scopes.scope_by_node.get(id(value), scope),
                visiting=visiting,
            )
        if node.id in scope.bound_names:
            return False
        if scope.parent is None:
            return False
        return _bot_id_has_trusted_source(
            node,
            scopes=scopes,
            resolver=resolver,
            functions=functions,
            before_line=before_line,
            scope=scope.parent,
            visiting=visiting,
        )
    return False


def _check_grid_orchestration(
    tree: ast.AST,
    *,
    source_path: str,
) -> tuple[list[str], int]:
    """Validate Grid lifecycle orchestration using Python AST relationships."""

    errors: list[str] = []
    resolver = _GetAgentNameResolver(tree)
    functions = _function_definitions(tree)
    bindings = _static_bindings(tree)
    bot_id_scopes = _BotIdScopeIndex(tree)
    calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call)]
    wrappers = [node for node in calls if _is_strategy_bot_wrapper(node, resolver)]
    allowed_grid_mutations: set[int] = set()

    for node in calls:
        trade_call = _trade_call(node, resolver)
        if trade_call is None or trade_call[0] != "grid":
            continue
        if trade_call[1] not in {
            "validate",
            "create_bot",
            "modify_bot",
            "add_investment",
        }:
            continue
        funds_source_node = _call_argument(
            node,
            position=999,
            keyword="funds_source",
        )
        if funds_source_node is None:
            continue
        funds_source_node = _resolve_static_expression(
            funds_source_node,
            bindings,
        )
        try:
            literal_funds_source = ast.literal_eval(funds_source_node)
        except (ValueError, TypeError):
            continue
        if literal_funds_source not in (["funding"], ("funding",)):
            errors.append(
                f"{source_path}: trade.grid.{trade_call[1]}() explicit "
                "funds_source must be ['funding'] "
                f"(line {node.lineno})"
            )

    for node in calls:
        if not _is_emit_decision(node, resolver):
            continue
        action_node = _call_argument(node, position=0, keyword="action")
        action_node = _resolve_static_expression(action_node, bindings)
        action = _literal_str(action_node) if action_node is not None else None
        if action in {"create", "modify", "shutdown"}:
            errors.append(
                f"{source_path}: direct runtime.emit_decision(action={action!r}) "
                f"cannot execute a Grid mutation (line {node.lineno}); use "
                "runtime.execute_strategy_bot_action(...) with an execute= callback"
            )
        elif action is None:
            errors.append(
                f"{source_path}: dynamic runtime.emit_decision action cannot be "
                f"validated in a Grid Playbook (line {node.lineno}); use a literal "
                "watch action or execute_strategy_bot_action(...)"
            )

    for wrapper in wrappers:
        action_node = _call_argument(wrapper, position=0, keyword="action")
        action_node = _resolve_static_expression(action_node, bindings)
        action = _literal_str(action_node) if action_node is not None else None
        if action not in DECISION_ACTIONS:
            errors.append(
                f"{source_path}: execute_strategy_bot_action action must be a "
                f"literal from {sorted(DECISION_ACTIONS)} (line {wrapper.lineno})"
            )
            continue

        execute_node = _call_argument(wrapper, position=999, keyword="execute")
        sub_action_node = _call_argument(wrapper, position=999, keyword="sub_action")
        sub_action_node = _resolve_static_expression(sub_action_node, bindings)
        sub_action = _literal_str(sub_action_node) if sub_action_node is not None else None

        if action == "watch":
            if execute_node is not None and not (
                isinstance(execute_node, ast.Constant) and execute_node.value is None
            ):
                errors.append(
                    f"{source_path}: action='watch' must not provide execute= "
                    f"(line {wrapper.lineno})"
                )
            if sub_action not in DECISION_WATCH_SUB_ACTIONS:
                errors.append(
                    f"{source_path}: action='watch' requires literal sub_action in "
                    f"{sorted(DECISION_WATCH_SUB_ACTIONS)} (line {wrapper.lineno})"
                )
            continue

        if sub_action_node is not None:
            errors.append(
                f"{source_path}: sub_action is only valid for action='watch' "
                f"(line {wrapper.lineno})"
            )
        if execute_node is None or (
            isinstance(execute_node, ast.Constant) and execute_node.value is None
        ):
            errors.append(
                f"{source_path}: action={action!r} requires an execute= callback "
                f"(line {wrapper.lineno})"
            )
            continue

        callback_flows = _callback_flow_paths(execute_node, functions=functions)
        if callback_flows is None:
            errors.append(
                f"{source_path}: execute= callback for action={action!r} uses "
                f"control flow that cannot guarantee exactly one mutation "
                f"(line {wrapper.lineno}); use a lambda or a named local function "
                "with straight-line code or explicit if/else branches"
            )
            continue
        mutation_flows = [
            ([
                (call, trade_call)
                for call in path
                if (trade_call := _trade_call(call, resolver)) is not None
                and _is_trade_mutation(*trade_call)
            ], status)
            for path, status in callback_flows
        ]
        raised_mutation_counts = sorted({
            len(path)
            for path, status in mutation_flows
            if status == "raise" and path
        })
        root_callback_name = execute_node.id if isinstance(execute_node, ast.Name) else None
        nested_raised_mutation_counts: set[int] = set()
        for helper_name, helper in _reachable_callback_functions(
            execute_node,
            functions=functions,
        ):
            if helper_name == root_callback_name:
                continue
            helper_flows = _body_flow_paths(
                helper.body,
                functions=functions,
                stack=(helper_name,),
            )
            if helper_flows is None:
                continue
            for helper_path, helper_status in helper_flows:
                if helper_status != "raise":
                    continue
                mutation_count = sum(
                    1
                    for call in helper_path
                    if (trade_call := _trade_call(call, resolver)) is not None
                    and _is_trade_mutation(*trade_call)
                )
                if mutation_count:
                    nested_raised_mutation_counts.add(mutation_count)
        raised_mutation_counts = sorted({
            *raised_mutation_counts,
            *nested_raised_mutation_counts,
        })
        if raised_mutation_counts:
            errors.append(
                f"{source_path}: action={action!r} execute= callback mutates before "
                f"raising; observed raised-path counts {raised_mutation_counts} "
                f"(line {wrapper.lineno})"
            )
            continue
        mutation_paths = [
            path for path, status in mutation_flows if status != "raise"
        ]
        mutation_counts = sorted({len(path) for path in mutation_paths})
        if not mutation_paths or mutation_counts != [1]:
            errors.append(
                f"{source_path}: every path through action={action!r} execute= "
                f"callback must perform exactly one trade mutation; observed "
                f"path counts {mutation_counts or [0]} (line {wrapper.lineno})"
            )
            continue

        expected_methods = GRID_ACTION_MUTATION_METHODS[action]
        mutations_by_id: dict[int, tuple[ast.Call, tuple[str, str]]] = {}
        for mutation_path in mutation_paths:
            mutation, (namespace, method) = mutation_path[0]
            mutations_by_id[id(mutation)] = (mutation, (namespace, method))
            if namespace != "grid" or method not in expected_methods:
                errors.append(
                    f"{source_path}: action={action!r} execute= callback must call one "
                    f"of trade.grid.{sorted(expected_methods)}, got "
                    f"trade.{namespace}.{method}() (line {mutation.lineno})"
                )
        if any(
            namespace != "grid" or method not in expected_methods
            for _, (namespace, method) in mutations_by_id.values()
        ):
            continue
        allowed_grid_mutations.update(mutations_by_id)
        callback_root: ast.AST | None = None
        if isinstance(execute_node, ast.Lambda):
            callback_root = execute_node.body
        elif isinstance(execute_node, ast.Name):
            callback_root = functions.get(execute_node.id)
        if callback_root is not None:
            for callback_node in ast.walk(callback_root):
                if not isinstance(callback_node, ast.Call):
                    continue
                callback_trade_call = _trade_call(callback_node, resolver)
                if (
                    callback_trade_call is not None
                    and callback_trade_call[0] == "grid"
                    and _is_trade_mutation(*callback_trade_call)
                ):
                    allowed_grid_mutations.add(id(callback_node))

        if action not in {"modify", "shutdown"}:
            continue
        params_node = _resolve_static_expression(
            _call_argument(wrapper, position=999, keyword="params"),
            bindings,
        )
        params_bot_id = (
            _dict_literal_value(params_node, "bot_id")
            if isinstance(params_node, ast.Dict)
            else None
        )
        params_bot_id_trusted = _bot_id_has_trusted_source(
            params_bot_id,
            scopes=bot_id_scopes,
            resolver=resolver,
            functions=functions,
            before_line=wrapper.lineno,
        )
        if not params_bot_id_trusted:
            errors.append(
                f"{source_path}: action={action!r} params.bot_id must trace to "
                "StrategyBotActionResult.strategy_bot_id or "
                "StrategyBotSnapshot.strategy_bot_id (including state IDs "
                f"canonicalized against a snapshot), never a symbol (line {wrapper.lineno})"
            )
        for mutation, (_, method) in mutations_by_id.values():
            trade_bot_id = _call_argument(mutation, position=0, keyword="bot_id")
            trade_bot_id_trusted = _bot_id_has_trusted_source(
                trade_bot_id,
                scopes=bot_id_scopes,
                resolver=resolver,
                functions=functions,
                before_line=mutation.lineno,
            )
            if not trade_bot_id_trusted:
                errors.append(
                    f"{source_path}: trade.grid.{method}() bot_id must trace to "
                    "a wrapper result or platform snapshot strategy_bot_id "
                    f"(line {mutation.lineno})"
                )
            if (
                params_bot_id is not None
                and trade_bot_id is not None
                and ast.dump(params_bot_id, include_attributes=False)
                != ast.dump(trade_bot_id, include_attributes=False)
            ):
                errors.append(
                    f"{source_path}: action={action!r} params.bot_id and "
                    f"trade.grid.{method}(..., bot_id=...) must target the same "
                    f"expression (line {wrapper.lineno})"
                )

    for node in calls:
        trade_call = _trade_call(node, resolver)
        if trade_call is None or not _is_trade_mutation(*trade_call):
            continue
        namespace, method = trade_call
        if namespace in {"account", "contract", "spot"}:
            errors.append(
                f"{source_path}: trade.{namespace}.{method}() is not allowed in "
                f"execution_mode=grid (line {node.lineno}); Grid Playbooks may "
                "mutate only trade.grid inside execute_strategy_bot_action"
            )
        elif id(node) not in allowed_grid_mutations:
            errors.append(
                f"{source_path}: trade.grid.{method}() must be inside the "
                "statically resolved execute= callback of "
                f"runtime.execute_strategy_bot_action(...) (line {node.lineno})"
            )

    return errors, len(wrappers)


def _target_names(target: ast.AST) -> list[str]:
    if isinstance(target, ast.Name):
        return [target.id]
    if isinstance(target, (ast.Tuple, ast.List)):
        names: list[str] = []
        for item in target.elts:
            names.extend(_target_names(item))
        return names
    return []


def _position_selection_assignments(tree: ast.AST) -> dict[str, str]:
    selections: dict[str, str] = {}
    for node in ast.walk(tree):
        value: ast.AST | None = None
        targets: list[ast.AST] = []
        if isinstance(node, ast.Assign):
            value = node.value
            targets = list(node.targets)
        elif isinstance(node, ast.AnnAssign):
            value = node.value
            targets = [node.target]
        elif isinstance(node, ast.NamedExpr):
            value = node.value
            targets = [node.target]
        if not isinstance(value, ast.Call):
            continue
        helper_name = _call_name(value.func)
        if helper_name not in POSITION_SELECTION_HELPERS:
            continue
        for target in targets:
            for name in _target_names(target):
                selections[name] = helper_name
    return selections


def _check_position_selection_attributes(tree: ast.AST, *, source_path: str) -> list[str]:
    selections = _position_selection_assignments(tree)
    if not selections:
        return []

    errors: list[str] = []
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Attribute)
            and isinstance(node.value, ast.Name)
            and node.value.id in selections
            and node.attr in POSITION_SELECTION_INVALID_ATTRS
        ):
            errors.append(
                f"{source_path}: PositionSelection returned by trade.helpers."
                f"{selections[node.value.id]}() does not expose '.{node.attr}' "
                f"(line {node.lineno}); use '.raw' or contract_position_records(...) "
                "for exchange-specific position fields"
            )
    return errors


def _unwrap_str_call(node: ast.AST) -> ast.AST:
    if (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "str"
        and len(node.args) == 1
        and not node.keywords
    ):
        return node.args[0]
    return node


def _is_fixed_precision_round(node: ast.AST) -> bool:
    unwrapped = _unwrap_str_call(node)
    if not isinstance(unwrapped, ast.Call):
        return False
    if _call_name(unwrapped.func) != "round" or len(unwrapped.args) < 2:
        return False
    precision_arg = unwrapped.args[1]
    return isinstance(precision_arg, ast.Constant) and isinstance(precision_arg.value, int)


def _check_contract_trigger_price_rounding(tree: ast.AST, *, source_path: str) -> list[str]:
    errors: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if _call_name(node.func) not in CONTRACT_ORDER_HELPERS:
            continue
        for keyword in node.keywords:
            if keyword.arg not in CONTRACT_TRIGGER_PRICE_KEYWORDS:
                continue
            if _is_fixed_precision_round(keyword.value):
                errors.append(
                    f"{source_path}: {keyword.arg} passed to trade.contract."
                    f"{_call_name(node.func)}() uses fixed round(..., N) precision "
                    f"(line {keyword.value.lineno}); use trade.helpers.resolve_contract_tpsl(...) "
                    "or contract_rules(symbol).price_step to align trigger prices with exchange tick size"
                )
    return errors


def _check_contract_tpsl_helper_call(tree: ast.AST, *, source_path: str) -> list[str]:
    errors: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if _attribute_path(node.func)[-3:] != ["trade", "helpers", CONTRACT_TPSL_HELPER]:
            continue
        if node.args:
            errors.append(
                f"{source_path}: trade.helpers.resolve_contract_tpsl() is keyword-only "
                f"(line {node.lineno}); pass symbol=..., side=..., leverage=..., and optional "
                "tp_trigger_price/sl_trigger_price/reference_price/product_type explicitly"
            )
        for keyword in node.keywords:
            if keyword.arg is None:
                errors.append(
                    f"{source_path}: trade.helpers.resolve_contract_tpsl() cannot be validated with **kwargs "
                    f"(line {node.lineno}); pass only explicit supported TP/SL keywords"
                )
                continue
            if keyword.arg not in CONTRACT_TPSL_HELPER_KEYWORDS:
                errors.append(
                    f"{source_path}: unsupported keyword '{keyword.arg}' passed to "
                    f"trade.helpers.resolve_contract_tpsl() (line {keyword.value.lineno}); "
                    "compute concrete tp_trigger_price/sl_trigger_price values instead of using "
                    "percentage override kwargs"
                )
    return errors


def _check_data_provider_keyword(tree: ast.AST, *, source_path: str) -> list[str]:
    errors: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        path = _attribute_path(node.func)
        if not path or "data" not in path:
            continue
        for keyword in node.keywords:
            if keyword.arg == "provider":
                errors.append(
                    f"{source_path}: do not pass provider=... to getagent.data calls "
                    f"(line {keyword.value.lineno}); the managed DataSDK provider is selected by the platform"
                )
    return errors


def _test_contains_follow_trade_guard(test: ast.AST) -> bool:
    if isinstance(test, ast.Call):
        return _attribute_path(test)[-2:] == ["runtime", "is_follow_trade"]
    if isinstance(test, ast.BoolOp) and isinstance(test.op, ast.And):
        return any(_test_contains_follow_trade_guard(value) for value in test.values)
    if isinstance(test, ast.Compare):
        nodes = [test.left, *test.comparators]
        has_follow_trade = any(
            isinstance(node, ast.Constant) and node.value == "follow_trade"
            for node in nodes
        )
        has_positive_operator = any(isinstance(op, (ast.Eq, ast.In)) for op in test.ops)
        return has_follow_trade and has_positive_operator
    return False


def _call_is_runtime_follow_wrapper(node: ast.Call) -> bool:
    return _attribute_path(node.func)[-2:] == ["runtime", "emit_signal_or_follow"]


def _call_is_trade_mutation(node: ast.Call) -> bool:
    path = _attribute_path(node.func)
    return (
        len(path) >= 3
        and path[0] == "trade"
        and path[-2] in {"account", "contract", "spot"}
        and path[-1] in TRADE_MUTATION_METHODS
    )


def _check_live_trade_mutation_guards(
    tree: ast.AST, *, source_path: str, execution_mode: str = ""
) -> list[str]:
    """Require direct live trade mutations in run() to be follow-trade guarded.

    Grid Playbooks route mutations through the managed Strategy Bot callback and
    must never call trade.contract / trade.spot mutation methods directly.
    """
    if source_path not in {"src/main.py", "src/main_live.py"}:
        return []

    errors: list[str] = []
    _is_grid = execution_mode == "grid"

    def visit(node: ast.AST, *, inside_run: bool, guarded: bool) -> None:
        next_inside_run = inside_run
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            next_inside_run = node.name == "run"

        next_guarded = guarded
        if next_inside_run and isinstance(node, ast.If) and _test_contains_follow_trade_guard(node.test):
            next_guarded = True

        if next_inside_run and isinstance(node, ast.Call) and _call_is_trade_mutation(node) and not next_guarded:
            path = ".".join(_attribute_path(node.func))
            if _is_grid:
                errors.append(
                    f"{source_path}: {path}() is not allowed in grid Playbooks "
                    f"(line {node.lineno}); Grid execution permits only trade.grid "
                    "mutations inside runtime.execute_strategy_bot_action(...)"
                )
            else:
                errors.append(
                    f"{source_path}: {path}() in run() must be inside an "
                    "execution_mode == 'follow_trade' guard after emitting the signal; "
                    f"unguarded live trade mutations are not allowed (line {node.lineno})"
                )

        if next_inside_run and isinstance(node, ast.Call) and _call_is_runtime_follow_wrapper(node):
            execute_trade_keywords = {
                keyword
                for keyword in node.keywords
                if keyword.arg == "execute_trade"
            }
            execute_trade_child_ids = {
                child_id
                for keyword in execute_trade_keywords
                for child_id in (id(keyword), id(keyword.value))
            }
            for keyword in execute_trade_keywords:
                visit(keyword.value, inside_run=next_inside_run, guarded=True)
            for child in ast.iter_child_nodes(node):
                if id(child) not in execute_trade_child_ids:
                    visit(child, inside_run=next_inside_run, guarded=next_guarded)
            return

        for child in ast.iter_child_nodes(node):
            visit(child, inside_run=next_inside_run, guarded=next_guarded)

    visit(tree, inside_run=False, guarded=False)
    return errors


def _literal_str(node: ast.AST) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _dict_literal_value(node: ast.Dict, key: str) -> ast.AST | None:
    for key_node, value_node in zip(node.keys, node.values):
        if key_node is not None and _literal_str(key_node) == key:
            return value_node
    return None


def _check_progress_block_literal(
    block: ast.AST, *, source_path: str, errors: list[str]
) -> None:
    if not isinstance(block, ast.Dict):
        return  # dynamically built block; runtime validation applies
    type_node = _dict_literal_value(block, "type")
    if type_node is not None:
        block_type = _literal_str(type_node)
        if block_type is not None and block_type not in PROGRESS_BLOCK_TYPES:
            if block_type in LEGACY_PROGRESS_BLOCK_TYPES:
                errors.append(
                    f"{source_path}: emit_progress block type '{block_type}' was "
                    "removed on 2026-07-20 — merge its content into a 'content' "
                    f"block using markdown (line {block.lineno})"
                )
            else:
                errors.append(
                    f"{source_path}: emit_progress block type must be one of "
                    f"{sorted(PROGRESS_BLOCK_TYPES)}, got '{block_type}' (line {block.lineno})"
                )
    ctx_node = _dict_literal_value(block, "ctx")
    if ctx_node is not None and isinstance(ctx_node, (ast.List, ast.Dict)):
        errors.append(
            f"{source_path}: emit_progress block ctx must be a markdown string "
            "(span lists / table dicts were removed on 2026-07-20) "
            f"(line {block.lineno})"
        )


def _check_runtime_event_emits(tree: ast.AST, *, source_path: str) -> list[str]:
    """Statically validate literal arguments of emit_progress / emit_decision.

    Matches qualified ``runtime.emit_*`` calls only (same policy as
    ``_call_is_runtime_follow_wrapper``): bare-name calls could be user-defined
    helpers, and malformed payloads still fail fast at runtime in the SDK.
    """
    errors: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        tail = _attribute_path(node.func)[-2:]

        if tail == ["runtime", "emit_progress"]:
            blocks_node: ast.AST | None = node.args[0] if node.args else None
            if blocks_node is None:
                for keyword in node.keywords:
                    if keyword.arg == "blocks":
                        blocks_node = keyword.value
            if isinstance(blocks_node, ast.List):
                if not blocks_node.elts:
                    errors.append(
                        f"{source_path}: emit_progress requires at least one block "
                        f"(line {node.lineno})"
                    )
                if len(blocks_node.elts) > MAX_PROGRESS_BLOCKS_PER_CALL:
                    errors.append(
                        f"{source_path}: emit_progress accepts at most "
                        f"{MAX_PROGRESS_BLOCKS_PER_CALL} blocks per call "
                        f"(line {node.lineno})"
                    )
                for block in blocks_node.elts:
                    _check_progress_block_literal(
                        block, source_path=source_path, errors=errors
                    )

        elif tail == ["runtime", "emit_decision"]:
            action_node: ast.AST | None = node.args[0] if node.args else None
            for keyword in node.keywords:
                if keyword.arg == "action" and action_node is None:
                    action_node = keyword.value
            action = _literal_str(action_node) if action_node is not None else None
            if action is not None and action not in DECISION_ACTIONS:
                errors.append(
                    f"{source_path}: emit_decision action must be one of "
                    f"{sorted(DECISION_ACTIONS)}, got '{action}' (line {node.lineno}); "
                    "open/close decision logs are derived by the platform, do not emit them"
                )
            for keyword in node.keywords:
                if keyword.arg != "sub_action":
                    continue
                sub_action = _literal_str(keyword.value)
                if sub_action is None:
                    continue
                if sub_action not in DECISION_WATCH_SUB_ACTIONS:
                    errors.append(
                        f"{source_path}: emit_decision sub_action must be one of "
                        f"{sorted(DECISION_WATCH_SUB_ACTIONS)}, got '{sub_action}' "
                        f"(line {node.lineno})"
                    )
                elif action is not None and action != "watch":
                    errors.append(
                        f"{source_path}: emit_decision sub_action is only allowed "
                        f"with action='watch' (line {node.lineno})"
                    )
    return errors


def _selection_basket_output_detected(source: str) -> bool:
    """Best-effort check that code emits a managed signal with basket metadata."""
    return (
        "basket" in source
        and (
            "emit_signal(" in source
            or "emit_signal_or_follow(" in source
        )
        and "meta" in source
    )


def _selection_basket_i18n_detected(source: str) -> bool:
    """Best-effort check that basket row text includes required i18n maps."""
    return (
        "thesis_i18n" in source
        and "risk_i18n" in source
        and all(repr(locale) in source or f'"{locale}"' in source for locale in REQUIRED_I18N_LOCALES)
    )


def _literal_string(node: ast.AST | None) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _check_selection_basket_name_fields(tree: ast.AST, *, source_path: str) -> list[str]:
    errors: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Dict):
            continue
        fields = {
            key_text: value
            for key, value in zip(node.keys, node.values)
            if (key_text := _literal_string(key))
        }
        if "name_i18n" in fields:
            errors.append(
                f"{source_path}: selection_basket picks must not emit name_i18n "
                f"(line {node.lineno}); keep asset/company names canonical and non-localized"
            )
        name_text = _literal_string(fields.get("name"))
        if name_text and CJK_TEXT_PATTERN.search(name_text):
            errors.append(
                f"{source_path}: selection_basket pick name must be canonical/non-localized "
                f"(line {node.lineno}); use an English/common name or the ticker, not {name_text!r}"
            )
    return errors


def _base_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    if isinstance(node, ast.Subscript):
        return _base_name(node.value)
    return ""


def _class_extends_strategy_config(node: ast.ClassDef) -> bool:
    return any(_base_name(base) == "StrategyConfig" for base in node.bases)


def _mutable_default_description(node: ast.AST | None) -> str:
    if isinstance(node, ast.List):
        return "list literal"
    if isinstance(node, ast.Dict):
        return "dict literal"
    if isinstance(node, ast.Set):
        return "set literal"
    if isinstance(node, ast.Call):
        name = _attribute_path(node.func)[-1:] or [""]
        if name[0] in {"list", "dict", "set"}:
            return f"{name[0]}() call"
    return ""


def _check_strategy_config_mutable_defaults(tree: ast.AST, *, source_path: str) -> list[str]:
    errors: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef) or not _class_extends_strategy_config(node):
            continue
        for statement in node.body:
            value: ast.AST | None = None
            target_name = ""
            if isinstance(statement, ast.AnnAssign):
                value = statement.value
                target_name = ".".join(_target_names(statement.target))
            elif isinstance(statement, ast.Assign):
                value = statement.value
                target_names = [
                    ".".join(_target_names(target))
                    for target in statement.targets
                ]
                target_name = ", ".join(name for name in target_names if name)
            description = _mutable_default_description(value)
            if description:
                errors.append(
                    f"{source_path}: StrategyConfig field {target_name or '<unknown>'} "
                    f"uses mutable default {description} (line {statement.lineno}); "
                    "use tuple, None, scalar defaults, or a default_factory pattern"
                )
    return errors


def validate_src_tree(
    pkg_dir: Path,
    result: ValidationResult,
    *,
    manifest: dict[str, object],
) -> None:
    src_root = pkg_dir / "src"
    if not src_root.exists():
        return

    local_import_roots = _local_import_roots(pkg_dir)
    exec_mode = str(manifest.get("execution_mode", "") or "").strip()
    is_selection_basket = (manifest.get("output_kind") or "trade_strategy") == "selection_basket"
    selection_basket_output_found = False
    selection_basket_i18n_found = False
    grid_wrapper_count = 0
    for path in src_root.rglob("*.py"):
        rel_path = path.relative_to(pkg_dir).as_posix()
        source = path.read_text()
        selection_basket_output_found = (
            selection_basket_output_found or _selection_basket_output_detected(source)
        )
        selection_basket_i18n_found = (
            selection_basket_i18n_found or _selection_basket_i18n_detected(source)
        )

        try:
            tree = ast.parse(source, filename=rel_path)
        except SyntaxError as e:
            result.error(f"{rel_path}: syntax error at line {e.lineno}: {e.msg}")
            continue

        for error in _check_position_selection_attributes(tree, source_path=rel_path):
            result.error(error)
        for error in _check_contract_trigger_price_rounding(tree, source_path=rel_path):
            result.error(error)
        for error in _check_contract_tpsl_helper_call(tree, source_path=rel_path):
            result.error(error)
        for error in _check_data_provider_keyword(tree, source_path=rel_path):
            result.error(error)
        if exec_mode == "grid":
            grid_errors, wrapper_count = _check_grid_orchestration(
                tree,
                source_path=rel_path,
            )
            grid_wrapper_count += wrapper_count
            for error in grid_errors:
                result.error(error)
        else:
            for error in _check_live_trade_mutation_guards(
                tree,
                source_path=rel_path,
                execution_mode=exec_mode,
            ):
                result.error(error)
        for error in _check_strategy_config_mutable_defaults(tree, source_path=rel_path):
            result.error(error)
        for error in _check_runtime_event_emits(tree, source_path=rel_path):
            result.error(error)
        if is_selection_basket:
            for error in _check_selection_basket_name_fields(tree, source_path=rel_path):
                result.error(error)

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    top = alias.name.split(".")[0]
                    if top in BLOCKED_IMPORTS:
                        result.error(f"{rel_path}: blocked import '{alias.name}' (line {node.lineno})")
                    elif top not in ALLOWED_IMPORTS and top not in local_import_roots:
                        result.error(f"{rel_path}: disallowed import '{alias.name}' (line {node.lineno})")

            elif isinstance(node, ast.ImportFrom):
                if node.level > 0:
                    continue
                if node.module:
                    top = node.module.split(".")[0]
                    if top in BLOCKED_IMPORTS:
                        result.error(f"{rel_path}: blocked import from '{node.module}' (line {node.lineno})")
                    elif top not in ALLOWED_IMPORTS and top not in local_import_roots:
                        result.error(f"{rel_path}: disallowed import from '{node.module}' (line {node.lineno})")

            elif isinstance(node, ast.Call):
                func = node.func
                name = ""
                if isinstance(func, ast.Name):
                    name = func.id
                elif isinstance(func, ast.Attribute):
                    name = func.attr

                if name in ("__import__", "import_module"):
                    result.error(f"{rel_path}: dynamic import via {name}() is not allowed (line {node.lineno})")
                if name in ("eval", "exec", "compile"):
                    result.error(f"{rel_path}: {name}() is not allowed (line {node.lineno})")
                if (
                    name in NAUTILUS_INSTRUMENT_REQUIRED_METHODS
                    and isinstance(func, ast.Attribute)
                    and isinstance(func.value, ast.Name)
                    and func.value.id == "self"
                    and not node.args
                    and not node.keywords
                ):
                    result.error(
                        f"{rel_path}: Nautilus Strategy.{name}() requires an instrument_id "
                        f"argument in this runner; call self.{name}(instrument_id) (line {node.lineno})"
                    )

            elif isinstance(node, ast.Name) and node.id == "__builtins__":
                result.error(f"{rel_path}: access to __builtins__ is not allowed (line {node.lineno})")

            elif isinstance(node, ast.Attribute) and node.attr in (
                "__import__", "__builtins__", "__subclasses__",
                "__globals__", "__code__", "__closure__",
            ):
                result.error(f"{rel_path}: access to {node.attr} is not allowed (line {node.lineno})")

    if is_selection_basket:
        if not selection_basket_output_found:
            result.error(
                "src/**: output_kind=selection_basket requires emitting "
                "runtime.emit_signal(..., meta={'basket': [...]})"
            )
        if not selection_basket_i18n_found:
            result.error(
                "src/**: output_kind=selection_basket requires basket rows to include "
                "thesis_i18n and risk_i18n for locales "
                f"{list(REQUIRED_I18N_LOCALES)}"
            )
    if exec_mode == "grid" and grid_wrapper_count == 0:
        result.error(
            "src/**: execution_mode=grid requires "
            "runtime.execute_strategy_bot_action(...) for Grid lifecycle actions"
        )


def validate_package(pkg_dir: Path) -> ValidationResult:
    result = ValidationResult()
    validate_structure(pkg_dir, result)
    manifest = validate_manifest(pkg_dir, result)
    validate_backtest_yaml(pkg_dir, manifest, result)
    validate_src_tree(pkg_dir, result, manifest=manifest)
    return result


def main() -> None:
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <package-directory>")
        sys.exit(1)

    pkg_dir = Path(sys.argv[1]).resolve()
    if not pkg_dir.is_dir():
        print(f"Error: {pkg_dir} is not a directory")
        sys.exit(1)

    print(f"Validating: {pkg_dir.name}/")
    print()

    result = validate_package(pkg_dir)

    if result.warnings:
        for w in result.warnings:
            print(f"  WARN  {w}")
        print()

    if result.errors:
        for e in result.errors:
            print(f"  FAIL  {e}")
        print()
        print(f"Validation FAILED — {len(result.errors)} error(s)")
        report_validation(
            passed=False,
            errors=len(result.errors),
            warnings=len(result.warnings),
        )
        sys.exit(1)

    print("Validation PASSED")
    report_validation(passed=True, errors=0, warnings=len(result.warnings))


if __name__ == "__main__":
    main()
