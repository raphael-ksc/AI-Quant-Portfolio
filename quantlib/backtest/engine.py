"""Backtrader 包裝：Cerebro 標準流程（第 5 課 SOP）+ 防前視偏差 + 美股成本。

成交規則：
- 策略在 t 日收盤後產生訊號，市價單在 t+1 日「開盤價」成交（Backtrader 預設，不開 cheat-on-close）
- 滑價以百分比套用在開盤成交價（slip_open=True）
- 單根 K 線最多成交當天成交量的 volume_cap（課程 1b 的 FixedBarPerc）
- 美股沒有 T+1 與漲跌停，課程 1b 的 A 股限制不適用

暖機期：資料從 warmup 起點餵入，讓 30 日均線、MACD 等指標先算好；
評估期（trade_start 起）之前一律不下單，淨值也只從 trade_start 開始記錄。
"""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field

import backtrader as bt
import pandas as pd

from .costs import USEquityCosts
from .metrics import nav_metrics, trade_metrics


@dataclass
class BacktestConfig:
    cash: float = 10_000.0          # 初始資金（美元）
    position_pct: float = 95.0      # 每次進場使用的資金比例（課程同為 95%）
    slippage_bps: float = 5.0       # 滑價（基點，1 bp = 0.01%）
    volume_cap: float = 0.10        # 單根 K 線最多成交當天成交量的 10%
    risk_free: float = 0.0          # 年化無風險利率（Sharpe／Sortino 用）
    costs: USEquityCosts = field(default_factory=USEquityCosts.from_config)


@dataclass
class BacktestResult:
    strategy: str
    symbol: str
    start: dt.date
    end: dt.date
    nav: pd.Series
    trades: pd.DataFrame            # 每筆成交：日期、方向、股數、價格、成本
    closed_pnls: list[float]
    rejected_orders: int
    total_costs: float
    exposure: float                 # 有持倉的交易日比例

    def metrics(self, risk_free: float = 0.0) -> dict:
        m = nav_metrics(self.nav, risk_free)
        m.update(trade_metrics(self.closed_pnls))
        m.update({'fills': len(self.trades), 'rejected_orders': self.rejected_orders,
                  'total_costs': self.total_costs, 'exposure': self.exposure,
                  'final_value': float(self.nav.iloc[-1])})
        return m


class _CommInfo(bt.CommInfoBase):
    """把 USEquityCosts 接到 Backtrader；成交日期由 engine 在 run 前注入。"""
    params = (('stocklike', True), ('commtype', bt.CommInfoBase.COMM_FIXED), ('percabs', True))

    def __init__(self, costs: USEquityCosts, date_fn):
        super().__init__()
        self.costs, self.date_fn = costs, date_fn

    def _getcommission(self, size, price, pseudoexec):
        return self.costs.breakdown(size, price, self.date_fn(), is_sell=size < 0).total


def _wrap(strategy_cls, trade_start: dt.date):
    """包一層：評估期前不下單，並記錄每日淨值、成交與被拒的委託。"""

    class Wrapped(strategy_cls):
        def __init__(self):
            super().__init__()
            self._nav, self._fills, self._closed, self._rejected, self._in_pos = [], [], [], 0, 0

        def notify_order(self, order):
            if order.status == order.Completed:
                self._fills.append({
                    'date': self.data.datetime.date(0), 'side': 'BUY' if order.isbuy() else 'SELL',
                    'size': abs(order.executed.size), 'price': order.executed.price,
                    'cost': order.executed.comm,
                })
            elif order.status in (order.Margin, order.Rejected):
                self._rejected += 1  # 例：跳空高開，95% 倉位的資金不夠買
            parent = getattr(super(), 'notify_order', None)
            if parent:
                parent(order)

        def notify_trade(self, trade):
            if trade.isclosed:
                self._closed.append(trade.pnlcomm)

        def _record(self) -> bool:
            today = self.data.datetime.date(0)
            if today < trade_start:
                return False  # 暖機期：指標照算，但不交易、不記淨值
            self._nav.append((today, self.broker.getvalue()))
            self._in_pos += 1 if self.position else 0
            return True

        def prenext(self):
            # 指標還沒算完（暖機不足）時 Backtrader 呼叫 prenext：照記淨值，但不交易
            self._record()

        def next(self):
            if self._record():
                super().next()

    Wrapped.__name__ = strategy_cls.__name__
    return Wrapped


def to_feed_frame(bars: pd.DataFrame) -> pd.DataFrame:
    """統一格式日線 → Backtrader PandasData 需要的 DatetimeIndex + OHLCV。"""
    df = bars[['date', 'open', 'high', 'low', 'close', 'volume']].copy()
    df['date'] = pd.to_datetime(df['date'])
    return df.set_index('date').sort_index().astype(float)


def run_backtest(strategy_cls, bars: pd.DataFrame, trade_start: dt.date, *, symbol: str = '',
                 config: BacktestConfig | None = None, **params) -> BacktestResult:
    """bars 須包含暖機期；trade_start 起才允許交易與計算績效。"""
    config = config or BacktestConfig()
    feed_df = to_feed_frame(bars)
    if not (feed_df.index.date >= trade_start).any():
        raise ValueError(f'資料沒有涵蓋評估期起點 {trade_start}')

    cerebro = bt.Cerebro(stdstats=False)
    data = bt.feeds.PandasData(dataname=feed_df)
    cerebro.adddata(data)
    cerebro.addstrategy(_wrap(strategy_cls, trade_start), **params)
    cerebro.broker.setcash(config.cash)
    cerebro.broker.addcommissioninfo(_CommInfo(config.costs, lambda: data.datetime.date(0)))
    cerebro.broker.set_slippage_perc(perc=config.slippage_bps / 10_000, slip_open=True,
                                     slip_match=True, slip_out=False)
    cerebro.broker.set_filler(bt.broker.fillers.FixedBarPerc(perc=config.volume_cap * 100))
    cerebro.addsizer(bt.sizers.PercentSizerInt, percents=config.position_pct)  # 整數股
    strat = cerebro.run()[0]

    nav = pd.Series({d: v for d, v in strat._nav}, name='nav')
    nav.index = pd.to_datetime(nav.index)
    trades = pd.DataFrame(strat._fills, columns=['date', 'side', 'size', 'price', 'cost'])
    return BacktestResult(
        strategy=strategy_cls.__name__, symbol=symbol, start=nav.index[0].date(), end=nav.index[-1].date(),
        nav=nav, trades=trades, closed_pnls=list(strat._closed), rejected_orders=strat._rejected,
        total_costs=float(trades['cost'].sum()) if len(trades) else 0.0,
        exposure=strat._in_pos / len(nav) if len(nav) else 0.0,
    )
