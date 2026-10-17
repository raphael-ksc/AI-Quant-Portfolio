"""quantlib.fundamentals 與 quantlib.data.edgar 單元測試：人造財報，不需要資料庫、OpenD 與網路。"""
import datetime as dt
import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from quantlib.data import DataSourceError  # noqa: E402
from quantlib.data.edgar import EdgarClient, Filing  # noqa: E402
from quantlib.fundamentals import (  # noqa: E402
    MetricSpec, add_ratios, add_ttm, availability, build_metrics, load_specs, match_filing, resolve, safe_divide,
)

D = dt.date


def items(rows, symbol='PLTR', source='moomoo'):
    """rows：(statement, field_id, period_end, value, fiscal_period)"""
    return pd.DataFrame([{
        'symbol': symbol, 'source': source, 'statement': st, 'field_id': fid, 'name': fid,
        'period_end': pd.Timestamp(pe), 'fiscal_period': fp, 'freq': 'Q', 'value': v, 'currency': 'USD',
        'announce_date': pd.NaT,
    } for st, fid, pe, v, fp in rows])


SPECS = {
    'revenue': MetricSpec('revenue', 'flow', (('income', '8001'), ('income', '8002'))),
    'ocf': MetricSpec('ocf', 'flow', (('cashflow', '8015'),)),
}


# ======================= 多候選科目比對 =======================

def test_resolve_uses_first_available_candidate_and_reports_it():
    df = items([('income', '8001', '2026-03-31', 100.0, '2026/Q1'),
                ('income', '8002', '2026-03-31', 999.0, '2026/Q1'),
                ('income', '8002', '2025-12-31', 90.0, '2025/Q4')])
    wide, rep = resolve(df, SPECS)
    assert wide.set_index('fiscal_period')['revenue'].to_dict() == {'2025/Q4': 90.0, '2026/Q1': 100.0}
    assert rep.used['revenue'] == {'income/8001': 1, 'income/8002': 1}


def test_resolve_never_mixes_statements_with_same_field_id():
    # 8015 在利潤表是 Other Taxes，不可被當成現金流量表的 Operating Cash Flow
    df = items([('income', '8015', '2026-03-31', 5.0, '2026/Q1'), ('income', '8001', '2026-03-31', 1.0, '2026/Q1')])
    wide, rep = resolve(df, SPECS)
    assert pd.isna(wide['ocf'].iloc[0]) and rep.missing['ocf'] == ['2026-03-31']


def test_resolve_aligns_period_end_mismatch_by_fiscal_period():
    # 實測 NVDA FY2025 Q1：利潤表 2024-04-27、現金流量表 2024-04-28（兩份報表 + 資產負債表投多數）
    df = items([('income', '8001', '2024-04-27', 26.0, '2025/Q1'),
                ('cashflow', '8015', '2024-04-28', 15.0, '2025/Q1'),
                ('balance', '8001', '2024-04-28', 65.0, '2025/Q1')])
    wide, rep = resolve(df, SPECS)
    assert len(wide) == 1 and wide['period_end'].iloc[0] == pd.Timestamp('2024-04-28')
    assert (wide['revenue'].iloc[0], wide['ocf'].iloc[0]) == (26.0, 15.0)
    assert rep.aligned == {'2025/Q1': ['2024-04-27', '2024-04-28']}


def test_resolve_rejects_mixed_symbols():
    with pytest.raises(ValueError):
        resolve(pd.concat([items([('income', '8001', '2026-03-31', 1.0, 'Q')]),
                           items([('income', '8001', '2026-03-31', 1.0, 'Q')], symbol='NVDA')]), SPECS)


def test_config_has_both_sources_for_every_metric():
    for source in ('moomoo', 'yfinance'):
        specs = load_specs(source)
        assert {'revenue', 'net_income', 'ocf', 'fcf', 'total_equity', 'total_assets'} <= set(specs)
        assert all(s.candidates for s in specs.values())


