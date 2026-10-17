"""MySQL 存取層：所有 SQL 集中在這裡，上層（ingest.py）只呼叫方法。

寫入一律用 executemany + ON DUPLICATE KEY UPDATE（第 4 課 p.41 批次寫入），重複執行不會產生重複資料。
使用 MySQL 8.0.19+ 的 `AS new` 別名寫法（`VALUES()` 函式在 8.0.20 起已被標為棄用）。
"""
from __future__ import annotations

import datetime as dt
import math
import re
from pathlib import Path
from typing import Iterable

import pandas as pd

from ..data.symbols import Symbol

SCHEMA_FILE = Path(__file__).resolve().parents[2] / 'db' / 'schema.sql'
BATCH_SIZE = 1000
PRICE_DECIMALS = 6

BAR_COLUMNS = ('symbol', 'trade_date', 'adjust', 'source', 'open', 'high', 'low', 'close',
               'volume', 'amount', 'turnover_rate', 'currency', 'run_id')
UPSERT_BARS = (
    f'INSERT INTO market_daily ({", ".join(BAR_COLUMNS)}) '
    f'VALUES ({", ".join(["%s"] * len(BAR_COLUMNS))}) AS new '
    'ON DUPLICATE KEY UPDATE open=new.open, high=new.high, low=new.low, '
    'close=new.close, volume=new.volume, amount=new.amount, '
    'turnover_rate=new.turnover_rate, currency=new.currency, run_id=new.run_id'
)
UPSERT_INSTRUMENT = (
    'INSERT INTO instruments (symbol, name_en, name_zh, exchange, currency, timezone, '
    'moomoo_code, yfinance_code) VALUES (%s, %s, %s, %s, %s, %s, %s, %s) AS new '
    'ON DUPLICATE KEY UPDATE name_en=new.name_en, name_zh=new.name_zh, '
    'exchange=new.exchange, currency=new.currency, timezone=new.timezone, '
    'moomoo_code=new.moomoo_code, yfinance_code=new.yfinance_code'
)


def split_sql(script: str) -> list[str]:
    """把 schema.sql 拆成單一陳述式（先去掉 -- 註解，再以行尾分號切分）。"""
    no_comments = re.sub(r'--[^\n]*', '', script)
    return [s.strip() for s in re.split(r';\s*(?:\n|$)', no_comments) if s.strip()]


def _clean(value, decimals: int | None = None):
    """NaN → None（寫入 NULL）；浮點數四捨五入到資料表精度。"""
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return None
    if decimals is not None:
        return round(float(value), decimals)
    return value


def bars_to_rows(bars: pd.DataFrame, run_id: int | None) -> list[tuple]:
    """統一格式的日線 DataFrame → executemany 用的 tuple 清單。"""
    rows = []
    has_amount, has_turnover = 'amount' in bars, 'turnover_rate' in bars
    for r in bars.itertuples(index=False):
        rows.append((
            r.symbol, pd.Timestamp(r.date).date(), r.adjust, r.source,
            _clean(r.open, PRICE_DECIMALS), _clean(r.high, PRICE_DECIMALS),
            _clean(r.low, PRICE_DECIMALS), _clean(r.close, PRICE_DECIMALS),
            _clean(r.volume, 4),
            _clean(r.amount, 4) if has_amount else None,
            _clean(r.turnover_rate, 8) if has_turnover else None,
            r.currency, run_id,
        ))
    return rows


