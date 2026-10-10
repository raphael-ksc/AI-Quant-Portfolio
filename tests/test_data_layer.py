"""quantlib.data 單元測試：用假的 OpenD / yfinance 物件，不需網路與帳號。"""
import datetime as dt
import sys
from pathlib import Path
from types import SimpleNamespace

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from quantlib.data import (  # noqa: E402
    DataSourceError, DataUnavailableError, SchemaError, get_symbol, load_symbols,
    validate_bars, validate_financials,
)
from quantlib.data.moomoo_source import MoomooSource, period_end_from_timestamp  # noqa: E402
from quantlib.data.yfinance_source import YFinanceSource  # noqa: E402

PLTR = get_symbol('PLTR')


# ======================= 假的 moomoo 模組 =======================

class FakeFt:
    RET_OK, RET_ERROR = 0, -1
    KLType = SimpleNamespace(K_DAY='K_DAY', K_1M='K_1M')
    AuType = SimpleNamespace(QFQ='qfq', NONE='None')


def kline_page(times, base=100.0):
    return pd.DataFrame({
        'time_key': times,
        'open': base, 'high': base + 2, 'low': base - 2, 'close': base + 1, 'volume': 1000.0,
    })


class FakeCtx:
    """依序回傳預先排好的結果，並記錄每次呼叫的參數。"""

    def __init__(self, kline=None, financials=None):
        self.kline = list(kline or [])
        self.financials = list(financials or [])
        self.calls = []
        self.closed = False

    def request_history_kline(self, code, **kw):
        self.calls.append(('kline', code, kw))
        return self.kline.pop(0)

    def get_financials_statements(self, code, **kw):
        self.calls.append(('fin', code, kw))
        return self.financials.pop(0)

    def close(self):
        self.closed = True


def make_source(ctx):
    sleeps = []
    src = MoomooSource(ft_module=FakeFt, ctx=ctx, sleep=sleeps.append, clock=lambda: 0.0)
    return src, sleeps


def report(ts, items, period_text='2026/Q2', currency='USD'):
    return {'date_time': ts, 'date_time_str': 'ignored', 'period_text': period_text,
            'currency_code': currency, 'item_list': items}


# ======================= 期末日修正 =======================

@pytest.mark.parametrize('ts,expected', [
    (1782748800, dt.date(2026, 6, 30)),   # PLTR 2026/Q2，date_time_str 為 2026-06-29
    (1774886400, dt.date(2026, 3, 31)),   # PLTR 2026/Q1
    (1767110400, dt.date(2025, 12, 31)),  # PLTR 2025/Q4
    (1784995200, dt.date(2026, 7, 26)),   # NVDA 2027/Q2，SEC 期末日 2026-07-26
])
def test_period_end_from_timestamp(ts, expected):
    assert period_end_from_timestamp(ts) == expected


# ======================= Moomoo K 線 =======================

def test_daily_bars_follow_all_pages():
    ctx = FakeCtx(kline=[
        (0, kline_page(['2025-01-02 00:00:00', '2025-01-03 00:00:00']), 'page2'),
        (0, kline_page(['2025-01-06 00:00:00']), 'page3'),
        (0, kline_page(['2025-01-07 00:00:00']), None),
    ])
    src, _ = make_source(ctx)
    df = src.get_daily_bars(PLTR, dt.date(2025, 1, 1), dt.date(2025, 1, 31))
    assert len(df) == 4
    assert [c[2]['page_req_key'] for c in ctx.calls] == [None, 'page2', 'page3']
    assert all(c[2]['extended_time'] is False for c in ctx.calls)
    validate_bars(df, 'daily')


def test_rate_limit_retries_then_succeeds():
    ctx = FakeCtx(kline=[
        (-1, 'Request frequency too high', None),
        (-1, 'too many requests', None),
        (0, kline_page(['2025-01-02 00:00:00']), None),
    ])
    src, sleeps = make_source(ctx)
    df = src.get_daily_bars(PLTR, dt.date(2025, 1, 1), dt.date(2025, 1, 2))
    assert len(df) == 1
    assert sleeps.count(5.0) == 2  # 兩次頻率錯誤各等 5 秒


def test_non_rate_limit_error_raises_immediately():
    ctx = FakeCtx(kline=[(-1, 'no permission for this market', None)])
    src, _ = make_source(ctx)
    with pytest.raises(DataSourceError, match='no permission'):
        src.get_daily_bars(PLTR, dt.date(2025, 1, 1), dt.date(2025, 1, 2))


