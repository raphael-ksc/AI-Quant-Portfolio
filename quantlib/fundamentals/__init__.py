"""基本面：財報科目比對、近四季合計與比率、財報可交易日（防前視偏差）。

用法：
    from quantlib.fundamentals import ingest_financials
    from quantlib.data.edgar import EdgarClient
    summary = ingest_financials(MySQLRepository(conn), source, symbols, edgar=EdgarClient())
"""
from .availability import Availability, availability, match_filing
from .fields import MatchReport, MetricSpec, load_specs, resolve
from .ingest import build_metrics, ingest_financials
from .metrics import add_ratios, add_ttm, safe_divide

__all__ = [
    'Availability', 'MatchReport', 'MetricSpec', 'add_ratios', 'add_ttm', 'availability', 'build_metrics',
    'ingest_financials', 'load_specs', 'match_filing', 'resolve', 'safe_divide',
]
