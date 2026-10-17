"""RSI 超買超賣（均值回歸）：課程 CASE 3-RSI策略.py，參數照課程預設。"""
import backtrader as bt

STRATEGY_META = {
    'name': 'RSI', 'name_en': 'RSI Mean Reversion',
    'category': 'mean_reversion',
    'desc': 'RSI 低於超賣線買進，高於超買線賣出',
    'params': {'period': 14, 'oversold': 30, 'overbought': 70},
    'logic': 'RSI(14) < 30 → 買進；RSI(14) > 70 → 平倉',
}


class Strategy(bt.Strategy):
    params = (('period', 14), ('oversold', 30), ('overbought', 70))

    def __init__(self):
        self.rsi = bt.indicators.RSI(self.data.close, period=self.p.period)

    def next(self):
        if not self.position:
            if self.rsi < self.p.oversold:
                self.buy()
        elif self.rsi > self.p.overbought:
            self.close()
