"""MACD 金叉死叉（趨勢跟蹤）：課程 CASE 2-MACD策略.py，參數照課程預設。"""
import backtrader as bt

STRATEGY_META = {
    'name': 'MACD', 'name_en': 'MACD Crossover',
    'category': 'trend',
    'desc': 'MACD 線上穿訊號線買進，下穿賣出',
    'params': {'short': 12, 'long': 26, 'signal': 9},
    'logic': 'MACD(12, 26, 9) 金叉 → 買進；死叉 → 平倉',
}


class Strategy(bt.Strategy):
    params = (('short', 12), ('long', 26), ('signal', 9))

    def __init__(self):
        macd = bt.indicators.MACD(self.data.close, period_me1=self.p.short,
                                  period_me2=self.p.long, period_signal=self.p.signal)
        self.crossover = bt.indicators.CrossOver(macd.macd, macd.signal)

    def next(self):
        if not self.position:
            if self.crossover > 0:
                self.buy()
        elif self.crossover < 0:
            self.close()
