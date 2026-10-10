"""統一資料格式與驗證。

所有資料源（Moomoo、yfinance）都必須輸出以下三種表，下游（資料庫、回測、因子）只認這個格式：

- 日線 DAILY_COLUMNS：一列一個交易日，`date` 為交易所當地日期（不含時區）
- 分鐘線 MINUTE_COLUMNS：一列一根 K 棒，`ts` 為 K 棒結束時間（帶交易所時區）
- 財報 FINANCIAL_COLUMNS：長表，一列 = 一個科目在一期的數值

財報的 `period_end` 是「報告期結束日」，不是公告日；`announce_date` 目前資料源都不提供，
留空並由使用端負責避免前視偏差（Look-ahead Bias）。
"""
from __future__ import annotations

import pandas as pd

DAILY_COLUMNS = ['symbol', 'date', 'open', 'high', 'low', 'close', 'volume',
                 'adjust', 'currency', 'source']
MINUTE_COLUMNS = ['symbol', 'ts', 'open', 'high', 'low', 'close', 'volume',
                  'adjust', 'currency', 'source']
FINANCIAL_COLUMNS = ['symbol', 'source', 'statement', 'field_id', 'name', 'period_end',
                     'fiscal_period', 'freq', 'value', 'currency', 'announce_date']

STATEMENTS = ('income', 'balance', 'cashflow')
FREQS = ('Q', 'A')
ADJUSTS = ('qfq', 'none')
SOURCES = ('moomoo', 'yfinance')


class SchemaError(ValueError):
    """資料不符合統一格式。"""


def _require_columns(df: pd.DataFrame, columns: list[str], kind: str) -> None:
    missing = [c for c in columns if c not in df.columns]
    if missing:
        raise SchemaError(f'{kind} 缺少欄位：{missing}')


def _single_value_per_symbol(df: pd.DataFrame, column: str, kind: str) -> None:
    counts = df.groupby('symbol')[column].nunique()
    bad = counts[counts > 1]
    if not bad.empty:
        raise SchemaError(f'{kind} 同一標的出現多個 {column}：{bad.index.tolist()}（不同幣別不可混用）')


def validate_bars(df: pd.DataFrame, kind: str = 'daily') -> pd.DataFrame:
    """驗證 K 線；通過時回傳依時間排序、只保留標準欄位的副本。"""
    columns = DAILY_COLUMNS if kind == 'daily' else MINUTE_COLUMNS
    time_col = 'date' if kind == 'daily' else 'ts'
    _require_columns(df, columns, f'{kind} K 線')
    if df.empty:
        raise SchemaError(f'{kind} K 線為空')

    price = df[['open', 'high', 'low', 'close']]
    if price.isna().any().any():
        raise SchemaError(f'{kind} K 線的 OHLC 有缺值')
    if (df['high'] < price.max(axis=1) - 1e-9).any() or (df['low'] > price.min(axis=1) + 1e-9).any():
        raise SchemaError(f'{kind} K 線的 high/low 不合理（high 必須最高、low 必須最低）')
    if (df['volume'] < 0).any():
        raise SchemaError(f'{kind} K 線的成交量為負')
    if not set(df['adjust']).issubset(ADJUSTS):
        raise SchemaError(f'adjust 只能是 {ADJUSTS}')
    if not set(df['source']).issubset(SOURCES):
        raise SchemaError(f'source 只能是 {SOURCES}')
    if df.duplicated(['symbol', time_col]).any():
        raise SchemaError(f'{kind} K 線有重複的時間點')
    if kind == 'minute' and getattr(df['ts'].dt, 'tz', None) is None:
        raise SchemaError('分鐘線的 ts 必須帶時區')
    _single_value_per_symbol(df, 'currency', f'{kind} K 線')
    return df[columns].sort_values(['symbol', time_col]).reset_index(drop=True)


def validate_financials(df: pd.DataFrame) -> pd.DataFrame:
    """驗證財報長表；通過時回傳排序後、只保留標準欄位的副本。"""
    _require_columns(df, FINANCIAL_COLUMNS, '財報')
    if df.empty:
        raise SchemaError('財報為空')
    if not set(df['statement']).issubset(STATEMENTS):
        raise SchemaError(f'statement 只能是 {STATEMENTS}')
    if not set(df['freq']).issubset(FREQS):
        raise SchemaError(f'freq 只能是 {FREQS}')
    if df['period_end'].isna().any():
        raise SchemaError('財報的 period_end 有缺值')
    # field_id 只在同一張報表內唯一（Moomoo 的 8017 在利潤表與現金流量表代表不同科目）
    key = ['symbol', 'source', 'statement', 'field_id', 'period_end', 'freq']
    if df.duplicated(key).any():
        dup = df[df.duplicated(key, keep=False)][key].head(3).to_dict('records')
        raise SchemaError(f'財報同一 (報表, 科目, 期別) 重複：{dup}')
    _single_value_per_symbol(df, 'currency', '財報')
    return df[FINANCIAL_COLUMNS].sort_values(
        ['symbol', 'statement', 'period_end', 'field_id']).reset_index(drop=True)