def test_throttle_spaces_calls():
    now = [0.0]
    sleeps = []
    ctx = FakeCtx(kline=[(0, kline_page(['2025-01-02 00:00:00']), 'p2'),
                         (0, kline_page(['2025-01-03 00:00:00']), None)])
    src = MoomooSource(ft_module=FakeFt, ctx=ctx, sleep=sleeps.append, clock=lambda: now[0])
    src.get_daily_bars(PLTR, dt.date(2025, 1, 1), dt.date(2025, 1, 3))
    assert sleeps and abs(sleeps[0] - 1.1) < 1e-9  # 第二次呼叫前補足 1.1 秒間隔


def test_minute_bars_regular_session_only_and_tz_aware():
    times = ['2026-02-06 09:30:00', '2026-02-06 09:31:00', '2026-02-06 16:00:00', '2026-02-06 16:01:00']
    ctx = FakeCtx(kline=[(0, kline_page(times), None)])
    src, _ = make_source(ctx)
    df = src.get_minute_bars(PLTR, dt.date(2026, 2, 6))
    assert df['ts'].dt.strftime('%H:%M').tolist() == ['09:31', '16:00']
    assert str(df['ts'].dt.tz) == 'America/New_York'
    validate_bars(df, 'minute')


def test_quota_parses_tuple_response():
    ctx = FakeCtx()
    ctx.get_history_kl_quota = lambda **kw: (0, (2, 98, []))
    src, _ = make_source(ctx)
    assert src.quota() == {'used': 2, 'remaining': 98}


def test_context_manager_closes_connection():
    ctx = FakeCtx()
    with MoomooSource(ft_module=FakeFt, ctx=ctx):
        pass
    assert ctx.closed


# ======================= Moomoo 財報 =======================

def test_financials_long_format_with_corrected_period_end():
    item = [{'field_id': 8017, 'display_name': 'Operating Profit', 'data': 10.0}]
    cf_item = [{'field_id': 8017, 'display_name': 'Net Income from Continuing Operations', 'data': 7.0}]
    ctx = FakeCtx(financials=[
        (0, {'report_list': [report(1782748800, item)], 'next_key': None}),
        (0, {'report_list': [report(1782748800, [{'field_id': 8001, 'display_name': 'Total Assets', 'data': 99.0}])],
             'next_key': None}),
        (0, {'report_list': [report(1782748800, cf_item)], 'next_key': None}),
    ])
    src, _ = make_source(ctx)
    df = validate_financials(src.get_financials(PLTR, periods=1))
    assert set(df['statement']) == {'income', 'balance', 'cashflow'}
    assert (df['period_end'] == pd.Timestamp('2026-06-30')).all()
    # 同一 field_id 8017 出現在兩張報表，必須都保留
    assert len(df[df['field_id'] == '8017']) == 2


def test_financials_follow_next_key():
    items = [{'field_id': 8001, 'display_name': 'Revenue', 'data': 1.0}]
    page1 = (0, {'report_list': [report(1782748800, items), report(1774886400, items)], 'next_key': 'k2'})
    page2 = (0, {'report_list': [report(1767110400, items)], 'next_key': ''})
    empty = (0, {'report_list': [report(1782748800, items)], 'next_key': None})
    ctx = FakeCtx(financials=[page1, page2, empty, empty])
    src, _ = make_source(ctx)
    df = src.get_financials(PLTR, periods=3)
    income = df[df['statement'] == 'income']
    assert len(income) == 3
    fin_calls = [c for c in ctx.calls if c[0] == 'fin']
    assert fin_calls[1][2]['next_key'] == 'k2'


# ======================= yfinance =======================

class FakeTicker:
    def __init__(self, recorder, history_df=None, statements=None):
        self.recorder = recorder
        self.history_df = history_df
        self.statements = statements or {}

    def history(self, **kw):
        self.recorder.append(kw)
        return self.history_df

    def _stmt(self, name, freq):
        return self.statements.get((name, freq), pd.DataFrame())

    def get_income_stmt(self, freq):
        return self._stmt('income', freq)

    def get_balance_sheet(self, freq):
        return self._stmt('balance', freq)

    def get_cashflow(self, freq):
        return self._stmt('cashflow', freq)


def fake_yf(**kw):
    recorder = []
    ticker = FakeTicker(recorder, **kw)
    return SimpleNamespace(Ticker=lambda code: ticker), recorder


