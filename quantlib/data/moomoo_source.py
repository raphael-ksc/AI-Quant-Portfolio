"""Moomoo OpenAPI 資料源（原課程為 QMT，此處為 Moomoo 版本）。

前置條件：OpenD 已在本機啟動並登入（預設 127.0.0.1:11111）。本模組只讀取行情與財報，不下單。

實測行為（docs/moomoo_api_notes.md、knowledge/data-engineering/moomoo-vs-yfinance.md）：
- 財報 `date_time_str` 比實際期末日早 1 天；正確期末日 = `date_time` 以 UTC+8 換算的日期
- 財報 `field_id` 只在同一 statement_type 內唯一；同公司不同期的科目數可能不同
- 財報接口頻率限制嚴格：每次呼叫間隔 ≥ 1 秒，遇頻率錯誤等 5 秒重試
- K 線與財報都會分頁（page_req_key / next_key），必須迴圈取完
- 美股分鐘線 time_key 為美東當地時間，標示 K 棒結束時間（第一根為 09:31）
"""
from __future__ import annotations

import datetime as dt
import os
import time
from typing import Any, Callable

import pandas as pd

from .base import DataSource, DataSourceError
from .symbols import Symbol

UTC8 = dt.timezone(dt.timedelta(hours=8))
STATEMENT_TYPES = {'income': 1, 'balance': 2, 'cashflow': 3}
FINANCIAL_TYPES = {'Q': 9, 'A': 7}  # 9：單季；7：年報
RATE_LIMIT_KEYWORDS = ('frequency', 'rate limit', 'too many', '频率', '頻率')
MAX_PAGES = 50  # 分頁保險上限，避免 API 異常時無窮迴圈


def period_end_from_timestamp(ts: int | float) -> dt.date:
    """Moomoo 財報 date_time 時間戳 → 實際期末日（以 UTC+8 換算）。"""
    return dt.datetime.fromtimestamp(ts, tz=UTC8).date()


