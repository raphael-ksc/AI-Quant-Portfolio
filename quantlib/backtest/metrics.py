"""績效指標：一律由每日淨值與已平倉交易自行計算，不依賴 Backtrader 的分析器。

課程（第 5 課 data_loader.py）也發現 Backtrader 的 DrawDown 在異常情況會回傳 > 100%，
所以改從淨值序列計算。本模組的計算方式與 QuantStats 相同（日報酬、252 個交易日年化），
並在 tests/test_backtest.py 交叉驗證。
"""
from __future__ import annotations

import math

import pandas as pd

TRADING_DAYS = 252


def max_drawdown(nav: pd.Series) -> float:
    """最大回撤（正數，例如 0.25 = 25%）。"""
    peak = nav.cummax()
    return float(((peak - nav) / peak).max()) if len(nav) else 0.0


def nav_metrics(nav: pd.Series, risk_free: float = 0.0) -> dict:
    """由每日淨值計算報酬、風險與風險調整後指標；risk_free 為年化無風險利率。"""
    rets = nav.pct_change().dropna()
    n = len(rets)
    total = float(nav.iloc[-1] / nav.iloc[0] - 1)
    cagr = (1 + total) ** (TRADING_DAYS / n) - 1 if n > 0 and total > -1 else float('nan')
    excess = rets - risk_free / TRADING_DAYS
    vol = float(rets.std(ddof=1) * math.sqrt(TRADING_DAYS)) if n > 1 else float('nan')
    sharpe = (float(excess.mean() / rets.std(ddof=1) * math.sqrt(TRADING_DAYS))
              if n > 1 and rets.std(ddof=1) > 0 else float('nan'))
    downside = math.sqrt((excess.clip(upper=0) ** 2).mean()) if n > 0 else 0.0
    sortino = float(excess.mean() / downside * math.sqrt(TRADING_DAYS)) if downside > 0 else float('nan')
    mdd = max_drawdown(nav)
    return {
        'total_return': total, 'cagr': cagr, 'volatility': vol, 'sharpe': sharpe, 'sortino': sortino,
        'max_drawdown': mdd, 'calmar': cagr / mdd if mdd > 0 else float('nan'), 'days': n,
    }


def trade_metrics(pnls: list[float]) -> dict:
    """已平倉交易的統計；pnls 為每筆交易扣除成本後的損益。"""
    wins = [p for p in pnls if p > 0]
    losses = [p for p in pnls if p <= 0]
    avg_win = sum(wins) / len(wins) if wins else 0.0
    avg_loss = sum(losses) / len(losses) if losses else 0.0
    gross_loss = abs(sum(losses))
    return {
        'trades': len(pnls),
        'win_rate': len(wins) / len(pnls) if pnls else float('nan'),
        'payoff_ratio': avg_win / abs(avg_loss) if avg_loss else float('nan'),
        'profit_factor': sum(wins) / gross_loss if gross_loss else float('nan'),
    }
