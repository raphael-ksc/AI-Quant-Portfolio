"""quantlib.backtest 與 quantlib.strategies 單元測試：用人造價格，不需要資料庫與網路。"""
import datetime as dt
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

bt = pytest.importorskip('backtrader')

from quantlib.backtest import (  # noqa: E402
    BacktestConfig, USEquityCosts, max_drawdown, nav_metrics, run_backtest, trade_metrics,
)
from quantlib.strategies import load_strategies  # noqa: E402
from quantlib.strategies.buy_and_hold import BuyAndHold  # noqa: E402

COSTS = USEquityCosts.from_config('moomoo_reference')
ZERO = BacktestConfig(slippage_bps=0.0, costs=USEquityCosts.from_config('zero_cost'))


def make_bars(close, start='2025-01-02', open_=None, volume=1e7):
    dates = pd.bdate_range(start, periods=len(close))
    close = np.asarray(close, dtype=float)
    open_ = close if open_ is None else np.asarray(open_, dtype=float)
    return pd.DataFrame({'date': dates, 'open': open_, 'high': np.maximum(open_, close) * 1.001,
                         'low': np.minimum(open_, close) * 0.999, 'close': close, 'volume': volume})


# ======================= 成本模型 =======================

def test_costs_buy_uses_minimums():
    c = COSTS.breakdown(10, 150.0, dt.date(2025, 3, 3), is_sell=False)
    assert (c.commission, c.platform, c.sec_fee, c.taf) == (0.99, 1.00, 0.0, 0.0)


def test_costs_per_share_above_minimum():
    c = COSTS.breakdown(1000, 20.0, dt.date(2025, 3, 3), is_sell=False)
    assert c.commission == pytest.approx(4.90) and c.platform == pytest.approx(5.00)


def test_costs_sell_regulatory_fees_follow_effective_dates():
    # 2025-03-03：SEC 每百萬 27.80 美元；TAF 0.000166/股
    early = COSTS.breakdown(100, 200.0, dt.date(2025, 3, 3), is_sell=True)
    assert early.sec_fee == pytest.approx(20_000 * 0.0000278)
    assert early.taf == pytest.approx(100 * 0.000166)
    # 2025-06-02：SEC 降為 0（2025-05-14 起），不收最低 0.01
    assert COSTS.breakdown(100, 200.0, dt.date(2025, 6, 2), is_sell=True).sec_fee == 0.0
    # 2026-05-01：SEC 每百萬 20.60；TAF 0.000195/股
    late = COSTS.breakdown(100, 200.0, dt.date(2026, 5, 1), is_sell=True)
    assert late.sec_fee == pytest.approx(20_000 * 0.0000206)
    assert late.taf == pytest.approx(100 * 0.000195)


def test_costs_sec_minimum_and_taf_cap():
    tiny = COSTS.breakdown(1, 5.0, dt.date(2025, 3, 3), is_sell=True)
    assert tiny.sec_fee == 0.01
    huge = COSTS.breakdown(100_000, 10.0, dt.date(2026, 5, 1), is_sell=True)
    assert huge.taf == 9.79


def test_zero_cost_profile_is_free():
    z = USEquityCosts.from_config('zero_cost').breakdown(100, 200.0, dt.date(2025, 3, 3), is_sell=True)
    assert z.total == 0.0


def test_costs_reject_dates_before_schedule():
    with pytest.raises(ValueError):
        COSTS.breakdown(1, 1.0, dt.date(2020, 1, 2), is_sell=True)


# ======================= 績效指標 =======================

def test_max_drawdown_known_path():
    assert max_drawdown(pd.Series([100, 120, 90, 130, 104])) == pytest.approx(0.25)


def test_nav_metrics_known_values():
    nav = pd.Series([100.0, 110.0, 99.0, 108.9])
    m = nav_metrics(nav)
    rets = np.array([0.10, -0.10, 0.10])
    assert m['total_return'] == pytest.approx(0.089)
    assert m['sharpe'] == pytest.approx(rets.mean() / rets.std(ddof=1) * math.sqrt(252))
    assert m['max_drawdown'] == pytest.approx(0.10)
    assert m['cagr'] == pytest.approx(1.089 ** (252 / 3) - 1)


def test_trade_metrics():
    m = trade_metrics([100.0, -50.0, 200.0, -50.0])
    assert m['win_rate'] == 0.5 and m['payoff_ratio'] == pytest.approx(3.0)
    assert m['profit_factor'] == pytest.approx(3.0)


def test_metrics_match_quantstats():
    qs = pytest.importorskip('quantstats')
    rets = pd.Series(np.random.default_rng(7).normal(0.0006, 0.015, 250),
                     index=pd.bdate_range('2025-01-02', periods=250))
    nav = pd.concat([pd.Series([1.0], index=[rets.index[0] - pd.offsets.BDay()]), (1 + rets).cumprod()])
    m = nav_metrics(nav)
    assert m['sharpe'] == pytest.approx(qs.stats.sharpe(rets), rel=1e-6)
    assert m['sortino'] == pytest.approx(qs.stats.sortino(rets), rel=1e-6)
    assert m['max_drawdown'] == pytest.approx(-qs.stats.max_drawdown(rets), rel=1e-6)


