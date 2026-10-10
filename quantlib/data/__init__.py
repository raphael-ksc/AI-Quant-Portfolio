"""資料層：統一介面的多資料源（Moomoo 研究用、yfinance 公開重現用）。

用法：
    from quantlib.data import get_source, get_symbol
    with get_source('moomoo') as src:
        bars = src.get_daily_bars(get_symbol('PLTR'), date(2025, 1, 1), date(2025, 12, 31))
"""
from .base import DataSource, DataSourceError, DataUnavailableError
from .schema import SchemaError, validate_bars, validate_financials
from .symbols import Symbol, get_symbol, load_symbols

__all__ = [
    'DataSource', 'DataSourceError', 'DataUnavailableError', 'SchemaError', 'Symbol',
    'get_source', 'get_symbol', 'load_symbols', 'validate_bars', 'validate_financials',
]


def get_source(name: str, **kwargs) -> DataSource:
    """依名稱建立資料源；moomoo 需 OpenD 已啟動。"""
    if name == 'moomoo':
        from .moomoo_source import MoomooSource
        return MoomooSource(**kwargs)
    if name == 'yfinance':
        from .yfinance_source import YFinanceSource
        return YFinanceSource(**kwargs)
    raise ValueError(f'未知的資料源：{name}（可用：moomoo、yfinance）')