class MoomooSource(DataSource):
    name = 'moomoo'

    def __init__(self, host: str | None = None, port: int | None = None, *,
                 ft_module: Any = None, ctx: Any = None,
                 call_interval: float = 1.1, max_retries: int = 3, retry_wait: float = 5.0,
                 sleep: Callable[[float], None] = time.sleep, clock: Callable[[], float] = time.monotonic):
        if ft_module is None:
            import moomoo as ft_module  # 延遲載入：沒裝 moomoo 的環境（CI）仍可使用其他資料源
        self.ft = ft_module
        host = host or os.getenv('MOOMOO_OPEND_HOST', '127.0.0.1')
        port = int(port or os.getenv('MOOMOO_OPEND_PORT', '11111'))
        self.ctx = ctx if ctx is not None else self.ft.OpenQuoteContext(host=host, port=port)
        self.call_interval = call_interval
        self.max_retries = max_retries
        self.retry_wait = retry_wait
        self._sleep = sleep
        self._clock = clock
        self._last_call: float | None = None

    # ---------- 連線與節流 ----------

    def close(self) -> None:
        if self.ctx is not None:
            self.ctx.close()
            self.ctx = None

    def _throttle(self) -> None:
        if self._last_call is not None:
            wait = self.call_interval - (self._clock() - self._last_call)
            if wait > 0:
                self._sleep(wait)
        self._last_call = self._clock()

    def _call(self, method: str, *args, **kwargs):
        """呼叫 OpenD API：自動節流；遇頻率限制時等待後重試；其他錯誤直接拋出。"""
        for attempt in range(1, self.max_retries + 1):
            self._throttle()
            result = getattr(self.ctx, method)(*args, **kwargs)
            ret, data = result[0], result[1]
            if ret == self.ft.RET_OK:
                return result
            message = str(data)
            if any(k in message.lower() for k in RATE_LIMIT_KEYWORDS) and attempt < self.max_retries:
                self._sleep(self.retry_wait)
                continue
            raise DataSourceError(f'Moomoo {method} 失敗：{message}')
        raise DataSourceError(f'Moomoo {method} 重試 {self.max_retries} 次仍失敗')  # pragma: no cover

    # ---------- K 線 ----------

    def _kline(self, code: str, start: str, end: str, ktype, autype, extended_time: bool) -> pd.DataFrame:
        frames, page_key = [], None
        for _ in range(MAX_PAGES):
            _, data, page_key = self._call(
                'request_history_kline', code, start=start, end=end, ktype=ktype, autype=autype,
                max_count=1000, page_req_key=page_key, extended_time=extended_time)
            frames.append(data)
            if page_key is None:
                break
        else:
            raise DataSourceError(f'{code} K 線分頁超過 {MAX_PAGES} 頁，請縮小日期區間')
        return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()

    def _autype(self, adjust: str):
        return {'qfq': self.ft.AuType.QFQ, 'none': self.ft.AuType.NONE}[adjust]

    def get_daily_bars(self, symbol: Symbol, start: dt.date, end: dt.date,
                       adjust: str = 'qfq') -> pd.DataFrame:
        raw = self._kline(symbol.code_for('moomoo'), start.isoformat(), end.isoformat(),
                          self.ft.KLType.K_DAY, self._autype(adjust), extended_time=False)
        df = pd.DataFrame({
            'symbol': symbol.ticker,
            'date': pd.to_datetime(raw['time_key']).dt.normalize(),
            'open': raw['open'].astype(float),
            'high': raw['high'].astype(float),
            'low': raw['low'].astype(float),
            'close': raw['close'].astype(float),
            'volume': raw['volume'].astype(float),
            # 選填欄位：turnover 為成交額；turnover_rate 為比例（0.0115 = 1.15%），2026-10-17 實測
            'amount': raw['turnover'].astype(float) if 'turnover' in raw else float('nan'),
            'turnover_rate': raw['turnover_rate'].astype(float) if 'turnover_rate' in raw else float('nan'),
        })
        df['adjust'], df['currency'], df['source'] = adjust, symbol.currency, self.name
        return df.drop_duplicates(['symbol', 'date']).reset_index(drop=True)

    def get_minute_bars(self, symbol: Symbol, day: dt.date, adjust: str = 'qfq') -> pd.DataFrame:
        raw = self._kline(symbol.code_for('moomoo'), day.isoformat(), day.isoformat(),
                          self.ft.KLType.K_1M, self._autype(adjust), extended_time=False)
        ts = pd.to_datetime(raw['time_key']).dt.tz_localize(symbol.timezone)
        df = pd.DataFrame({
            'symbol': symbol.ticker,
            'ts': ts,
            'open': raw['open'].astype(float),
            'high': raw['high'].astype(float),
            'low': raw['low'].astype(float),
            'close': raw['close'].astype(float),
            'volume': raw['volume'].astype(float),
        })
        # 保險：只保留正常交易時段（K 棒結束時間 09:31–16:00）
        clock = df['ts'].dt.strftime('%H:%M')
        df = df[(clock >= '09:31') & (clock <= '16:00')]
        df['adjust'], df['currency'], df['source'] = adjust, symbol.currency, self.name
        return df.drop_duplicates(['symbol', 'ts']).reset_index(drop=True)

    # ---------- 財報 ----------

    def _reports(self, code: str, statement_type: int, financial_type: int, periods: int) -> list[dict]:
        """依 next_key 分頁取回報表，直到期數足夠或沒有下一頁。"""
        reports: list[dict] = []
        seen: set[int] = set()
        next_key = None
        for _ in range(MAX_PAGES):
            _, data = self._call('get_financials_statements', code, statement_type=statement_type,
                                 financial_type=financial_type, next_key=next_key,
                                 num=periods - len(reports))
            new = [r for r in data.get('report_list', []) if r['date_time'] not in seen]
            seen.update(r['date_time'] for r in new)
            reports.extend(new)
            next_key = data.get('next_key')
            if len(reports) >= periods or not next_key or not new:
                break
        return reports[:periods]

    def get_financials(self, symbol: Symbol, freq: str = 'Q', periods: int = 8) -> pd.DataFrame:
        code = symbol.code_for('moomoo')
        rows = []
        for statement, stype in STATEMENT_TYPES.items():
            for report in self._reports(code, stype, FINANCIAL_TYPES[freq], periods):
                period_end = period_end_from_timestamp(report['date_time'])
                currency = report.get('currency_code') or symbol.currency
                for item in report.get('item_list', []):
                    rows.append({
                        'symbol': symbol.ticker,
                        'source': self.name,
                        'statement': statement,
                        'field_id': str(item['field_id']),
                        'name': item.get('display_name'),
                        'period_end': pd.Timestamp(period_end),
                        'fiscal_period': report.get('period_text'),
                        'freq': freq,
                        'value': item.get('data'),
                        'currency': currency,
                        'announce_date': pd.NaT,  # Moomoo 不提供公告日
                    })
        return pd.DataFrame(rows)

    def quota(self) -> dict:
        """歷史 K 線額度使用狀況（每 30 天的標的數上限）。"""
        _, data = self._call('get_history_kl_quota', get_detail=False)
        if isinstance(data, pd.DataFrame):
            return data.to_dict(orient='records')[0] if not data.empty else {}
        if isinstance(data, tuple) and len(data) >= 2:
            # 實測回傳 (已用標的數, 剩餘標的數, 明細)，例如 (2, 98, [])
            return {'used': data[0], 'remaining': data[1]}
        return data if isinstance(data, dict) else {'raw': str(data)}
