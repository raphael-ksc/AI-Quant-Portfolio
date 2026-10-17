"""quantlib.db 單元測試：不需要 MySQL、OpenD 與網路（CI 每次都跑）。"""
import datetime as dt
import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from quantlib.data import DataSourceError, get_symbol  # noqa: E402
from quantlib.data.base import DataSource  # noqa: E402
from quantlib.db import (  # noqa: E402
    DbConfig, DbConfigError, bars_to_rows, ingest_daily, last_closed_session, needs_refresh,
    plan_fetch, split_sql,
)
from quantlib.db.planner import trim_unclosed  # noqa: E402
from quantlib.db.repository import SCHEMA_FILE  # noqa: E402

ET = dt.timezone(dt.timedelta(hours=-4))  # 美東夏令時間（EDT）
PLTR, IREN = get_symbol('PLTR'), get_symbol('IREN')


def bars(dates, close=100.0, symbol='PLTR', adjust='qfq', source='yfinance'):
    closes = close if isinstance(close, list) else [close] * len(dates)
    return pd.DataFrame({
        'symbol': symbol, 'date': pd.to_datetime(dates),
        'open': closes, 'high': [c + 1 for c in closes], 'low': [c - 1 for c in closes],
        'close': closes, 'volume': 1000.0, 'adjust': adjust, 'currency': 'USD', 'source': source,
    })


# ======================= 最後已收盤交易日 =======================

@pytest.mark.parametrize('now, expected', [
    (dt.datetime(2026, 10, 16, 12, 0, tzinfo=ET), dt.date(2026, 10, 15)),   # 週五盤中 → 週四
    (dt.datetime(2026, 10, 16, 16, 10, tzinfo=ET), dt.date(2026, 10, 15)),  # 收盤後 10 分鐘，未過緩衝
    (dt.datetime(2026, 10, 16, 16, 45, tzinfo=ET), dt.date(2026, 10, 16)),  # 收盤後 45 分鐘 → 當天
    (dt.datetime(2026, 10, 17, 10, 0, tzinfo=ET), dt.date(2026, 10, 16)),   # 週六 → 週五
    (dt.datetime(2026, 10, 19, 9, 0, tzinfo=ET), dt.date(2026, 10, 16)),    # 週一開盤前 → 上週五
])
def test_last_closed_session(now, expected):
    assert last_closed_session(now) == expected


def test_last_closed_session_from_taipei_time():
    # 台北 2026-10-17 05:00 = 美東 10-16 17:00（已收盤）；台北日期已跨到隔天
    taipei = dt.datetime(2026, 10, 17, 5, 0, tzinfo=dt.timezone(dt.timedelta(hours=8)))
    assert last_closed_session(taipei) == dt.date(2026, 10, 16)


def test_last_closed_session_requires_timezone():
    with pytest.raises(ValueError):
        last_closed_session(dt.datetime(2026, 10, 16, 12, 0))


# ======================= 增量規劃 =======================

SESSION = dt.date(2026, 10, 16)


def test_plan_without_history_is_full():
    plan = plan_fetch('PLTR', 'qfq', latest=None, overlap_start=None, last_session=SESSION)
    assert (plan.reason, plan.start, plan.end) == ('full', dt.date(2023, 1, 1), SESSION)


def test_plan_up_to_date_skips():
    plan = plan_fetch('PLTR', 'qfq', latest=SESSION, overlap_start=dt.date(2026, 10, 12), last_session=SESSION)
    assert plan.skip


def test_plan_incremental_starts_at_overlap():
    plan = plan_fetch('PLTR', 'qfq', latest=dt.date(2026, 10, 10), overlap_start=dt.date(2026, 10, 6),
                      last_session=SESSION)
    assert (plan.reason, plan.start, plan.end) == ('incremental', dt.date(2026, 10, 6), SESSION)


def test_plan_full_mode_ignores_history():
    plan = plan_fetch('PLTR', 'qfq', latest=SESSION, overlap_start=SESSION, last_session=SESSION, mode='full')
    assert plan.reason == 'full'


def test_plan_rejects_unknown_mode():
    with pytest.raises(ValueError):
        plan_fetch('PLTR', 'qfq', latest=None, overlap_start=None, last_session=SESSION, mode='daily')


# ======================= 復權基準比對 =======================

def test_needs_refresh_detects_changed_close():
    stored = bars(['2026-10-12', '2026-10-13'], [100.0, 101.0])
    fetched = bars(['2026-10-12', '2026-10-13', '2026-10-14'], [50.0, 50.5, 51.0])  # 1 拆 2 後整段減半
    assert needs_refresh(stored, fetched) == [pd.Timestamp('2026-10-12'), pd.Timestamp('2026-10-13')]


def test_needs_refresh_ignores_rounding_and_non_overlap():
    stored = bars(['2026-10-12'], [100.123456])
    fetched = bars(['2026-10-12', '2026-10-13'], [100.1234561, 999.0])
    assert needs_refresh(stored, fetched) == []
    assert needs_refresh(stored.iloc[0:0], fetched) == []


