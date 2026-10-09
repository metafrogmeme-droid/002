"""Sandbox entry point. Routes by injected evaluation mode; shared indicator
math lives in features.py, historical replay in main_backtest.py, live
follow-trade in main_live.py.
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