# ======================= 近四季合計與比率 =======================

def quarters(ends, **cols):
    return pd.DataFrame({'period_end': pd.to_datetime(ends), **cols})


QE = ['2025-03-31', '2025-06-30', '2025-09-30', '2025-12-31', '2026-03-31']


def test_ttm_needs_four_consecutive_quarters():
    df = add_ttm(quarters(QE, revenue=[1.0, 2.0, 3.0, 4.0, 5.0], gross_profit=[None] * 5, net_income=[1.0] * 5,
                          ocf=[1.0, None, 1.0, 1.0, 1.0], capex=[0.0] * 5, fcf=[0.0] * 5))
    assert df['revenue_ttm'].tolist()[3:] == [10.0, 14.0]
    assert df['revenue_ttm'].iloc[:3].isna().all()
    assert df['ocf_ttm'].iloc[3:].isna().all()                   # 窗口內缺一季 → 留空，不外推


def test_ttm_rejects_gap_between_quarters():
    ends = ['2024-12-31', '2025-06-30', '2025-09-30', '2025-12-31']   # 少了 2025-03-31
    df = add_ttm(quarters(ends, revenue=[1.0] * 4, gross_profit=[1.0] * 4, net_income=[1.0] * 4,
                          ocf=[1.0] * 4, capex=[1.0] * 4, fcf=[1.0] * 4))
    assert pd.isna(df['revenue_ttm'].iloc[-1])


def test_ttm_accepts_52_53_week_fiscal_quarters():
    ends = ['2025-04-27', '2025-07-27', '2025-10-26', '2026-01-25']   # NVDA 的週日期末
    df = add_ttm(quarters(ends, revenue=[1.0] * 4, gross_profit=[1.0] * 4, net_income=[1.0] * 4,
                          ocf=[1.0] * 4, capex=[1.0] * 4, fcf=[1.0] * 4))
    assert df['revenue_ttm'].iloc[-1] == 4.0


def test_ratios_and_guards():
    df = add_ratios(pd.DataFrame([
        {'net_income_ttm': 20.0, 'total_equity': 100.0, 'total_assets': 200.0, 'revenue_ttm': 80.0,
         'gross_profit_ttm': 60.0, 'ocf_ttm': 30.0, 'fcf_ttm': 10.0, 'total_liabilities': 100.0,
         'current_assets': 50.0, 'current_liabilities': 25.0, 'revenue': 20.0, 'gross_profit': 15.0,
         'net_income': 5.0},
        {'net_income_ttm': -20.0, 'total_equity': -5.0, 'total_assets': 200.0, 'revenue_ttm': 0.0,
         'gross_profit_ttm': 0.0, 'ocf_ttm': 30.0, 'fcf_ttm': 1.0, 'total_liabilities': 205.0,
         'current_assets': 50.0, 'current_liabilities': 0.0, 'revenue': None, 'gross_profit': 1.0,
         'net_income': 1.0},
    ]))
    ok, bad = df.iloc[0], df.iloc[1]
    assert (ok['roe_ttm'], ok['roa_ttm'], ok['gross_margin_ttm']) == (0.2, 0.1, 0.75)
    assert (ok['ocf_to_ni_ttm'], ok['debt_ratio'], ok['current_ratio']) == (1.5, 0.5, 2.0)
    assert pd.isna(bad['roe_ttm'])                # 負權益 → ROE 留空
    assert pd.isna(bad['ocf_to_ni_ttm'])          # 淨利 ≤ 0 → 盈餘品質比值留空
    assert pd.isna(bad['gross_margin_ttm'])       # 營收為 0
    assert pd.isna(bad['current_ratio']) and pd.isna(bad['net_margin_q'])


def test_safe_divide():
    assert safe_divide(1, 2) == 0.5
    assert safe_divide(1, 0) is None and safe_divide(None, 2) is None
    assert safe_divide(1, -2) == -0.5 and safe_divide(1, -2, positive_den=True) is None