def test_trim_unclosed_drops_today():
    df = bars(['2026-10-15', '2026-10-16'])
    assert trim_unclosed(df, dt.date(2026, 10, 15))['date'].dt.date.tolist() == [dt.date(2026, 10, 15)]


# ======================= 寫入資料列 =======================

def test_bars_to_rows_rounds_and_maps_nan_to_null():
    df = bars(['2026-10-16'], [12.3456789])
    df['amount'], df['turnover_rate'] = [float('nan')], [0.011523456789]
    (row,) = bars_to_rows(df, run_id=7)
    assert row[:4] == ('PLTR', dt.date(2026, 10, 16), 'qfq', 'yfinance')
    assert row[7] == 12.345679           # close 四捨五入到 6 位
    assert row[9] is None                # amount NaN → NULL
    assert row[10] == 0.01152346         # turnover_rate 8 位
    assert row[-1] == 7


def test_bars_to_rows_without_optional_columns():
    (row,) = bars_to_rows(bars(['2026-10-16']), run_id=None)
    assert row[9] is None and row[10] is None


def test_split_sql_on_repo_schema():
    statements = split_sql(SCHEMA_FILE.read_text(encoding='utf-8'))
    heads = [s.split('(')[0].split('\n')[0].strip() for s in statements]
    assert heads == ['CREATE TABLE IF NOT EXISTS instruments', 'CREATE TABLE IF NOT EXISTS ingest_runs',
                     'CREATE TABLE IF NOT EXISTS market_daily', 'CREATE OR REPLACE VIEW trade_stock_daily AS',
                     'CREATE TABLE IF NOT EXISTS financial_items', 'CREATE TABLE IF NOT EXISTS financial_revisions',
                     'CREATE TABLE IF NOT EXISTS financial_metrics', 'CREATE OR REPLACE VIEW trade_stock_financial AS']
    assert all('--' not in s for s in statements)


# ======================= 連線設定 =======================

ENV = {'MYSQL_HOST': '127.0.0.1', 'MYSQL_PORT': '3307', 'MYSQL_USER': 'quant_app',
       'MYSQL_PASSWORD': 'not-a-real-pw', 'MYSQL_DATABASE': 'quant_portfolio'}


def test_db_config_from_env_hides_password():
    cfg = DbConfig.from_env(ENV)
    assert cfg.port == 3307 and cfg.describe() == 'quant_app@127.0.0.1:3307/quant_portfolio'
    assert 'not-a-real-pw' not in repr(cfg) and 'not-a-real-pw' not in cfg.describe()


def test_db_config_missing_keys_listed_without_values():
    with pytest.raises(DbConfigError) as e:
        DbConfig.from_env({**ENV, 'MYSQL_USER': '', 'MYSQL_PASSWORD': ' '})
    assert 'MYSQL_USER' in str(e.value) and 'MYSQL_PASSWORD' in str(e.value)


def test_db_config_bad_port():
    with pytest.raises(DbConfigError):
        DbConfig.from_env({**ENV, 'MYSQL_PORT': 'abc'})


def test_db_config_database_override():
    assert DbConfig.from_env(ENV, database='quant_portfolio_test').database == 'quant_portfolio_test'


# ======================= 寫入流程（假的資料源與資料庫） =======================

class FakeSource(DataSource):
    name = 'yfinance'

    def __init__(self, history: dict[str, pd.DataFrame], fail: set[str] = frozenset()):
        self.history, self.fail, self.calls = history, fail, []

    def get_daily_bars(self, symbol, start, end, adjust='qfq'):
        self.calls.append((symbol.ticker, start, end, adjust))
        if symbol.ticker in self.fail:
            raise DataSourceError('模擬 API 失敗')
        df = self.history[symbol.ticker]
        d = df['date'].dt.date
        return df[(d >= start) & (d <= end)].assign(adjust=adjust, symbol=symbol.ticker).reset_index(drop=True)

    def get_minute_bars(self, symbol, day):  # pragma: no cover
        raise NotImplementedError

    def get_financials(self, symbol, freq='Q', periods=8):  # pragma: no cover
        raise NotImplementedError


