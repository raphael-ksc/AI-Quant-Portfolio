"""資料源介面：所有資料源實作同一組方法，輸出 schema.py 定義的統一格式。"""
from __future__ import annotations

import datetime as dt
from abc import ABC, abstractmethod

import pandas as pd

from .symbols import Symbol


class DataSourceError(RuntimeError):
    """資料源回傳錯誤（連線失敗、API 錯誤等）。"""


class DataUnavailableError(DataSourceError):
    """資料源本身不提供這段資料（例：yfinance 1 分鐘線只有最近 7 天）。"""


class DataSource(ABC):
    """可當 context manager 使用：with get_source('moomoo') as src: ..."""

    name: str

    @abstractmethod
    def get_daily_bars(self, symbol: Symbol, start: dt.date, end: dt.date,
                       adjust: str = 'qfq') -> pd.DataFrame:
        """日線，start 與 end 皆包含在內。"""

    @abstractmethod
    def get_minute_bars(self, symbol: Symbol, day: dt.date) -> pd.DataFrame:
        """單一交易日的 1 分鐘線，只含正常交易時段。"""

    @abstractmethod
    def get_financials(self, symbol: Symbol, freq: str = 'Q', periods: int = 8) -> pd.DataFrame:
        """財報長表（利潤表、資產負債表、現金流量表），最近 periods 期。"""

    def close(self) -> None:
        """釋放連線；預設不需要。"""

    def __enter__(self):
        return self

    def __exit__(self, *exc) -> None:
        self.close()