# ======================= 引擎：成交時點與前視偏差 =======================

def test_signal_fills_at_next_open_not_same_close():
    """第 1 天收盤下單；第 2 天跳空高開 4%。若用當天收盤成交會撿到便宜，正確做法是用隔天開盤價。"""
    close = [100, 104, 104, 104, 104]
    open_ = [100, 104, 104, 104, 104]
    r = run_backtest(BuyAndHold, make_bars(close, open_=open_), dt.date(2025, 1, 2), config=ZERO)
    first = r.trades.iloc[0]
    assert first['date'] == dt.date(2025, 1, 3) and first['price'] == pytest.approx(104.0)


def test_slippage_applied_to_open_fill():
    cfg = BacktestConfig(slippage_bps=10.0, costs=USEquityCosts.from_config('zero_cost'))
    r = run_backtest(BuyAndHold, make_bars([100.0] * 5), dt.date(2025, 1, 2), config=cfg)
    assert r.trades.iloc[0]['price'] == pytest.approx(100.0 * 1.001, rel=1e-6)


def test_whole_shares_and_costs_charged():
    r = run_backtest(BuyAndHold, make_bars([100.0] * 5), dt.date(2025, 1, 2),
                     config=BacktestConfig(slippage_bps=0.0, costs=COSTS))
    fill = r.trades.iloc[0]
    assert fill['size'] == 95 and float(fill['size']).is_integer()   # 10,000 × 95% ÷ 100
    assert fill['cost'] == pytest.approx(0.99 + 1.00)


def test_volume_cap_limits_fill():
    # 成交量 500 × 10% = 每天最多 50 股：95 股分兩天成交（01-03 成交 50、01-06 補 45 才完成）
    r = run_backtest(BuyAndHold, make_bars([100.0] * 5, volume=500), dt.date(2025, 1, 2), config=ZERO)
    done = r.trades.iloc[0]
    assert done['size'] == 95 and done['date'] == dt.date(2025, 1, 6)


def test_gap_up_beyond_cash_buffer_is_rejected():
    # 95% 倉位只留 5% 緩衝：隔天跳空 +10% 時資金不夠，委託被拒
    close = [100, 100, 110, 110, 110]
    r = run_backtest(BuyAndHold, make_bars(close, open_=[100, 110, 110, 110, 110]),
                     dt.date(2025, 1, 2), config=ZERO)
    assert r.rejected_orders >= 1


def test_warmup_period_never_trades_and_nav_starts_at_trade_start():
    bars = make_bars(np.linspace(100, 150, 60), start='2024-11-01')
    r = run_backtest(BuyAndHold, bars, dt.date(2025, 1, 2), config=ZERO)
    assert r.start == dt.date(2025, 1, 2)
    assert r.trades['date'].min() > dt.date(2025, 1, 2)
    assert r.nav.iloc[0] == pytest.approx(10_000.0)


def test_backtest_is_deterministic():
    px = 100 * np.exp(np.cumsum(np.random.default_rng(3).normal(0, 0.02, 300)))
    bars = make_bars(px, start='2024-01-02')
    spec = load_strategies()['macd']
    a = run_backtest(spec.cls, bars, dt.date(2025, 1, 2))
    b = run_backtest(spec.cls, bars, dt.date(2025, 1, 2))
    pd.testing.assert_series_equal(a.nav, b.nav)


# ======================= 策略外掛 =======================

def test_registry_loads_six_course_strategies():
    specs = load_strategies()
    assert list(specs) == ['bollinger', 'double_ma', 'macd', 'macd_divergence', 'momentum', 'rsi']
    for s in specs.values():
        assert {'name', 'name_en', 'category', 'desc', 'params', 'logic'} <= set(s.meta)


def _fill_dates(key, close, start='2025-01-02'):
    r = run_backtest(load_strategies()[key].cls, make_bars(close, start=start), dt.date(2025, 1, 2), config=ZERO)
    return r.trades


def test_double_ma_buys_after_golden_cross():
    close = [140 - i for i in range(40)] + [101 + 2 * i for i in range(30)]  # 先跌 40 天再漲 → 短均線上穿
    trades = _fill_dates('double_ma', close)
    assert trades.iloc[0]['side'] == 'BUY'
    assert trades.iloc[0]['date'] > pd.bdate_range('2025-01-02', periods=41)[-1].date()


def test_rsi_buys_when_oversold_and_sells_when_overbought():
    wiggle = [100 + (1 if i % 2 else -1) for i in range(20)]  # 小幅震盪（完全平盤時 RSI 會除以 0）
    close = wiggle + [100 - 2 * i for i in range(1, 11)] + [80 + 3 * i for i in range(1, 16)]
    trades = _fill_dates('rsi', close)
    assert list(trades['side'][:2]) == ['BUY', 'SELL']


def test_momentum_needs_threshold():
    assert _fill_dates('momentum', [100.0] * 60).empty                  # 平盤不交易
    assert not _fill_dates('momentum', np.linspace(100, 160, 60)).empty   # 20 日漲幅 > 5%
