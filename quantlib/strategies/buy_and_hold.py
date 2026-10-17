"""買入持有基準：評估期第一天收盤下單、隔天開盤買進，之後一直持有。

不屬於候選策略，registry 不會載入；回測時用來當每檔股票的比較基準。
"""
import backtrader as bt


class BuyAndHold(bt.Strategy):
    def next(self):
        if not self.position:
            self.buy()
