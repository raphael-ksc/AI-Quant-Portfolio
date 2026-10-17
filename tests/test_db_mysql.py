"""quantlib.db 整合測試：需要真的 MySQL。

只在設定 MYSQL_TEST_DATABASE（名稱必須以 _test 結尾）時執行，否則整個檔案略過；
測試會清空並重建該資料庫的資料表，絕不會連到正式資料庫 MYSQL_DATABASE。
"""
import datetime as dt
import os
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

pytest.importorskip('pymysql')
try:
    from dotenv import load_dotenv
    load_dotenv(ROOT / '.env')
except ImportError:  # CI 直接用環境變數
    pass

TEST_DB = os.getenv('MYSQL_TEST_DATABASE', '').strip()
pytestmark = [
    pytest.mark.mysql,
    pytest.mark.skipif(not TEST_DB, reason='未設定 MYSQL_TEST_DATABASE，略過 MySQL 整合測試'),
]

from quantlib.data import get_symbol  # noqa: E402
from quantlib.db import DbConfig, MySQLRepository  # noqa: E402


def bars(dates, close, adjust='qfq', source='moomoo', amount=1e6, turnover=0.0123):
    return pd.DataFrame({
        'symbol': 'PLTR', 'date': pd.to_datetime(dates), 'open': close, 'high': close + 1,
        'low': close - 1, 'close': close, 'volume': 1000.0, 'amount': amount,
        'turnover_rate': turnover, 'adjust': adjust, 'currency': 'USD', 'source': source,
    })


@pytest.fixture()
def repo():
    if not TEST_DB.endswith('_test') or TEST_DB == os.getenv('MYSQL_DATABASE'):
        pytest.fail(f'MYSQL_TEST_DATABASE 必須以 _test 結尾且不同於正式資料庫：{TEST_DB}')
    cfg = DbConfig.from_env(dict(os.environ), database=TEST_DB)
    admin = cfg.connect(with_database=False)
    with admin.cursor() as cur:
        cur.execute(f'DROP DATABASE IF EXISTS `{TEST_DB}`')
        cur.execute(f'CREATE DATABASE `{TEST_DB}` CHARACTER SET utf8mb4')
    admin.commit()
    admin.close()
    conn = cfg.connect()
    r = MySQLRepository(conn)
    r.apply_schema()
    r.upsert_instruments([get_symbol('PLTR')])
    yield r
    conn.close()


def count(repo, sql, *params):
    with repo.conn.cursor() as cur:
        cur.execute(sql, params)
        return cur.fetchone()[0]


def test_schema_is_reapplicable(repo):
    assert repo.apply_schema() == 4  # 第二次套用不報錯


def test_upsert_is_idempotent_and_updates(repo):
    days = ['2026-10-14', '2026-10-15', '2026-10-16']
    assert repo.upsert_bars(bars(days, 100.0), run_id=None) == 3
    repo.upsert_bars(bars(days, 100.0), run_id=None)
    assert count(repo, 'SELECT COUNT(*) FROM market_daily') == 3
    repo.upsert_bars(bars(['2026-10-16'], 101.5), run_id=None)
    assert count(repo, "SELECT close FROM market_daily WHERE trade_date='2026-10-16'") == pytest.approx(101.5)


def test_latest_dates_and_replace(repo):
    days = pd.bdate_range('2026-10-05', '2026-10-16')
    repo.upsert_bars(bars(days, 100.0), run_id=None)
    assert repo.latest_dates('moomoo', 'qfq', 3) == {'PLTR': (dt.date(2026, 10, 16), dt.date(2026, 10, 14))}
    repo.upsert_bars(bars(days[-2:], 50.0), run_id=None, replace=True)
    assert count(repo, 'SELECT COUNT(*) FROM market_daily') == 2


def test_adjust_and_source_coexist(repo):
    repo.upsert_bars(bars(['2026-10-16'], 100.0), run_id=None)
    repo.upsert_bars(bars(['2026-10-16'], 200.0, adjust='none'), run_id=None)
    repo.upsert_bars(bars(['2026-10-16'], 100.1, source='yfinance', amount=float('nan'),
                          turnover=float('nan')), run_id=None)
    assert count(repo, 'SELECT COUNT(*) FROM market_daily') == 3
    assert count(repo, 'SELECT COUNT(*) FROM market_daily WHERE amount IS NULL') == 1


def test_course_view_prefers_moomoo_and_uses_percent(repo):
    repo.upsert_bars(bars(['2026-10-15', '2026-10-16'], 100.0), run_id=None)
    repo.upsert_bars(bars(['2026-10-16', '2026-10-19'], 100.1, source='yfinance'), run_id=None)
    with repo.conn.cursor() as cur:
        cur.execute('SELECT trade_date, source, turnover_rate FROM trade_stock_daily ORDER BY trade_date')
        rows = cur.fetchall()
    assert [(str(d), s) for d, s, _ in rows] == [
        ('2026-10-15', 'moomoo'), ('2026-10-16', 'moomoo'), ('2026-10-19', 'yfinance')]
    assert float(rows[0][2]) == pytest.approx(1.23)  # 0.0123 → 1.23（%）


def test_ingest_runs_lifecycle(repo):
    run_id = repo.start_run('market_daily', 'moomoo', 'incremental', ['PLTR'])
    repo.finish_run(run_id, 'success', 3)
    with repo.conn.cursor() as cur:
        cur.execute('SELECT status, rows_written, finished_at IS NOT NULL FROM ingest_runs WHERE run_id=%s',
                    (run_id,))
        assert cur.fetchone() == ('success', 3, 1)
