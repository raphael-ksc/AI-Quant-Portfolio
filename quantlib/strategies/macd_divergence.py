"""MACD 底背離（反轉）：課程 CASE strategies/macd_divergence.py，參數與判斷式照課程。

注意（課程 p.56 已提到）：macd_lowest[0] 包含當天，而「MACD > 前低 × 0.8」在 MACD 為正值時
意義會反轉，屬於寬鬆型背離。為了忠實比較課程策略，這裡不修改判斷式，只在報告中說明。
"""
import backtrader as bt

STRATEGY_META = {
    'name': 'MACD 底背離', 'name_en': 'MACD Bullish Divergence',
    'category': 'reversal',
    'desc': '價格在 N 日低點附近、MACD 未創新低且金叉時買進，死叉賣出',
    'params': {'lookback': 30, 'fast': 12, 'slow': 26, 'signal': 9},
    'logic': '最低價 ≤ 30 日最低 × 1.01 且 MACD > 30 日 MACD 最低 × 0.8 且 MACD > 訊號線 → 買進；死叉 → 平倉',
}


class Strategy(bt.Strategy):
    params = (('lookback', 30), ('fast', 12), ('slow', 26), ('signal', 9))

    def __init__(self):
        self.macd = bt.indicators.MACD(self.data.close, period_me1=self.p.fast,
                                       period_me2=self.p.slow, period_signal=self.p.signal)
        self.price_lowest = bt.indicators.Lowest(self.data.low, period=self.p.lookback)
        self.macd_lowest = bt.indicators.Lowest(self.macd.macd, period=self.p.lookback)

    def next(self):
        if not self.position:
            at_price_low = self.data.low[0] <= self.price_lowest[0] * 1.01
            macd_higher = self.macd.macd[0] > self.macd_lowest[0] * 0.8
            golden_cross = self.macd.macd[0] > self.macd.signal[0]
            if at_price_low and macd_higher and golden_cross:
                self.buy()
        elif self.macd.macd[0] < self.macd.signal[0] and self.macd.macd[-1] >= self.macd.signal[-1]:
            self.close()
