"""布林帶（均值回歸）：課程 CASE 4-布林带策略.py，參數照課程預設。"""
import backtrader as bt

STRATEGY_META = {
    'name': '布林帶', 'name_en': 'Bollinger Bands',
    'category': 'mean_reversion',
    'desc': '收盤跌破下軌買進，突破上軌賣出',
    'params': {'period': 20, 'devfactor': 2.0},
    'logic': '收盤 < 下軌(20, 2σ) → 買進；收盤 > 上軌 → 平倉',
}


class Strategy(bt.Strategy):
    params = (('period', 20), ('devfactor', 2.0))

    def __init__(self):
        self.boll = bt.indicators.BollingerBands(self.data.close, period=self.p.period,
                                                 devfactor=self.p.devfactor)

    def next(self):
        if not self.position:
            if self.data.close[0] < self.boll.bot[0]:
                self.buy()
        elif self.data.close[0] > self.boll.top[0]:
            self.close()
