"""自選股設定載入：config/symbols.yaml → Symbol。"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

DEFAULT_CONFIG = Path(__file__).resolve().parents[2] / 'config' / 'symbols.yaml'


@dataclass(frozen=True)
class Symbol:
    ticker: str
    name_en: str
    name_zh: str
    exchange: str
    currency: str
    timezone: str
    moomoo: str | None = None
    yfinance: str | None = None

    def code_for(self, source: str) -> str:
        """回傳指定資料源使用的代碼；該資料源不支援此標的時拋 KeyError。"""
        code = getattr(self, source, None)
        if not code:
            raise KeyError(f'{self.ticker} 沒有設定 {source} 代碼')
        return code


def load_symbols(path: Path = DEFAULT_CONFIG) -> dict[str, Symbol]:
    raw = yaml.safe_load(path.read_text(encoding='utf-8'))['symbols']
    return {ticker: Symbol(ticker=ticker, **cfg) for ticker, cfg in raw.items()}


def get_symbol(ticker: str, path: Path = DEFAULT_CONFIG) -> Symbol:
    symbols = load_symbols(path)
    if ticker not in symbols:
        raise KeyError(f'config/symbols.yaml 沒有 {ticker}，請先加入設定')
    return symbols[ticker]
