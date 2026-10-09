"""Package entry. Historical and live runs share one manifest."""

from getagent import runtime

try:
    from . import main_backtest, main_live
except ImportError:
    import main_backtest
    import main_live


def run() -> None:
    if runtime.is_historical():
        main_backtest.run()
        return
    if runtime.is_live():
        main_live.run()
        return
    raise ValueError(f"unsupported evaluation_mode={runtime.evaluation_mode!r}")


if __name__ == "__main__":
    run()
