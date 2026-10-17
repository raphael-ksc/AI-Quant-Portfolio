"""可重用的策略外掛；用 load_strategies() 自動載入（見 registry.py）。"""
from .registry import StrategySpec, StrategySpecError, load_strategies

__all__ = ['StrategySpec', 'StrategySpecError', 'load_strategies']