class MySQLRepository:
    def __init__(self, conn):
        self.conn = conn

    # ---------- 結構 ----------

    def apply_schema(self, script: str | None = None) -> int:
        statements = split_sql(script if script is not None else SCHEMA_FILE.read_text(encoding='utf-8'))
        with self.conn.cursor() as cur:
            for stmt in statements:
                cur.execute(stmt)
        self.conn.commit()
        return len(statements)

    def upsert_instruments(self, symbols: Iterable[Symbol]) -> None:
        rows = [(s.ticker, s.name_en, s.name_zh, s.exchange, s.currency, s.timezone,
                 s.moomoo, s.yfinance) for s in symbols]
        with self.conn.cursor() as cur:
            cur.executemany(UPSERT_INSTRUMENT, rows)
        self.conn.commit()

    # ---------- 寫入紀錄 ----------

    def start_run(self, job: str, source: str, mode: str, symbols: list[str]) -> int:
        with self.conn.cursor() as cur:
            cur.execute('INSERT INTO ingest_runs (job, source, mode, symbols) VALUES (%s, %s, %s, %s)',
                        (job, source, mode, ','.join(symbols)[:1000]))
            run_id = cur.lastrowid
        self.conn.commit()
        return run_id

    def finish_run(self, run_id: int, status: str, rows_written: int, message: str | None = None) -> None:
        with self.conn.cursor() as cur:
            cur.execute('UPDATE ingest_runs SET status=%s, rows_written=%s, message=%s, '
                        'finished_at=CURRENT_TIMESTAMP WHERE run_id=%s',
                        (status, rows_written, message, run_id))
        self.conn.commit()

    # ---------- 日線 ----------

    def latest_dates(self, source: str, adjust: str, n: int) -> dict[str, tuple[dt.date, dt.date]]:
        """一條 SQL 查出每檔的（最新日期, 倒數第 n 個日期）。"""
        sql = (
            'SELECT symbol, MAX(trade_date), MIN(trade_date) FROM ('
            '  SELECT symbol, trade_date, ROW_NUMBER() OVER '
            '    (PARTITION BY symbol ORDER BY trade_date DESC) AS rn'
            '  FROM market_daily WHERE source=%s AND adjust=%s'
            ') t WHERE rn <= %s GROUP BY symbol'
        )
        with self.conn.cursor() as cur:
            cur.execute(sql, (source, adjust, n))
            return {sym: (latest, nth) for sym, latest, nth in cur.fetchall()}

    def load_closes(self, symbol: str, source: str, adjust: str, start: dt.date) -> pd.DataFrame:
        with self.conn.cursor() as cur:
            cur.execute('SELECT trade_date, close FROM market_daily WHERE symbol=%s AND source=%s '
                        'AND adjust=%s AND trade_date >= %s ORDER BY trade_date',
                        (symbol, source, adjust, start))
            rows = cur.fetchall()
        return pd.DataFrame({'date': pd.to_datetime([r[0] for r in rows]),
                             'close': [float(r[1]) for r in rows]})

    def load_bars(self, symbol: str, start: dt.date, end: dt.date, *, source: str = 'moomoo',
                  adjust: str = 'qfq') -> pd.DataFrame:
        """讀回統一格式的日線（給回測使用），start 與 end 皆包含。"""
        with self.conn.cursor() as cur:
            cur.execute('SELECT trade_date, open, high, low, close, volume, currency FROM market_daily '
                        'WHERE symbol=%s AND source=%s AND adjust=%s AND trade_date BETWEEN %s AND %s '
                        'ORDER BY trade_date', (symbol, source, adjust, start, end))
            rows = cur.fetchall()
        if not rows:
            raise LookupError(f'market_daily 沒有 {symbol}（{source}/{adjust}）{start}～{end} 的資料，請先跑 C06')
        df = pd.DataFrame(rows, columns=['date', 'open', 'high', 'low', 'close', 'volume', 'currency'])
        df['date'] = pd.to_datetime(df['date'])
        for c in ('open', 'high', 'low', 'close', 'volume'):
            df[c] = df[c].astype(float)
        df['symbol'], df['adjust'], df['source'] = symbol, adjust, source
        return df

    def earliest_date(self, symbol: str, source: str, adjust: str) -> dt.date | None:
        with self.conn.cursor() as cur:
            cur.execute('SELECT MIN(trade_date) FROM market_daily WHERE symbol=%s AND source=%s AND adjust=%s',
                        (symbol, source, adjust))
            return cur.fetchone()[0]

    def upsert_bars(self, bars: pd.DataFrame, run_id: int | None, *, replace: bool = False) -> int:
        """寫入日線；replace=True 時先刪除該 (symbol, source, adjust) 全部舊資料（同一交易內）。"""
        rows = bars_to_rows(bars, run_id)
        try:
            with self.conn.cursor() as cur:
                if replace:
                    for sym, src, adj in {(r[0], r[3], r[2]) for r in rows}:
                        cur.execute('DELETE FROM market_daily WHERE symbol=%s AND source=%s AND adjust=%s',
                                    (sym, src, adj))
                for i in range(0, len(rows), BATCH_SIZE):
                    cur.executemany(UPSERT_BARS, rows[i:i + BATCH_SIZE])
            self.conn.commit()
        except Exception:
            self.conn.rollback()
            raise
        return len(rows)

    def summary(self) -> list[dict]:
        """每檔、每種復權、每個資料源的筆數與日期範圍（給 metrics.json，不含價格）。"""
        with self.conn.cursor() as cur:
            cur.execute('SELECT symbol, adjust, source, COUNT(*), MIN(trade_date), MAX(trade_date), '
                        'SUM(amount IS NULL), SUM(turnover_rate IS NULL) FROM market_daily '
                        'GROUP BY symbol, adjust, source ORDER BY symbol, adjust, source')
            keys = ('symbol', 'adjust', 'source', 'rows', 'first', 'last', 'null_amount', 'null_turnover')
            return [dict(zip(keys, r)) for r in cur.fetchall()]
