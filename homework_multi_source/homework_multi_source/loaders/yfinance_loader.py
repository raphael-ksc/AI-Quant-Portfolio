"""
yfinance_loader.py
===================
使用 yfinance 抓取澳股（BHP.AX）的日線、分鐘線、季度財務數據。

重要提醒（坑，Known Pitfalls）：
- 分鐘線資料 yfinance 官方限制：
    interval="1m"  → 只能抓最近 7 天
    interval="5m"/"15m"/"30m"/"60m" → 只能抓最近 60 天
  超過範圍會直接回傳空的 DataFrame，不會噴錯誤，容易被忽略，
  務必檢查回傳是否為空。
- BHP.AX 是 AUD（澳幣）計價，跟 PLTR/IREN 的 USD 不同，
  不可直接放在同一張價格圖上比較。
- yfinance 沒有官方 SLA，抓取失敗或欄位改變是常見情況，
  建議加上簡單的重試機制。
"""

from __future__ import annotations

import pandas as pd
import yfinance as yf


class YFinanceLoaderError(Exception):
    """yfinance 資料抓取過程中發生的錯誤。"""


def get_daily_kline(ticker: str, start: str, end: str) -> pd.DataFrame:
    """
    抓取日線資料。

    Args:
        ticker: yfinance 格式代碼，例如 "BHP.AX"
        start / end: "YYYY-MM-DD"

    Returns:
        DataFrame，欄位：date, open, high, low, close, volume
    """
    df = yf.download(ticker, start=start, end=end, interval="1d", progress=False)
    if df.empty:
        raise YFinanceLoaderError(f"抓取 {ticker} 日線為空，請確認代碼與日期區間")

    df = df.reset_index()
    # yfinance 新版可能回傳 MultiIndex 欄位，統一攤平
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [c[0] for c in df.columns]

    df = df.rename(
        columns={
            "Date": "date",
            "Open": "open",
            "High": "high",
            "Low": "low",
            "Close": "close",
            "Volume": "volume",
        }
    )[["date", "open", "high", "low", "close", "volume"]]
    return df


def get_minute_kline(ticker: str, period: str = "5d", interval: str = "1m") -> pd.DataFrame:
    """
    抓取分鐘線資料。

    注意：yfinance 對分鐘線的歷史區間有硬性限制（見檔案頂部說明），
    period 建議依 interval 調整：
        interval="1m"  → period 最多 "7d"
        interval="5m"  → period 最多 "60d"
    """
    df = yf.download(ticker, period=period, interval=interval, progress=False)
    if df.empty:
        raise YFinanceLoaderError(
            f"抓取 {ticker} 分鐘線為空，可能是 period/interval 超出 yfinance 限制"
        )

    df = df.reset_index()
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [c[0] for c in df.columns]

    # 分鐘線的索引欄位在 yfinance 中通常叫 "Datetime"
    time_col = "Datetime" if "Datetime" in df.columns else "Date"
    df = df.rename(
        columns={
            time_col: "datetime",
            "Open": "open",
            "High": "high",
            "Low": "low",
            "Close": "close",
            "Volume": "volume",
        }
    )[["datetime", "open", "high", "low", "close", "volume"]]
    return df


def get_financials(ticker: str, num_quarters: int = 8) -> pd.DataFrame:
    """
    抓取財務數據，優先取季報，若季報為空則自動降級為年報。

    重要背景知識：澳洲（ASX）上市公司的法定財報義務是「半年報 + 年報」，
    不像美股強制季報。因此像 BHP 這類 ASX 標的，Yahoo Finance 上的
    quarterly 欄位經常是空的或資料稀疏，屬於資料源本質限制，並非程式錯誤。
    本函式在偵測到季報為空時，會自動改抓年報，並在回傳資料的
    attrs['granularity'] 標註實際使用的是哪一種，避免呈現時誤導。

    Returns:
        DataFrame，index 為財務科目，欄位為各期日期。
        df.attrs['granularity'] 會是 "quarterly" 或 "annual"。
    """
    tk = yf.Ticker(ticker)

    def _fetch(freq: str) -> pd.DataFrame:
        income = tk.get_income_stmt(freq=freq)
        balance = tk.get_balance_sheet(freq=freq)
        cashflow = tk.get_cashflow(freq=freq)
        if income is None or income.empty:
            return pd.DataFrame()
        combined = pd.concat([income, balance, cashflow], axis=0)
        return combined.iloc[:, :num_quarters]

    combined = _fetch("quarterly")
    granularity = "quarterly"

    if combined.empty:
        # 季報為空（常見於澳股半年報公司），自動降級抓年報
        combined = _fetch("yearly")
        granularity = "annual"

    if combined.empty:
        raise YFinanceLoaderError(
            f"抓取 {ticker} 財務數據為空（季報與年報皆無資料），請確認代碼是否正確"
        )

    combined.attrs["granularity"] = granularity
    return combined


if __name__ == "__main__":
    df = get_daily_kline("BHP.AX", "2025-01-01", "2025-12-31")
    print(df.tail())