# ======================= 可交易日 =======================

FILINGS = [Filing('10-Q', D(2026, 8, 26), D(2026, 7, 26)), Filing('10-K', D(2026, 2, 25), D(2026, 1, 25))]


def test_availability_uses_edgar_filing_date_plus_one_day():
    a = availability(D(2026, 7, 26), '2027/Q2', FILINGS)
    assert (a.filing_date, a.filing_form, a.available_date, a.basis) == (D(2026, 8, 26), '10-Q', D(2026, 8, 27), 'edgar')


def test_availability_matches_within_tolerance():
    assert match_filing(D(2026, 7, 31), FILINGS).form == '10-Q'          # 差 5 天
    assert match_filing(D(2026, 9, 30), FILINGS) is None                  # 差 66 天


def test_availability_falls_back_to_conservative_lags():
    q = availability(D(2024, 3, 31), '2024/Q3', [])
    q4 = availability(D(2024, 6, 30), '2024/Q4', [])
    assert (q.available_date, q.basis) == (D(2024, 5, 16), 'lag_rule')   # +45 天再隔天
    assert q4.available_date == D(2024, 9, 14)                            # 財年 Q4 +75 天再隔天


def test_build_metrics_end_to_end():
    rows = []
    for i, (pe, fp) in enumerate(zip(QE, ['2025/Q1', '2025/Q2', '2025/Q3', '2025/Q4', '2026/Q1'])):
        rows += [('income', '8001', pe, 100.0 + i, fp), ('income', '8004', pe, 80.0, fp),
                 ('income', '8043', pe, 10.0, fp), ('cashflow', '8015', pe, 12.0, fp),
                 ('balance', '8081', pe, 400.0, fp), ('balance', '8001', pe, 500.0, fp)]
    wide, rep = build_metrics(items(rows), 'moomoo', [Filing('10-Q', D(2026, 5, 5), D(2026, 3, 31))])
    last = wide.iloc[-1]
    assert last['revenue_ttm'] == 101 + 102 + 103 + 104 and last['roe_ttm'] == 40 / 400
    assert last['available_basis'] == 'edgar' and wide.iloc[0]['available_basis'] == 'lag_rule'
    assert 'eps_basic' in rep.missing   # 人造資料沒有 EPS → 回報缺值，不推算


# ======================= EDGAR client =======================

def fake_fetch(responses):
    calls = []

    def fetch(url, ua):
        calls.append((url, ua))
        return responses[url]
    fetch.calls = calls
    return fetch


def test_edgar_requires_contact_email():
    with pytest.raises(DataSourceError):
        EdgarClient('no-email-here', fetch=fake_fetch({}), sleep=lambda s: None)


def test_edgar_parses_periodic_filings_only():
    fetch = fake_fetch({
        'https://www.sec.gov/files/company_tickers.json': {'0': {'cik_str': 1321655, 'ticker': 'PLTR'}},
        'https://data.sec.gov/submissions/CIK0001321655.json': {'filings': {'recent': {
            'form': ['10-Q', '8-K', '10-K', '10-Q/A'],
            'filingDate': ['2026-08-04', '2026-08-04', '2026-02-17', '2026-09-01'],
            'reportDate': ['2026-06-30', '2026-08-04', '2025-12-31', '2026-06-30'],
        }}},
    })
    client = EdgarClient('Test test@example.com', fetch=fetch, sleep=lambda s: None)
    got = client.periodic_filings('pltr')
    assert [(f.form, f.report_date) for f in got] == [('10-K', D(2025, 12, 31)), ('10-Q', D(2026, 6, 30))]
    assert all(ua == 'Test test@example.com' for _, ua in fetch.calls)


def test_edgar_unknown_ticker():
    fetch = fake_fetch({'https://www.sec.gov/files/company_tickers.json': {}})
    with pytest.raises(DataSourceError):
        EdgarClient('t t@example.com', fetch=fetch, sleep=lambda s: None).cik('ZZZZ')
