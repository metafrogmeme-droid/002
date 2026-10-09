"""Entry point: route historical replay vs live execution.

Historical runs use the managed Nautilus replay (src/main_backtest.py).
Live runs evaluate the same rules on fresh Bitget bars and route any order
through runtime.emit_signal_or_follow (src/main_live.py).
"""
from getagent import runtime


def run() -> None:
    if runtime.is_historical():
        from . import main_backtest

        main_backtest.run()
        return
    if runtime.is_live():
        from . import main_live

        main_live.run()
        return
    raise ValueError(f"unsupported evaluation_mode={runtime.evaluation_mode!r}")


if __name__ == "__main__":
    run()
