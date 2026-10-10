"""yfinance 資料源：公開重現用，任何人不需帳號即可執行。

已知限制：
- `history(end=...)` 不含 end 當天，本模組自動 +1 天，讓 start、end 皆包含在內
- 1 分鐘線只能抓最近 7 天，超出範圍回傳空表而不報錯；本模組改為明確拋 DataUnavailableError
- 季報通常只有最近 5–6 期（Moomoo 約 12 期以上）；季報為空時自動改抓年報並標 freq='A'
- 財報科目名稱與 Moomoo 不同（field_id 這裡用 yfinance 的科目名，例如 TotalRevenue）
- 非官方套件、資料來自 Yahoo，原始數據不可公開轉發；本專案只公開彙總結果
"""
from __future__ import annotations

import datetime as dt
from typing import Any

import pandas as pd

from .base import DataSource, DataSourceError, DataUnavailableError
from .symbols import Symbol

MINUTE_LOOKBACK_DAYS = 7
STATEMENT_METHODS = {
    'income': 'get_income_stmt',
    'balance': 'get_balance_sheet',
    'cashflow': 'get_cashflow',
}


class YFinanceSource(DataSource):
    name = 'yfinance'

    def __init__(self, *, yf_module: Any = None, today: dt.date | None = None):
        if yf_module is None:
            import yfinance as yf_module
        self.yf = yf_module
        self._today = today

    @property
    def today(self) -> dt.date:
        return self._today or dt.date.today()

    def _history(self, symbol: Symbol, **kwargs) -> pd.DataFrame:
        try:
            df = self.yf.Ticker(symbol.code_for('yfinance')).history(**kwargs)
        except Exception as e:  # noqa: BLE001 — yfinance 的例外型別不固定，統一包裝
            raise DataSourceError(f'yfinance 抓取 {symbol.ticker} 失敗：{e}') from e
        if df is None or df.empty:
            raise DataUnavailableError(f'yfinance 沒有回傳 {symbol.ticker} 的資料：{kwargs}')
        return df

    @staticmethod
    def _bars(df: pd.DataFrame, symbol: Symbol, adjust: str) -> pd.DataFrame:
        out = pd.DataFrame({
            'symbol': symbol.ticker,
            'open': df['Open'].astype(float).to_numpy(),
            'high': df['High'].astype(float).to_numpy(),
            'low': df['Low'].astype(float).to_numpy(),
            'close': df['Close'].astype(float).to_numpy(),
            'volume': df['Volume'].astype(float).to_numpy(),
        })
        out['adjust'], out['currency'], out['source'] = adjust, symbol.currency, 'yfinance'
        return out

    def get_daily_bars(self, symbol: Symbol, start: dt.date, end: dt.date,
                       adjust: str = 'qfq') -> pd.DataFrame:
        # auto_adjust=True：價格依分割與股利調整，對應 Moomoo 的前復權（QFQ）
        df = self._history(symbol, start=start.isoformat(),
                           end=(end + dt.timedelta(days=1)).isoformat(),
                           interval='1d', auto_adjust=(adjust == 'qfq'), actions=False)
        out = self._bars(df, symbol, adjust)
        index = pd.DatetimeIndex(df.index)
        if index.tz is not None:
            index = index.tz_convert(symbol.timezone).tz_localize(None)
        out.insert(1, 'date', index.normalize())
        return out[(out['date'] >= pd.Timestamp(start)) & (out['date'] <= pd.Timestamp(end))].reset_index(drop=True)

    def get_minute_bars(self, symbol: Symbol, day: dt.date, adjust: str = 'qfq') -> pd.DataFrame:
        if (self.today - day).days > MINUTE_LOOKBACK_DAYS:
            raise DataUnavailableError(
                f'yfinance 1 分鐘線只提供最近 {MINUTE_LOOKBACK_DAYS} 天，{day} 已超出範圍')
        df = self._history(symbol, start=day.isoformat(), end=(day + dt.timedelta(days=1)).isoformat(),
                           interval='1m', auto_adjust=(adjust == 'qfq'), prepost=False, actions=False)
        out = self._bars(df, symbol, adjust)
        # yfinance 的時間是 K 棒開始時間；+1 分鐘換成結束時間，與 Moomoo 一致
        start_ts = pd.DatetimeIndex(df.index)
        if start_ts.tz is None:
            start_ts = start_ts.tz_localize(symbol.timezone)
        out.insert(1, 'ts', start_ts.tz_convert(symbol.timezone) + pd.Timedelta(minutes=1))
        return out

    def _statement(self, symbol: Symbol, statement: str, freq: str) -> pd.DataFrame:
        tk = self.yf.Ticker(symbol.code_for('yfinance'))
        df = getattr(tk, STATEMENT_METHODS[statement])(freq='quarterly' if freq == 'Q' else 'yearly')
        return df if df is not None else pd.DataFrame()

    def get_financials(self, symbol: Symbol, freq: str = 'Q', periods: int = 8) -> pd.DataFrame:
        tables = {s: self._statement(symbol, s, freq) for s in STATEMENT_METHODS}
        if freq == 'Q' and all(t.empty for t in tables.values()):
            # 季報為空（例如只出半年報的市場）時改抓年報，freq 標成 'A' 避免誤用
            freq = 'A'
            tables = {s: self._statement(symbol, s, freq) for s in STATEMENT_METHODS}
        rows = []
        for statement, table in tables.items():
            if table.empty:
                continue
            cols = sorted(table.columns, reverse=True)[:periods]
            for item, values in table[cols].iterrows():
                for period, value in values.items():
                    if pd.isna(value):
                        continue
                    rows.append({
                        'symbol': symbol.ticker,
                        'source': self.name,
                        'statement': statement,
                        'field_id': str(item),
                        'name': str(item),
                        'period_end': pd.Timestamp(period).normalize(),
                        'fiscal_period': None,
                        'freq': freq,
                        'value': float(value),
                        'currency': symbol.currency,
                        'announce_date': pd.NaT,
                    })
        if not rows:
            raise DataUnavailableError(f'yfinance 沒有 {symbol.ticker} 的財報資料')
        return pd.DataFrame(rows)
