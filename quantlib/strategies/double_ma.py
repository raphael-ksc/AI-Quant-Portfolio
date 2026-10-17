"""雙均線（趨勢跟蹤）：課程 CASE 1-双均线策略.py，參數照課程預設。"""
import backtrader as bt

STRATEGY_META = {
    'name': '雙均線', 'name_en': 'Dual Moving Average',
    'category': 'trend',
    'desc': '短均線上穿長均線買進，下穿賣出',
    'params': {'fast': 10, 'slow': 30},
    'logic': 'SMA(10) 上穿 SMA(30) → 買進；下穿 → 平倉',
}


class Strategy(bt.Strategy):
    params = (('fast', 10), ('slow', 30))

    def __init__(self):
        fast = bt.indicators.SMA(self.data.close, period=self.p.fast)
        slow = bt.indicators.SMA(self.data.close, period=self.p.slow)
        self.crossover = bt.indicators.CrossOver(fast, slow)

    def next(self):
        if not self.position:
            if self.crossover > 0:
                self.buy()
        elif self.crossover < 0:
            self.close()
