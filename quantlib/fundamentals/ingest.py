"""財務數據流程：抓財報 → 驗證 → 寫入長表（偵測重編）→ 科目比對 → 近四季合計與比率 → 可交易日 → 寫入指標表。

資料源、EDGAR、repository 都由外部傳入，單元測試可換成假物件。
"""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field

import pandas as pd

from ..data.base import DataSource, DataSourceError
from ..data.schema import SchemaError, validate_financials
from ..data.symbols import Symbol
from .availability import availability
from .fields import MatchReport, load_specs, resolve
from .metrics import add_ratios, add_ttm

JOB = 'financials'


@dataclass
class FinancialResult:
    symbol: str
    status: str                      # success / failed
    periods: int = 0
    items: int = 0
    revisions: int = 0
    first: str | None = None
    last: str | None = None
    edgar_matched: int = 0
    edgar_error: str | None = None
    report: dict = field(default_factory=dict)
    error: str | None = None


def build_metrics(items: pd.DataFrame, source: str, filings: list, specs=None) -> tuple[pd.DataFrame, MatchReport]:
    """財報長表（單一標的、季報）→ 指標寬表（含近四季合計、比率、可交易日）。"""
    specs = specs or load_specs(source)
    wide, report = resolve(items, specs)
    wide = add_ratios(add_ttm(wide))
    avail = [availability(pd.Timestamp(r.period_end).date(), r.fiscal_period, filings)
             for r in wide.itertuples(index=False)]
    wide['filing_date'] = [a.filing_date for a in avail]
    wide['filing_form'] = [a.filing_form for a in avail]
    wide['available_date'] = [a.available_date for a in avail]
    wide['available_basis'] = [a.basis for a in avail]
    wide['symbol'] = items['symbol'].iloc[0]
    wide['source'] = source
    wide['freq'] = items['freq'].iloc[0]
    wide['currency'] = items['currency'].iloc[0]
    return wide, report


def ingest_financials(repo, source: DataSource, symbols: list[Symbol], *, edgar=None, periods: int = 12) -> dict:
    """寫入財報與指標；單一標的失敗不中斷其他標的。edgar=None 時全部用保守推算的可交易日。"""
    repo.upsert_instruments(symbols)
    run_id = repo.start_run(JOB, source.name, 'full', [s.ticker for s in symbols])
    results = []
    for sym in symbols:
        try:
            items = validate_financials(source.get_financials(sym, freq='Q', periods=periods))
            n_items, n_rev = repo.upsert_financial_items(items, run_id)
            filings, edgar_error = [], None
            if edgar is not None:
                try:
                    filings = edgar.periodic_filings(sym.ticker)
                except DataSourceError as e:
                    edgar_error = str(e)   # EDGAR 失敗時退回保守推算，不中斷
            wide, report = build_metrics(items, source.name, filings)
            repo.upsert_financial_metrics(wide, run_id)
            ends = pd.to_datetime(wide['period_end'])
            results.append(FinancialResult(
                sym.ticker, 'success', len(wide), n_items, n_rev, ends.min().date().isoformat(),
                ends.max().date().isoformat(), int((wide['available_basis'] == 'edgar').sum()), edgar_error,
                report.as_dict()))
        except (DataSourceError, SchemaError, KeyError, ValueError) as e:
            results.append(FinancialResult(sym.ticker, 'failed', error=f'{type(e).__name__}: {e}'))

    failed = [r for r in results if r.status == 'failed']
    status = 'success' if not failed else ('failed' if len(failed) == len(results) else 'partial')
    repo.finish_run(run_id, status, sum(r.items for r in results),
                    '; '.join(f'{r.symbol}: {r.error}' for r in failed) or None)
    return {'run_id': run_id, 'status': status, 'run_date': dt.date.today().isoformat(), 'results': results}
