"""財報可交易日（available_date）：回測時，這期財報最早哪一天可以用。

優先順序：
1. SEC EDGAR 的 10-Q / 10-K 原始申報日（期末日前後 10 天內的申報，對應 NVDA 這種「1 月最後一個週日」的財年）
2. 查不到時用保守推算：季報 = 期末日 + 45 天、財年第 4 季 = 期末日 + 75 天
   （SEC 申報期限：大型加速申報公司 10-Q 為 40 天、10-K 為 60 天，推算值刻意比期限晚）

可交易日 = 申報日（或推算日）的隔天：申報常在收盤後，當天收盤價還沒反映。
用申報日而不是財報發布日（earnings release）是保守做法：發布日通常更早，市場在那天就開始反應。
"""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass

from ..data.edgar import Filing

MATCH_WINDOW_DAYS = 10
LAG_QUARTER_DAYS = 45
LAG_ANNUAL_DAYS = 75


@dataclass(frozen=True)
class Availability:
    filing_date: dt.date | None
    filing_form: str | None
    available_date: dt.date
    basis: str          # edgar / lag_rule


def match_filing(period_end: dt.date, filings: list[Filing]) -> Filing | None:
    """找報告期與期末日相差 ≤ 10 天的申報；有多筆時取最早申報的那筆。"""
    close = [f for f in filings if abs((f.report_date - period_end).days) <= MATCH_WINDOW_DAYS]
    return min(close, key=lambda f: f.filing_date) if close else None


def is_fiscal_q4(fiscal_period: str | None) -> bool:
    return bool(fiscal_period) and str(fiscal_period).upper().endswith('Q4')


def availability(period_end: dt.date, fiscal_period: str | None, filings: list[Filing]) -> Availability:
    f = match_filing(period_end, filings)
    if f is not None:
        return Availability(f.filing_date, f.form, f.filing_date + dt.timedelta(days=1), 'edgar')
    lag = LAG_ANNUAL_DAYS if is_fiscal_q4(fiscal_period) else LAG_QUARTER_DAYS
    return Availability(None, None, period_end + dt.timedelta(days=lag + 1), 'lag_rule')
