"""日線寫入流程：規劃 → 抓取 → 驗證 → 比對復權基準 → 寫入 → 紀錄。

DataSource 與 repository 都由外部傳入，單元測試可以換成假物件，不需要 OpenD 與 MySQL。
"""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field

from ..data.base import DataSource, DataSourceError
from ..data.schema import SchemaError, validate_bars
from ..data.symbols import Symbol
from .planner import (DEFAULT_LOOKBACK, DEFAULT_START, MarketHours, last_closed_session,
                      needs_refresh, plan_fetch, trim_unclosed)

JOB = 'market_daily'


@dataclass
class SymbolResult:
    symbol: str
    adjust: str
    reason: str               # full / incremental / refresh / up_to_date / failed
    rows: int = 0
    start: str | None = None
    end: str | None = None
    mismatched_dates: list[str] = field(default_factory=list)
    error: str | None = None


def ingest_daily(repo, source: DataSource, symbols: list[Symbol], *, adjusts=('qfq', 'none'),
                 mode: str = 'incremental', now: dt.datetime | None = None,
                 default_start: dt.date = DEFAULT_START, lookback: int = DEFAULT_LOOKBACK,
                 hours: MarketHours = MarketHours()) -> dict:
    """寫入日線並回傳摘要；單一標的失敗不中斷其他標的（狀態記為 partial）。"""
    now = now or dt.datetime.now(dt.timezone.utc)
    last_session = last_closed_session(now, hours)
    repo.upsert_instruments(symbols)
    run_id = repo.start_run(JOB, source.name, mode, [s.ticker for s in symbols])
    results: list[SymbolResult] = []

    try:
        for adjust in adjusts:
            known = repo.latest_dates(source.name, adjust, lookback)
            for sym in symbols:
                latest, overlap = known.get(sym.ticker, (None, None))
                plan = plan_fetch(sym.ticker, adjust, latest=latest, overlap_start=overlap,
                                  last_session=last_session, mode=mode, default_start=default_start)
                results.append(_ingest_one(repo, source, sym, plan, run_id, default_start, last_session))
    except Exception as e:
        repo.finish_run(run_id, 'failed', sum(r.rows for r in results), f'{type(e).__name__}: {e}')
        raise

    failed = [r for r in results if r.reason == 'failed']
    status = 'success' if not failed else ('failed' if len(failed) == len(results) else 'partial')
    message = '; '.join(f'{r.symbol}/{r.adjust}: {r.error}' for r in failed) or None
    total = sum(r.rows for r in results)
    repo.finish_run(run_id, status, total, message)
    return {'run_id': run_id, 'status': status, 'rows_written': total,
            'last_session': last_session.isoformat(), 'results': results}


def _ingest_one(repo, source: DataSource, sym: Symbol, plan, run_id: int,
                default_start: dt.date, last_session: dt.date) -> SymbolResult:
    if plan.skip:
        return SymbolResult(sym.ticker, plan.adjust, plan.reason)
    try:
        bars = _fetch(source, sym, plan.start, plan.end, plan.adjust, last_session)
        reason, replace, mismatched = plan.reason, plan.reason == 'full', []

        if plan.reason == 'incremental':
            stored = repo.load_closes(sym.ticker, source.name, plan.adjust, plan.start)
            mismatched = needs_refresh(stored, bars)
            if mismatched:
                # 復權基準改變：從庫中最早日期（或預設起點）整段重抓並取代舊資料
                earliest = repo.earliest_date(sym.ticker, source.name, plan.adjust) or default_start
                bars = _fetch(source, sym, min(earliest, default_start), plan.end, plan.adjust, last_session)
                reason, replace = 'refresh', True

        rows = repo.upsert_bars(bars, run_id, replace=replace)
        dates = bars['date'].dt.date
        return SymbolResult(sym.ticker, plan.adjust, reason, rows, dates.min().isoformat(),
                            dates.max().isoformat(), [d.date().isoformat() for d in mismatched])
    except (DataSourceError, SchemaError, KeyError) as e:
        return SymbolResult(sym.ticker, plan.adjust, 'failed', error=f'{type(e).__name__}: {e}')


def _fetch(source: DataSource, sym: Symbol, start: dt.date, end: dt.date, adjust: str,
           last_session: dt.date):
    bars = source.get_daily_bars(sym, start, end, adjust=adjust)
    return validate_bars(trim_unclosed(bars, last_session), 'daily')
