"""Entry point: historical runs use the Nautilus replay, live runs use the guarded follow-trade cycle."""
from getagent import runtime

from . import main_backtest, main_live


def run() -> None:
    if runtime.is_historical():
        main_backtest.run()
    elif runtime.is_live():
        main_live.run()
    else:
        raise ValueError(f"unsupported evaluation_mode={runtime.evaluation_mode!r}")


if __name__ == "__main__":
    run()
