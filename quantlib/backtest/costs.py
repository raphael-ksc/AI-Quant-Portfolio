"""美股交易成本模型：券商佣金 + 平台費 + 賣出時的 SEC 費與 FINRA TAF。

課程（第 5 課 1b-摩擦成本与成交约束.py）是 A 股成本：佣金、印花稅、過戶費。
美股沒有印花稅與過戶費，改成以下四項，費率全部來自 config/costs.yaml：

    佣金     = max(股數 × 每股佣金, 最低佣金)
    平台費   = max(股數 × 每股平台費, 最低平台費)
    SEC 費   = max(成交金額 × 當時費率, 最低收費)      只在賣出、且費率 > 0 時收
    FINRA TAF = min(股數 × 當時每股費率, 單筆上限)      只在賣出時收

監管費率依「成交日期」查表，因為 SEC 費在 2025-05-14 降為 0、2026-04-04 又調升。
"""
from __future__ import annotations

import bisect
import datetime as dt
from dataclasses import dataclass, field
from pathlib import Path

import yaml

DEFAULT_CONFIG = Path(__file__).resolve().parents[2] / 'config' / 'costs.yaml'


@dataclass(frozen=True)
class DatedRate:
    """依生效日分段的費率表；查詢時取「生效日 ≤ 查詢日」的最後一段。"""
    effective: tuple[dt.date, ...]
    values: tuple

    def at(self, day: dt.date):
        i = bisect.bisect_right(self.effective, day) - 1
        if i < 0:
            raise ValueError(f'{day} 早於費率表的第一個生效日 {self.effective[0]}')
        return self.values[i]


@dataclass(frozen=True)
class CostBreakdown:
    commission: float
    platform: float
    sec_fee: float
    taf: float

    @property
    def total(self) -> float:
        return self.commission + self.platform + self.sec_fee + self.taf


@dataclass(frozen=True)
class USEquityCosts:
    profile: str
    commission_per_share: float
    commission_min: float
    platform_per_share: float
    platform_min: float
    regulatory: bool = True
    sec_min: float = 0.01
    sec_rates: DatedRate | None = field(default=None, repr=False)
    taf_rates: DatedRate | None = field(default=None, repr=False)

    @classmethod
    def from_config(cls, profile: str = 'moomoo_reference', path: Path = DEFAULT_CONFIG) -> 'USEquityCosts':
        cfg = yaml.safe_load(path.read_text(encoding='utf-8'))
        if profile not in cfg['profiles']:
            raise KeyError(f'config/costs.yaml 沒有成本設定 {profile}')
        p = cfg['profiles'][profile]
        sec = sorted(cfg['sec_fee']['schedule'], key=lambda r: r['effective'])
        taf = sorted(cfg['finra_taf']['schedule'], key=lambda r: r['effective'])
        return cls(
            profile=profile,
            commission_per_share=float(p['commission_per_share']), commission_min=float(p['commission_min']),
            platform_per_share=float(p['platform_per_share']), platform_min=float(p['platform_min']),
            regulatory=bool(p.get('regulatory', True)), sec_min=float(cfg['sec_fee']['minimum']),
            sec_rates=DatedRate(tuple(r['effective'] for r in sec), tuple(float(r['rate']) for r in sec)),
            taf_rates=DatedRate(tuple(r['effective'] for r in taf),
                                tuple((float(r['per_share']), float(r['cap'])) for r in taf)),
        )

    def breakdown(self, shares: float, price: float, day: dt.date, is_sell: bool) -> CostBreakdown:
        shares = abs(shares)
        if shares == 0:
            return CostBreakdown(0.0, 0.0, 0.0, 0.0)
        commission = max(shares * self.commission_per_share, self.commission_min)
        platform = max(shares * self.platform_per_share, self.platform_min)
        sec_fee = taf = 0.0
        if is_sell and self.regulatory:
            rate = self.sec_rates.at(day)
            if rate > 0:
                sec_fee = max(shares * price * rate, self.sec_min)
            per_share, cap = self.taf_rates.at(day)
            taf = min(shares * per_share, cap)
        return CostBreakdown(commission, platform, sec_fee, taf)
