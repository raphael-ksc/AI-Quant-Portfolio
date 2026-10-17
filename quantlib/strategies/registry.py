"""策略外掛機制（第 5 課 p.57–60「動態策略插件」）。

規範：strategies/ 底下每個策略檔案都要有
    STRATEGY_META = {'name', 'category', 'desc', 'params', 'logic'}
    class Strategy(bt.Strategy)
新增策略時只要放一個檔案進來，load_strategies() 就會自動載入，不需要改其他程式。
"""
from __future__ import annotations

import importlib
import pkgutil
from dataclasses import dataclass

REQUIRED_META = ('name', 'category', 'desc', 'params', 'logic')
SKIP = {'registry', 'buy_and_hold'}


class StrategySpecError(ValueError):
    """策略檔案不符合外掛規範。"""


@dataclass(frozen=True)
class StrategySpec:
    key: str          # 模組名稱，例如 double_ma
    meta: dict
    cls: type


def _declared_params(cls) -> dict:
    return {name: getattr(cls.params, name) for name in cls.params._getkeys()}


def _spec(module, key: str) -> StrategySpec:
    meta = getattr(module, 'STRATEGY_META', None)
    cls = getattr(module, 'Strategy', None)
    if not isinstance(meta, dict) or cls is None:
        raise StrategySpecError(f'{key} 缺少 STRATEGY_META 或 Strategy 類別')
    missing = [k for k in REQUIRED_META if k not in meta]
    if missing:
        raise StrategySpecError(f'{key} 的 STRATEGY_META 缺少欄位：{missing}')
    if meta['params'] != _declared_params(cls):
        raise StrategySpecError(f'{key} 的 STRATEGY_META.params 與 Strategy.params 不一致')
    return StrategySpec(key, meta, cls)


def load_strategies(package: str = 'quantlib.strategies') -> dict[str, StrategySpec]:
    """掃描套件內的策略模組，依檔名排序回傳。"""
    pkg = importlib.import_module(package)
    specs = {}
    for info in sorted(pkgutil.iter_modules(pkg.__path__), key=lambda i: i.name):
        if info.name.startswith('_') or info.name in SKIP:
            continue
        module = importlib.import_module(f'{package}.{info.name}')
        specs[info.name] = _spec(module, info.name)
    return specs
