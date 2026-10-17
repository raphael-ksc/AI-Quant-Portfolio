"""回測層：Backtrader 包裝、美股交易成本、績效指標。

用法：
    from quantlib.backtest import BacktestConfig, run_backtest
    result = run_backtest(StrategyCls, bars, trade_start=date(2025, 1, 2), symbol='PLTR')
    result.metrics()
"""
from .costs import CostBreakdown, USEquityCosts
from .engine import BacktestConfig, BacktestResult, run_backtest, to_feed_frame
from .metrics import max_drawdown, nav_metrics, trade_metrics

__all__ = [
    'BacktestConfig', 'BacktestResult', 'CostBreakdown', 'USEquityCosts', 'max_drawdown',
    'nav_metrics', 'run_backtest', 'to_feed_frame', 'trade_metrics',
]
