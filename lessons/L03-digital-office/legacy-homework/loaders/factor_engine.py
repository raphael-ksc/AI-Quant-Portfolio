"""
factor_engine.py
=================
純計算層：給定一檔股票的財務數據（moomoo_loader.get_financials() 回傳的
DataFrame），計算 ROE(TTM) 與三個「Capex 循環」相關比率的趨勢。

本模組不做任何網路請求，方便獨立測試與驗證邏輯。

重要提醒（已知的坑）：
財務科目的比對是用「關鍵字比對 display_name」，因為 Moomoo API 回傳的
欄位命名可能因語系/版本而異。若自動比對失敗（回傳 None），請對照實際
印出的 df.index，在下方 LABEL_KEYWORDS 補上正確關鍵字。

資料方向假設：df 欄位為 period_0, period_1, ... period_N，其中
period_0 為最新一期（與 moomoo_loader.get_financials 的回傳順序一致，
若實測發現順序相反，請對調 iloc 的切片方向）。
"""

from __future__ import annotations

from typing import Optional

import pandas as pd

LABEL_KEYWORDS = {
    "net_income": ["net income", "淨利潤", "净利润"],
    "total_equity": [
        "total equity",
        "shareholders equity",
        "total shareholders",
        "股東權益",
        "股东权益",
    ],
    "revenue": ["total revenue", "operating revenue", "營業收入", "营业收入"],
    "ocf": [
        "operating cash flow",  # Moomoo 實際命名（依 2026-09-06 debug 結果核實）
        "cash flow from operating",
        "net cash from operating",
        "經營活動現金流量淨額",
        "经营活动产生的现金流量净额",
    ],
    "capex": [
        "ppe purchase",  # Moomoo 實際命名：Net PPE Purchase and Sale（依 debug 結果核實）
        "purchase of property",
        "purchases of property",
        "capital expenditure",
        "資本支出",
        "资本支出",
    ],
    "fcf_direct": ["free cash flow"],  # Moomoo 直接提供的現成科目，優先使用
}


def _find_row(df: pd.DataFrame, key: str) -> Optional[pd.Series]:
    """依關鍵字在 df.index（財務科目名稱）中找出對應的列。"""
    for idx in df.index:
        idx_lower = str(idx).lower()
        for kw in LABEL_KEYWORDS[key]:
            if kw.lower() in idx_lower:
                return df.loc[idx]
    return None


def compute_roe_ttm(df: pd.DataFrame) -> Optional[float]:
    """
    ROE (TTM) = 近四季淨利加總 / 近四季平均股東權益

    用「近四季加總」而非「單季 x 4」，避免季節性業務被簡化算法扭曲。
    """
    net_income = _find_row(df, "net_income")
    equity = _find_row(df, "total_equity")
    if net_income is None or equity is None:
        return None

    ni_ttm = pd.to_numeric(net_income.iloc[:4], errors="coerce").sum()
    equity_avg = pd.to_numeric(equity.iloc[:4], errors="coerce").mean()
    if pd.isna(equity_avg) or equity_avg == 0:
        return None
    return float(ni_ttm / equity_avg)


def compute_capex_intensity_series(df: pd.DataFrame) -> Optional[pd.Series]:
    """Capex Intensity = |資本支出| / 營業收入，逐季序列。"""
    capex = _find_row(df, "capex")
    revenue = _find_row(df, "revenue")
    if capex is None or revenue is None:
        return None
    capex = pd.to_numeric(capex, errors="coerce").abs()
    revenue = pd.to_numeric(revenue, errors="coerce")
    return capex / revenue


def compute_ocf_coverage_series(df: pd.DataFrame) -> Optional[pd.Series]:
    """OCF Coverage of Capex = 營運現金流 / |資本支出|，逐季序列。"""
    ocf = _find_row(df, "ocf")
    capex = _find_row(df, "capex")
    if ocf is None or capex is None:
        return None
    ocf = pd.to_numeric(ocf, errors="coerce")
    capex = pd.to_numeric(capex, errors="coerce").abs()
    return ocf / capex


def compute_fcf_margin_series(df: pd.DataFrame) -> Optional[pd.Series]:
    """
    FCF Margin，逐季序列。

    優先使用 Moomoo 直接提供的「Free Cash Flow」科目 / 營業收入
    （較可靠，因為不需要靠關鍵字比對湊出 OCF - Capex）；
    若該科目不存在，才退回用 (OCF - |Capex|) / Revenue 自行計算。
    """
    revenue = _find_row(df, "revenue")
    if revenue is None:
        return None
    revenue = pd.to_numeric(revenue, errors="coerce")

    fcf_direct = _find_row(df, "fcf_direct")
    if fcf_direct is not None:
        fcf_direct = pd.to_numeric(fcf_direct, errors="coerce")
        return fcf_direct / revenue

    ocf = _find_row(df, "ocf")
    capex = _find_row(df, "capex")
    if ocf is None or capex is None:
        return None
    ocf = pd.to_numeric(ocf, errors="coerce")
    capex = pd.to_numeric(capex, errors="coerce").abs()
    return (ocf - capex) / revenue


def trend_direction(series: Optional[pd.Series], periods: int = 4) -> str:
    """
    簡單版趨勢判斷：近 N 季均值 vs 前 N 季均值，變化 > 5% 判定為上升/下降。
    序列假設 index 0（.iloc[0]）為最新一期。
    """
    if series is None:
        return "資料不足"
    series = series.dropna()
    if len(series) < periods * 2:
        return "資料不足"

    recent = series.iloc[:periods].mean()
    prior = series.iloc[periods : periods * 2].mean()
    if pd.isna(prior) or prior == 0 or pd.isna(recent):
        return "資料不足"

    change = (recent - prior) / abs(prior)
    if change > 0.05:
        return "上升"
    if change < -0.05:
        return "下降"
    return "持平"


def evaluate_stock(ticker: str, financials_df: pd.DataFrame, roe_threshold: float = 0.15) -> dict:
    """
    對單一股票計算完整的因子評估結果，並套用篩選條件：
    ROE(TTM) > roe_threshold 且 Capex Intensity 上升 且 OCF Coverage 上升。

    Returns:
        dict，含 ticker / roe_ttm / capex_intensity_trend /
        ocf_coverage_trend / fcf_margin_latest / passed
    """
    roe = compute_roe_ttm(financials_df)
    capex_series = compute_capex_intensity_series(financials_df)
    ocf_series = compute_ocf_coverage_series(financials_df)
    fcf_series = compute_fcf_margin_series(financials_df)

    capex_trend = trend_direction(capex_series)
    ocf_trend = trend_direction(ocf_series)

    fcf_latest = None
    if fcf_series is not None:
        fcf_clean = fcf_series.dropna()
        if not fcf_clean.empty:
            fcf_latest = float(fcf_clean.iloc[0])

    passed = bool(
        roe is not None
        and roe > roe_threshold
        and capex_trend == "上升"
        and ocf_trend == "上升"
    )

    return {
        "ticker": ticker,
        "roe_ttm": roe,
        "capex_intensity_trend": capex_trend,
        "ocf_coverage_trend": ocf_trend,
        "fcf_margin_latest": fcf_latest,
        "passed": passed,
    }
