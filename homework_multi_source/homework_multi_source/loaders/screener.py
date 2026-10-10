"""
screener.py
===========
協調層：抓板塊成分股 → 逐檔抓財務數據 → 呼叫 factor_engine 計算 → 篩選排序。

不重寫抓資料邏輯，直接沿用 moomoo_loader 既有的 get_plate_stocks /
get_financials，維持「不重複造輪子」原則。
"""

from __future__ import annotations

import time

import pandas as pd

from . import factor_engine, moomoo_loader

DEFAULT_MAX_CANDIDATES = 30
REQUEST_INTERVAL_SEC = 1.5  # 拉長間隔：get_financials 內部已對三張報表各自間隔，
                              # 這裡是「換下一檔股票」前的緩衝，兩者合計降低整體撞到頻率限制的機率


def run_screen(
    plate_keyword: str,
    roe_threshold: float = 0.15,
    max_candidates: int = DEFAULT_MAX_CANDIDATES,
) -> pd.DataFrame:
    """
    執行多因子選股。

    Args:
        plate_keyword: 板塊關鍵字，例如 "semiconductor"
        roe_threshold: ROE 門檻（小數，0.15 = 15%）
        max_candidates: 候選股數量上限（依市值排序取前 N 大）

    Returns:
        DataFrame，每列一檔股票的評估結果，依 fcf_margin_latest 由高到低排序，
        通過篩選（passed=True）的股票排在最前面。
    """
    candidates = moomoo_loader.get_plate_stocks(plate_keyword, max_count=max_candidates)

    results = []
    for code in candidates:
        try:
            financials = moomoo_loader.get_financials(code, num_quarters=8)
            result = factor_engine.evaluate_stock(code, financials, roe_threshold=roe_threshold)
        except Exception as exc:  # noqa: BLE001 — 單檔失敗不應中斷整個篩選
            result = {
                "ticker": code,
                "roe_ttm": None,
                "capex_intensity_trend": "抓取失敗",
                "ocf_coverage_trend": "抓取失敗",
                "fcf_margin_latest": None,
                "passed": False,
                "error": str(exc),
            }
        results.append(result)
        time.sleep(REQUEST_INTERVAL_SEC)

    df = pd.DataFrame(results)
    if df.empty:
        return df

    df = df.sort_values(
        by=["passed", "fcf_margin_latest"], ascending=[False, False], na_position="last"
    )
    return df.reset_index(drop=True)
