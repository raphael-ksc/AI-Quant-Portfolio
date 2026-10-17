"""SEC EDGAR 申報資料：查 10-Q / 10-K 的申報日，當作財報「什麼時候市場才知道」的依據。

Moomoo 與 yfinance 的財報只有報告期結束日，沒有公告日（docs/moomoo_api_notes.md）。
直接用期末日回測，等於提前 1–2 個月看到財報，會產生前視偏差。

SEC 規定（https://www.sec.gov/os/accessing-edgar-data）：
- 每個請求的 User-Agent 都要附聯絡 email → 從 .env 的 SEC_USER_AGENT 讀，不寫在程式碼
- 每秒最多 10 個請求 → 本模組每次呼叫間隔 0.2 秒
"""
from __future__ import annotations

import datetime as dt
import json
import os
import time
import urllib.request
from dataclasses import dataclass
from typing import Callable

from .base import DataSourceError

TICKERS_URL = 'https://www.sec.gov/files/company_tickers.json'
SUBMISSIONS_URL = 'https://data.sec.gov/submissions/CIK{cik:010d}.json'
PERIODIC_FORMS = ('10-Q', '10-K')   # 只用原始申報；修正版（/A）晚於原始申報，不代表市場第一次得知的時間


@dataclass(frozen=True)
class Filing:
    form: str
    filing_date: dt.date
    report_date: dt.date


def fetch_json(url: str, user_agent: str) -> dict:
    req = urllib.request.Request(url, headers={'User-Agent': user_agent, 'Accept-Encoding': 'identity'})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except Exception as e:  # noqa: BLE001 — 網路錯誤型別很多，統一包裝
        raise DataSourceError(f'SEC EDGAR 讀取失敗：{url}（{type(e).__name__}: {e}）') from e


class EdgarClient:
    def __init__(self, user_agent: str | None = None, *, fetch: Callable[[str, str], dict] = fetch_json,
                 interval: float = 0.2, sleep: Callable[[float], None] = time.sleep):
        self.user_agent = (user_agent or os.getenv('SEC_USER_AGENT', '')).strip().strip('"')
        if '@' not in self.user_agent:
            raise DataSourceError('SEC_USER_AGENT 未設定或缺少 email（SEC 規定），請在 .env 設定')
        self._fetch, self._interval, self._sleep = fetch, interval, sleep
        self._ciks: dict[str, int] | None = None

    def _get(self, url: str) -> dict:
        self._sleep(self._interval)
        return self._fetch(url, self.user_agent)

    def cik(self, ticker: str) -> int:
        if self._ciks is None:
            data = self._get(TICKERS_URL)
            self._ciks = {v['ticker'].upper(): int(v['cik_str']) for v in data.values()}
        try:
            return self._ciks[ticker.upper()]
        except KeyError as e:
            raise DataSourceError(f'SEC EDGAR 找不到 {ticker} 的 CIK') from e

    def periodic_filings(self, ticker: str) -> list[Filing]:
        """最近的 10-Q / 10-K 原始申報（EDGAR recent 區段，約最近 1,000 筆申報）。"""
        recent = self._get(SUBMISSIONS_URL.format(cik=self.cik(ticker)))['filings']['recent']
        out = []
        for form, filed, report in zip(recent['form'], recent['filingDate'], recent['reportDate']):
            if form in PERIODIC_FORMS and filed and report:
                out.append(Filing(form, dt.date.fromisoformat(filed), dt.date.fromisoformat(report)))
        return sorted(out, key=lambda f: f.report_date)
