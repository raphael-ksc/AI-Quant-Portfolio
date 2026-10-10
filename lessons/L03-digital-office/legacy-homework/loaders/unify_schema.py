"""
unify_schema.py
================
把 Moomoo 與 yfinance 兩種來源的資料，統一成同一張表的格式，
並強制標註幣別（currency）與資料源（source），避免下游誤用。

這是整個專案的「防呆層」：所有要進入 present_report 或
notebook 分析的資料，都應該先經過這裡處理。
"""

from __future__ import annotations

import pandas as pd

# 股票代碼 → (資料源, yfinance/moomoo 代碼, 幣別, 顯示名稱)
TICKER_CONFIG = {
    "PLTR": {
        "source": "moomoo",
        "code": "US.PLTR",
        "currency": "USD",
        "name_en": "Palantir Technologies",
        "name_zh": "Palantir 科技",
    },
    "IREN": {
        "source": "moomoo",
        "code": "US.IREN",
        "currency": "USD",
        "name_en": "IREN Limited",
        "name_zh": "IREN Limited",
    },
    "BHP": {
        "source": "yfinance",
        "code": "BHP.AX",
        "currency": "AUD",
        "name_en": "BHP Group",
        "name_zh": "必和必拓（BHP）",
    },
}


def unify_kline(df: pd.DataFrame, ticker: str, timeframe: str) -> pd.DataFrame:
    """
    為 K 線資料補上 ticker / currency / source / timeframe 欄位，
    統一日期欄位命名為 'date'（日線）或 'datetime'（分鐘線）。
    """
    cfg = TICKER_CONFIG[ticker]
    df = df.copy()
    df["ticker"] = ticker
    df["currency"] = cfg["currency"]
    df["source"] = cfg["source"]
    df["timeframe"] = timeframe
    return df


def unify_financials(df: pd.DataFrame, ticker: str) -> pd.DataFrame:
    """為財務數據補上 ticker / currency / source 欄位。"""
    cfg = TICKER_CONFIG[ticker]
    df = df.copy()
    df["ticker"] = ticker
    df["currency"] = cfg["currency"]
    df["source"] = cfg["source"]
    return df


def get_display_name(ticker: str, lang: str = "zh") -> str:
    """依語言回傳標的顯示名稱，lang: 'zh' 或 'en'。"""
    cfg = TICKER_CONFIG[ticker]
    return cfg["name_zh"] if lang == "zh" else cfg["name_en"]