def yf_history(index):
    return pd.DataFrame({'Open': 10.0, 'High': 12.0, 'Low': 9.0, 'Close': 11.0, 'Volume': 5.0}, index=index)


def test_yfinance_daily_end_is_inclusive():
    idx = pd.DatetimeIndex(['2025-12-30', '2025-12-31']).tz_localize('America/New_York')
    yf, rec = fake_yf(history_df=yf_history(idx))
    df = YFinanceSource(yf_module=yf).get_daily_bars(PLTR, dt.date(2025, 12, 30), dt.date(2025, 12, 31))
    assert rec[0]['end'] == '2026-01-01'  # yfinance 的 end 不含當天，需 +1 天
    assert df['date'].max() == pd.Timestamp('2025-12-31')
    validate_bars(df, 'daily')


def test_yfinance_minute_out_of_range():
    yf, _ = fake_yf()
    src = YFinanceSource(yf_module=yf, today=dt.date(2026, 10, 10))
    with pytest.raises(DataUnavailableError, match='7'):
        src.get_minute_bars(PLTR, dt.date(2026, 2, 6))


def test_yfinance_minute_converts_to_bar_end_time():
    idx = pd.DatetimeIndex(['2026-10-09 09:30', '2026-10-09 09:31']).tz_localize('America/New_York')
    yf, rec = fake_yf(history_df=yf_history(idx))
    src = YFinanceSource(yf_module=yf, today=dt.date(2026, 10, 10))
    df = src.get_minute_bars(PLTR, dt.date(2026, 10, 9))
    assert df['ts'].dt.strftime('%H:%M').tolist() == ['09:31', '09:32']
    assert rec[0]['prepost'] is False


def test_yfinance_empty_history_raises():
    yf, _ = fake_yf(history_df=pd.DataFrame())
    with pytest.raises(DataUnavailableError):
        YFinanceSource(yf_module=yf).get_daily_bars(PLTR, dt.date(2025, 1, 1), dt.date(2025, 1, 2))


def test_yfinance_financials_fallback_to_annual():
    annual = pd.DataFrame({pd.Timestamp('2025-12-31'): [100.0, None]}, index=['TotalRevenue', 'EBIT'])
    yf, _ = fake_yf(statements={('income', 'yearly'): annual})
    df = validate_financials(YFinanceSource(yf_module=yf).get_financials(PLTR, freq='Q'))
    assert set(df['freq']) == {'A'}
    assert df['field_id'].tolist() == ['TotalRevenue']  # 空值被略過


# ======================= 格式驗證 =======================

def good_daily():
    return pd.DataFrame({
        'symbol': 'PLTR', 'date': pd.to_datetime(['2025-01-02', '2025-01-03']),
        'open': 10.0, 'high': 12.0, 'low': 9.0, 'close': 11.0, 'volume': 100.0,
        'adjust': 'qfq', 'currency': 'USD', 'source': 'moomoo',
    })


def test_validate_bars_rejects_bad_high_low():
    df = good_daily()
    df.loc[0, 'high'] = 8.0
    with pytest.raises(SchemaError, match='high/low'):
        validate_bars(df)


def test_validate_bars_rejects_duplicates():
    df = pd.concat([good_daily(), good_daily().iloc[[0]]])
    with pytest.raises(SchemaError, match='重複'):
        validate_bars(df)


def test_validate_bars_rejects_mixed_currency():
    df = good_daily()
    df.loc[1, 'currency'] = 'AUD'
    with pytest.raises(SchemaError, match='幣別'):
        validate_bars(df)


def test_validate_minute_requires_timezone():
    df = good_daily().rename(columns={'date': 'ts'})
    with pytest.raises(SchemaError, match='時區'):
        validate_bars(df, 'minute')


def test_validate_financials_rejects_duplicate_key():
    row = {'symbol': 'PLTR', 'source': 'moomoo', 'statement': 'income', 'field_id': '8001', 'name': 'x',
           'period_end': pd.Timestamp('2026-06-30'), 'fiscal_period': '2026/Q2', 'freq': 'Q', 'value': 1.0,
           'currency': 'USD', 'announce_date': pd.NaT}
    with pytest.raises(SchemaError, match='重複'):
        validate_financials(pd.DataFrame([row, row]))


def test_symbols_config_loads():
    symbols = load_symbols()
    assert symbols['IREN'].code_for('moomoo') == 'US.IREN'
    assert 'BHP' not in symbols
    with pytest.raises(KeyError):
        get_symbol('XXXX')
