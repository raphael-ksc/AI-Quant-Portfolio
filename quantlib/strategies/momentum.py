"""動量（強者恆強）：課程 CASE 6-动量策略.py，參數照課程預設。"""
import backtrader as bt

STRATEGY_META = {
    'name': '動量', 'name_en': 'Momentum (ROC)',
    'category': 'trend',
    'desc': '20 日漲幅超過門檻買進，跌幅超過門檻賣出',
    'params': {'period': 20, 'threshold': 5.0},
    'logic': 'ROC(20) > +5% → 買進；ROC(20) < −5% → 平倉',
}


class Strategy(bt.Strategy):
    params = (('period', 20), ('threshold', 5.0))

    def __init__(self):
        self.roc = bt.indicators.ROC100(self.data.close, period=self.p.period)

    def next(self):
        if not self.position:
            if self.roc[0] > self.p.threshold:
                self.buy()
        elif self.roc[0] < -self.p.threshold:
            self.close()
