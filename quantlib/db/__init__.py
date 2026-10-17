"""資料庫層：MySQL `quant_portfolio`（本機 MySQL80 :3306 或 Docker :3307）。

用法：
    from quantlib.db import DbConfig, MySQLRepository, ingest_daily
    cfg = DbConfig.from_env()            # 讀 Project/.env
    with cfg.connect() as conn:
        summary = ingest_daily(MySQLRepository(conn), source, symbols)
"""
from .config import DbConfig, DbConfigError
from .ingest import ingest_daily
from .planner import FetchPlan, MarketHours, last_closed_session, needs_refresh, plan_fetch
from .repository import MySQLRepository, bars_to_rows, split_sql

__all__ = [
    'DbConfig', 'DbConfigError', 'FetchPlan', 'MarketHours', 'MySQLRepository', 'bars_to_rows',
    'ingest_daily', 'last_closed_session', 'needs_refresh', 'plan_fetch', 'split_sql',
]
