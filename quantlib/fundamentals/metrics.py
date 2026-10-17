"""衍生財務指標：單季值 → 近四季合計（TTM）→ 比率。

課程（第 4 課 p.46–47）：優先取現成值，沒有則自行計算；safe_divide 處理分母為 0。
本專案補充：
- 季報的流量科目（營收、淨利、現金流）是單季值，比率改用「近四季合計」較穩定，也和年報口徑一致
- 近四季合計只在「連續 4 季都有值」時計算；中間缺一季就留空，不用 3 季外推
- 期末時點科目（資產、負債、權益）不加總
- 比率一律存成小數（0.25 = 25%），課程相容 VIEW 再換算成百分比
"""
from __future__ import annotations

import math

import pandas as pd

FLOW_TTM = ('revenue', 'gross_profit', 'net_income', 'ocf', 'capex', 'fcf')
QUARTER_GAP_DAYS = (80, 100)   # 相鄰兩季期末日的合理間隔（容許 52/53 週財年）


def safe_divide(num, den, *, positive_den: bool = False):
    """num / den；任一缺值、分母為 0（或要求正分母但 ≤ 0）時回傳 None。"""
    if num is None or den is None or _isnan(num) or _isnan(den):
        return None
    if den == 0 or (positive_den and den <= 0):
        return None
    return num / den


def _isnan(x) -> bool:
    return isinstance(x, float) and math.isnan(x)


def _consecutive(ends: list[pd.Timestamp]) -> bool:
    gaps = [(b - a).days for a, b in zip(ends, ends[1:])]
    return all(QUARTER_GAP_DAYS[0] <= g <= QUARTER_GAP_DAYS[1] for g in gaps)


def add_ttm(wide: pd.DataFrame) -> pd.DataFrame:
    """在寬表（一列一季，依期末日排序）加上 *_ttm 欄位。"""
    df = wide.sort_values('period_end').reset_index(drop=True).copy()
    ends = list(pd.to_datetime(df['period_end']))
    for col in FLOW_TTM:
        out = []
        for i in range(len(df)):
            if i < 3 or not _consecutive(ends[i - 3:i + 1]):
                out.append(None)
                continue
            window = df[col].iloc[i - 3:i + 1].tolist()
            out.append(None if any(v is None or _isnan(v) for v in window) else float(sum(window)))
        df[f'{col}_ttm'] = out
    return df


def add_ratios(df: pd.DataFrame) -> pd.DataFrame:
    """比率（小數）。ROE 在股東權益 ≤ 0 時留空：負權益下的 ROE 沒有意義。"""
    df = df.copy()

    def col(row, name):
        v = row.get(name)
        return None if v is None or _isnan(v) else v

    rows = []
    for _, r in df.iterrows():
        rows.append({
            'roe_ttm': safe_divide(col(r, 'net_income_ttm'), col(r, 'total_equity'), positive_den=True),
            'roa_ttm': safe_divide(col(r, 'net_income_ttm'), col(r, 'total_assets'), positive_den=True),
            'gross_margin_ttm': safe_divide(col(r, 'gross_profit_ttm'), col(r, 'revenue_ttm'), positive_den=True),
            'net_margin_ttm': safe_divide(col(r, 'net_income_ttm'), col(r, 'revenue_ttm'), positive_den=True),
            'fcf_margin_ttm': safe_divide(col(r, 'fcf_ttm'), col(r, 'revenue_ttm'), positive_den=True),
            # 盈餘品質（第 4 課 p.45）：營運現金流 ÷ 淨利；淨利 ≤ 0 時比值沒有意義，留空
            'ocf_to_ni_ttm': safe_divide(col(r, 'ocf_ttm'), col(r, 'net_income_ttm'), positive_den=True),
            'debt_ratio': safe_divide(col(r, 'total_liabilities'), col(r, 'total_assets'), positive_den=True),
            'current_ratio': safe_divide(col(r, 'current_assets'), col(r, 'current_liabilities'), positive_den=True),
            'gross_margin_q': safe_divide(col(r, 'gross_profit'), col(r, 'revenue'), positive_den=True),
            'net_margin_q': safe_divide(col(r, 'net_income'), col(r, 'revenue'), positive_den=True),
        })
    return pd.concat([df, pd.DataFrame(rows, index=df.index)], axis=1)
