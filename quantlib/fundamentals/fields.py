"""多候選科目比對（第 4 課 p.46 get_field）：財報長表 → 每期每個指標一個值。

設定檔 config/financial_fields.yaml 依優先順序列出每個指標的候選 (statement, field_id)。
每期逐一嘗試候選，第一個有值的就用；全部找不到則留空，並在 MatchReport 中記錄，不推算、不猜。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd
import yaml

DEFAULT_CONFIG = Path(__file__).resolve().parents[2] / 'config' / 'financial_fields.yaml'


@dataclass(frozen=True)
class MetricSpec:
    name: str
    kind: str                                   # flow / stock
    candidates: tuple[tuple[str, str], ...]     # ((statement, field_id), ...)


@dataclass
class MatchReport:
    """每個指標在各期用了哪個候選、哪些期找不到。"""
    used: dict[str, dict[str, int]] = field(default_factory=dict)      # metric → {"income/8001": 期數}
    missing: dict[str, list[str]] = field(default_factory=dict)        # metric → [期末日]
    aligned: dict[str, list[str]] = field(default_factory=dict)        # 財年期別 → 被統一前的各種期末日

    def as_dict(self) -> dict:
        return {'used': self.used, 'missing': self.missing, 'aligned_period_ends': self.aligned}


def align_period_ends(items: pd.DataFrame, report: MatchReport) -> pd.DataFrame:
    """同一財年期別在不同報表的期末日不一致時（實測：NVDA FY2025 Q1 利潤表 2024-04-27、
    資產負債表與現金流量表 2024-04-28），統一成多數報表採用的日期；同票時取較晚者。修正會記錄在報告中。"""
    if 'fiscal_period' not in items or items['fiscal_period'].isna().any():
        return items
    items = items.copy()
    for fp, g in items.groupby('fiscal_period'):
        votes = g.drop_duplicates(['statement', 'period_end'])['period_end'].value_counts()
        if len(votes) <= 1:
            continue
        top = votes.max()
        canonical = max(d for d, n in votes.items() if n == top)
        report.aligned[str(fp)] = sorted(pd.Timestamp(d).date().isoformat() for d in votes.index)
        items.loc[g.index, 'period_end'] = canonical
    return items


def load_specs(source: str, path: Path = DEFAULT_CONFIG) -> dict[str, MetricSpec]:
    cfg = yaml.safe_load(path.read_text(encoding='utf-8'))['metrics']
    specs = {}
    for name, item in cfg.items():
        if source not in item:
            raise KeyError(f'config/financial_fields.yaml 的 {name} 沒有 {source} 候選科目')
        if item['kind'] not in ('flow', 'stock'):
            raise ValueError(f'{name} 的 kind 只能是 flow / stock')
        specs[name] = MetricSpec(name, item['kind'], tuple((str(s), str(f)) for s, f in item[source]))
    return specs


def resolve(items: pd.DataFrame, specs: dict[str, MetricSpec]) -> tuple[pd.DataFrame, MatchReport]:
    """財報長表（單一標的、單一資料源、單一 freq）→ 寬表：一列一期，欄位為各指標。"""
    if items['symbol'].nunique() != 1 or items['source'].nunique() != 1 or items['freq'].nunique() != 1:
        raise ValueError('resolve() 一次只處理單一標的、單一資料源、單一 freq')
    report = MatchReport()
    items = align_period_ends(items, report)
    lookup = {(r.statement, str(r.field_id), r.period_end): r.value
              for r in items.itertuples(index=False) if pd.notna(r.value)}
    periods = (items[['period_end', 'fiscal_period']].drop_duplicates('period_end')
               .sort_values('period_end').reset_index(drop=True))
    rows = []
    for p in periods.itertuples(index=False):
        row = {'period_end': p.period_end, 'fiscal_period': p.fiscal_period}
        for name, spec in specs.items():
            value = None
            for statement, field_id in spec.candidates:
                value = lookup.get((statement, field_id, p.period_end))
                if value is not None:
                    key = f'{statement}/{field_id}'
                    report.used.setdefault(name, {}).setdefault(key, 0)
                    report.used[name][key] += 1
                    break
            if value is None:
                report.missing.setdefault(name, []).append(pd.Timestamp(p.period_end).date().isoformat())
            row[name] = value
        rows.append(row)
    return pd.DataFrame(rows), report
