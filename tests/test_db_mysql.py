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
    assert repo.apply_schema() == 8  # 第二次套用不報錯


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


# ======================= 財務數據（C07） =======================

def fin_items(value, period='2026-06-30', fp='2026/Q2', source='moomoo'):
    return pd.DataFrame([{
        'symbol': 'PLTR', 'source': source, 'statement': 'income', 'field_id': '8001',
        'name': 'Total Revenue as Reported', 'period_end': pd.Timestamp(period), 'fiscal_period': fp,
        'freq': 'Q', 'value': value, 'currency': 'USD',
    }])


def test_financial_items_idempotent_and_revisions_kept(repo):
    assert repo.upsert_financial_items(fin_items(1_003_000_000.0), run_id=None) == (1, 0)
    assert repo.upsert_financial_items(fin_items(1_003_000_000.0), run_id=None) == (1, 0)   # 同值不算重編
    assert repo.upsert_financial_items(fin_items(1_010_000_000.0), run_id=None) == (1, 1)   # 重編
    assert count(repo, 'SELECT COUNT(*) FROM financial_items') == 1
    with repo.conn.cursor() as cur:
        cur.execute('SELECT old_value, new_value FROM financial_revisions')
        assert [tuple(float(v) for v in r) for r in cur.fetchall()] == [(1_003_000_000.0, 1_010_000_000.0)]
    back = repo.load_financial_items('PLTR', 'moomoo')
    assert back['value'].iloc[0] == 1_010_000_000.0


def test_financial_metrics_and_course_view(repo):
    metrics = pd.DataFrame([{
        'symbol': 'PLTR', 'source': source, 'period_end': pd.Timestamp('2026-06-30'), 'freq': 'Q',
        'fiscal_period': '2026/Q2', 'currency': 'USD', 'filing_date': dt.date(2026, 8, 4), 'filing_form': '10-Q',
        'available_date': dt.date(2026, 8, 5), 'available_basis': 'edgar', 'revenue': 1.0e9,
        'net_income': 4.0e8, 'roe_ttm': 0.305, 'gross_margin_ttm': 0.848, 'debt_ratio': 0.154,
        'current_ratio': 7.2, 'eps_basic': 0.17,
    } for source in ('moomoo', 'yfinance')])
    assert repo.upsert_financial_metrics(metrics, run_id=None) == 2
    with repo.conn.cursor() as cur:
        cur.execute('SELECT stock_code, report_date, roe, gross_margin, debt_ratio, available_date, data_source '
                    'FROM trade_stock_financial')
        rows = cur.fetchall()
    assert len(rows) == 1                                            # 兩個資料源只取 Moomoo
    code, report_date, roe, gm, dr, avail, src = rows[0]
    assert (code, str(report_date), str(avail), src) == ('PLTR', '2026-06-30', '2026-08-05', 'moomoo')
    assert (float(roe), float(gm), float(dr)) == pytest.approx((30.5, 84.8, 15.4))   # 換算成課程的百分比
