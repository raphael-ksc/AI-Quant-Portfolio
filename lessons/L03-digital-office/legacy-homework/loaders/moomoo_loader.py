"""
moomoo_loader.py
=================
使用 Moomoo OpenAPI（moomoo-api 套件）抓取美股（US.PLTR、US.IREN）的
日線、分鐘線、季度財務數據。

前置條件（Prerequisites）：
1. Moomoo OpenD 已在本機啟動並成功登入（畫面顯示 Connected）
2. 已執行 `pip install moomoo-api`

重要提醒（坑，Known Pitfalls）：
- get_financials_statements() 回傳的欄位命名，官方文件與實際回傳可能不完全一致，
  第一次執行時務必先 print(df.columns) 確認實際欄位名稱，再往下游接。
- 歷史 K 線額度（history kline quota）每 30 天有上限，正式使用前建議先呼叫
  quote_ctx.get_history_kl_quota() 確認額度是否足夠。
- 本模組僅示範「抓取」，不涉及下單／交易，安全性較高，但仍建議用完就
  呼叫 quote_ctx.close() 釋放連線。
"""

from __future__ import annotations

import datetime as dt
import time
from dataclasses import dataclass

import pandas as pd

try:
    import moomoo as ft
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        "找不到 moomoo 套件，請先執行：pip install moomoo-api"
    ) from exc


# ------------------------------------------------------------------
# 連線設定
# ------------------------------------------------------------------
OPEND_HOST = "127.0.0.1"
OPEND_PORT = 11111


@dataclass
class MoomooLoaderError(Exception):
    """Moomoo 資料抓取過程中發生的錯誤，統一包裝方便上層判斷。"""

    message: str

    def __str__(self) -> str:  # pragma: no cover
        return self.message


def _get_quote_ctx() -> "ft.OpenQuoteContext":
    """建立並回傳一個 OpenQuoteContext。呼叫端用完務必 close()。"""
    return ft.OpenQuoteContext(host=OPEND_HOST, port=OPEND_PORT)


def check_connection() -> bool:
    """快速檢查 OpenD 是否可連通，回傳 True/False，不拋例外。"""
    ctx = _get_quote_ctx()
    try:
        ret, _data = ctx.get_global_state()
        return ret == ft.RET_OK
    finally:
        ctx.close()


def check_quota() -> dict:
    """查詢目前歷史 K 線額度使用狀況，避免超額。"""
    ctx = _get_quote_ctx()
    try:
        ret, data = ctx.get_history_kl_quota(get_detail=False)
        if ret != ft.RET_OK:
            raise MoomooLoaderError(f"查詢額度失敗：{data}")
        return data.to_dict(orient="records")[0] if not data.empty else {}
    finally:
        ctx.close()


def get_daily_kline(code: str, start: str, end: str) -> pd.DataFrame:
    """
    抓取日線資料。

    Args:
        code: Moomoo 格式股票代碼，例如 "US.PLTR"、"US.IREN"
        start: 起始日期 "YYYY-MM-DD"
        end:   結束日期 "YYYY-MM-DD"

    Returns:
        DataFrame，欄位：date, open, high, low, close, volume
    """
    ctx = _get_quote_ctx()
    try:
        ret, data, _page_req_key = ctx.request_history_kline(
            code,
            start=start,
            end=end,
            ktype=ft.KLType.K_DAY,
            autype=ft.AuType.QFQ,  # 前復權
            max_count=1000,
        )
        if ret != ft.RET_OK:
            raise MoomooLoaderError(f"抓取 {code} 日線失敗：{data}")

        df = data.rename(
            columns={
                "time_key": "date",
                "open": "open",
                "high": "high",
                "low": "low",
                "close": "close",
                "volume": "volume",
            }
        )[["date", "open", "high", "low", "close", "volume"]]
        df["date"] = pd.to_datetime(df["date"])
        return df
    finally:
        ctx.close()


def get_minute_kline(code: str, start: str, end: str) -> pd.DataFrame:
    """
    抓取分鐘線資料（1 分鐘 K 線）。

    注意：Moomoo 歷史 K 線額度每 30 天限量，抓分鐘線消耗額度較快，
    建議先用較短的區間測試（例如近 5 個交易日）。
    """
    ctx = _get_quote_ctx()
    try:
        ret, data, _page_req_key = ctx.request_history_kline(
            code,
            start=start,
            end=end,
            ktype=ft.KLType.K_1M,
            autype=ft.AuType.QFQ,
            max_count=1000,
        )
        if ret != ft.RET_OK:
            raise MoomooLoaderError(f"抓取 {code} 分鐘線失敗：{data}")

        df = data.rename(columns={"time_key": "datetime"})[
            ["datetime", "open", "high", "low", "close", "volume"]
        ]
        df["datetime"] = pd.to_datetime(df["datetime"])
        return df
    finally:
        ctx.close()