class FakeRepo:
    """記憶體版 MySQLRepository：key = (symbol, source, adjust) → {date: close}。"""

    def __init__(self):
        self.data, self.runs, self.instruments = {}, {}, []

    def upsert_instruments(self, symbols):
        self.instruments = [s.ticker for s in symbols]

    def start_run(self, job, source, mode, symbols):
        run_id = len(self.runs) + 1
        self.runs[run_id] = {'status': 'running'}
        return run_id

    def finish_run(self, run_id, status, rows_written, message=None):
        self.runs[run_id] = {'status': status, 'rows': rows_written, 'message': message}

    def latest_dates(self, source, adjust, n):
        out = {}
        for (sym, src, adj), rows in self.data.items():
            if src == source and adj == adjust and rows:
                dates = sorted(rows, reverse=True)[:n]
                out[sym] = (dates[0], dates[-1])
        return out

    def load_closes(self, symbol, source, adjust, start):
        rows = self.data.get((symbol, source, adjust), {})
        keep = sorted(d for d in rows if d >= start)
        return pd.DataFrame({'date': pd.to_datetime(keep), 'close': [rows[d] for d in keep]})

    def earliest_date(self, symbol, source, adjust):
        rows = self.data.get((symbol, source, adjust), {})
        return min(rows) if rows else None

    def upsert_bars(self, df, run_id, *, replace=False):
        for (sym, src, adj), g in df.groupby(['symbol', 'source', 'adjust']):
            store = {} if replace else self.data.get((sym, src, adj), {})
            store.update(dict(zip(g['date'].dt.date, g['close'])))
            self.data[(sym, src, adj)] = store
        return len(df)


WEEKDAYS = pd.bdate_range('2026-10-05', '2026-10-16')  # 10 個交易日
NOW = dt.datetime(2026, 10, 16, 17, 0, tzinfo=ET)        # 週五收盤後


def test_ingest_full_then_incremental_is_idempotent():
    src = FakeSource({'PLTR': bars(WEEKDAYS, 100.0)})
    repo = FakeRepo()
    first = ingest_daily(repo, src, [PLTR], adjusts=('qfq',), now=NOW, default_start=dt.date(2026, 10, 1))
    assert first['status'] == 'success' and first['results'][0].reason == 'full'
    assert len(repo.data[('PLTR', 'yfinance', 'qfq')]) == 10

    second = ingest_daily(repo, src, [PLTR], adjusts=('qfq',), now=NOW, default_start=dt.date(2026, 10, 1))
    assert second['results'][0].reason == 'up_to_date' and second['rows_written'] == 0


def test_ingest_incremental_fetches_overlap_window():
    src = FakeSource({'PLTR': bars(WEEKDAYS, 100.0)})
    repo = FakeRepo()
    early = dt.datetime(2026, 10, 12, 17, 0, tzinfo=ET)   # 只寫到 10-12
    ingest_daily(repo, src, [PLTR], adjusts=('qfq',), now=early, default_start=dt.date(2026, 10, 1))
    summary = ingest_daily(repo, src, [PLTR], adjusts=('qfq',), now=NOW, lookback=3)
    r = summary['results'][0]
    assert r.reason == 'incremental' and r.start == '2026-10-08'  # 倒數第 3 個已存日
    assert max(repo.data[('PLTR', 'yfinance', 'qfq')]) == dt.date(2026, 10, 16)


def test_ingest_refreshes_whole_series_when_adjustment_changes():
    old = bars(WEEKDAYS, 100.0)
    src = FakeSource({'PLTR': old})
    repo = FakeRepo()
    ingest_daily(repo, src, [PLTR], adjusts=('qfq',), now=dt.datetime(2026, 10, 12, 17, 0, tzinfo=ET),
                 default_start=dt.date(2026, 10, 1))
    src.history['PLTR'] = bars(WEEKDAYS, 50.0)  # 1 拆 2：前復權歷史價格整段改變
    summary = ingest_daily(repo, src, [PLTR], adjusts=('qfq',), now=NOW, default_start=dt.date(2026, 10, 1))
    r = summary['results'][0]
    assert r.reason == 'refresh' and r.mismatched_dates
    assert set(repo.data[('PLTR', 'yfinance', 'qfq')].values()) == {50.0}  # 舊基準的價格全部被取代


def test_ingest_never_writes_unclosed_bar():
    src = FakeSource({'PLTR': bars(WEEKDAYS, 100.0)})
    repo = FakeRepo()
    intraday = dt.datetime(2026, 10, 16, 11, 0, tzinfo=ET)
    ingest_daily(repo, src, [PLTR], adjusts=('qfq',), now=intraday, default_start=dt.date(2026, 10, 1))
    assert max(repo.data[('PLTR', 'yfinance', 'qfq')]) == dt.date(2026, 10, 15)


def test_ingest_one_symbol_failure_is_partial():
    src = FakeSource({'PLTR': bars(WEEKDAYS, 100.0)}, fail={'IREN'})
    repo = FakeRepo()
    summary = ingest_daily(repo, src, [PLTR, IREN], adjusts=('qfq', 'none'), now=NOW,
                           default_start=dt.date(2026, 10, 1))
    assert summary['status'] == 'partial'
    assert {(r.symbol, r.reason) for r in summary['results']} == {('PLTR', 'full'), ('IREN', 'failed')}
    assert 'IREN/qfq' in repo.runs[summary['run_id']]['message']
    assert ('PLTR', 'yfinance', 'none') in repo.data  # 兩種復權各自寫入