def get_financials(code: str, num_quarters: int = 8) -> pd.DataFrame:
    """
    抓取季度財務報表數據（近 num_quarters 季）。

    重要：get_financials_statements 的實際回傳欄位，第一次執行請務必
    print(df.columns) 核對，官方文件與實際欄位命名可能有落差
    （此為前面課程已知的坑）。

    Args:
        code: Moomoo 格式股票代碼，例如 "US.PLTR"
        num_quarters: 想取得的季度數量，預設 8（近 2 年）

    官方函式簽名（已依 openapi.futunn.com 文件核實，2026-09-06）：
        get_financials_statements(code, statement_type=None, financial_type=None,
                                   currency_code=None, next_key=None, num=None)
        statement_type：1=Income(利潤表) 2=BalanceSheet(資產負債表)
                        3=CashFlow(現金流量表) 4=MainIndex(關鍵指標)
        financial_type：9=單季報組合（我們要的「每季一筆」資料用這個）

    回傳的 data 是 dict，結構為：
        data['report_list'] = [
            { ...期別資訊..., 'item_list': [{field_id, display_name, data, yoy, qoq}, ...] },
            ...
        ]
    本函式會把 income/balance sheet/cash flow 三張報表都抓回來，
    合併成「列 = 財務科目，欄 = 各期」的寬表，方便網頁端顯示。

    Returns:
        DataFrame，index 為科目顯示名稱，欄位為各期序號（0 = 最新一期）
    """
    STATEMENT_TYPES = {"Income": 1, "BalanceSheet": 2, "CashFlow": 3}
    FINANCIAL_TYPE_SINGLE_QUARTER = 9
    MAX_RETRIES = 3
    RETRY_WAIT_SEC = 5
    BETWEEN_CALLS_SEC = 1.0  # 三張報表之間也要間隔，避免瞬間打三次請求

    ctx = _get_quote_ctx()
    try:
        all_rows: dict[str, list] = {}
        num_periods = 0

        for stmt_name, stmt_code in STATEMENT_TYPES.items():
            data = None
            for attempt in range(1, MAX_RETRIES + 1):
                ret, resp = ctx.get_financials_statements(
                    code,
                    statement_type=stmt_code,
                    financial_type=FINANCIAL_TYPE_SINGLE_QUARTER,
                    num=num_quarters,
                )
                if ret == ft.RET_OK:
                    data = resp
                    break
                # 頻率限制通常會在錯誤訊息中提到 frequency / rate limit / too many
                is_rate_limit = any(
                    kw in str(resp).lower() for kw in ["frequency", "rate limit", "too many", "40012"]
                )
                if is_rate_limit and attempt < MAX_RETRIES:
                    time.sleep(RETRY_WAIT_SEC)
                    continue
                raise MoomooLoaderError(f"抓取 {code} {stmt_name} 失敗：{resp}")

            report_list = data.get("report_list", [])
            num_periods = max(num_periods, len(report_list))

            for period_idx, report in enumerate(report_list):
                for item in report.get("item_list", []):
                    label = f"[{stmt_name}] {item.get('display_name', item.get('field_id'))}"
                    all_rows.setdefault(label, [None] * num_periods)
                    while len(all_rows[label]) < num_periods:
                        all_rows[label].append(None)
                    all_rows[label][period_idx] = item.get("data")

            time.sleep(BETWEEN_CALLS_SEC)

        df = pd.DataFrame.from_dict(
            all_rows, orient="index", columns=[f"period_{i}" for i in range(num_periods)]
        )
        return df
    finally:
        ctx.close()


def get_plate_stocks(plate_keyword: str, market=None, max_count: int = 30) -> list[str]:
    """
    依板塊關鍵字（不分大小寫、部分比對）尋找板塊，回傳依市值排序的
    前 max_count 檔股票代碼（預設市場：美股）。

    Args:
        plate_keyword: 板塊名稱關鍵字，例如 "semiconductor"、"artificial intelligence"
        market: ft.Market 列舉，預設 ft.Market.US
        max_count: 回傳股票數量上限

    Returns:
        股票代碼清單，例如 ["US.NVDA", "US.AVGO", ...]
    """
    if market is None:
        market = ft.Market.US

    ctx = _get_quote_ctx()
    try:
        ret, plates = ctx.get_plate_list(market, ft.Plate.ALL)
        if ret != ft.RET_OK:
            raise MoomooLoaderError(f"取得板塊清單失敗：{plates}")

        matched = plates[plates["plate_name"].str.contains(plate_keyword, case=False, na=False)]
        if matched.empty:
            raise MoomooLoaderError(
                f"找不到符合關鍵字「{plate_keyword}」的板塊。"
                f"若確定板塊存在，可能是命名不同，建議先印出 plates['plate_name'] 核對實際名稱。"
            )

        plate_code = matched.iloc[0]["code"]
        ret, stocks = ctx.get_plate_stock(plate_code)
        if ret != ft.RET_OK:
            raise MoomooLoaderError(f"取得板塊成分股失敗：{stocks}")

        if "market_val" in stocks.columns:
            stocks = stocks.sort_values("market_val", ascending=False)

        return stocks["code"].head(max_count).tolist()
    finally:
        ctx.close()


if __name__ == "__main__":
    # 快速自我測試：確認連線、抓一小段 PLTR 日線
    print("檢查連線：", check_connection())
    print("額度狀況：", check_quota())

    end = dt.date.today().isoformat()
    start = (dt.date.today() - dt.timedelta(days=30)).isoformat()
    df = get_daily_kline("US.PLTR", start, end)
    print(df.tail())
