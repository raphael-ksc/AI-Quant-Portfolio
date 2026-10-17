"""C06 行情數據採集：自選股日線 → MySQL `quant_portfolio.market_daily`。

原課程為 QMT（`get_market_data_ex` + 每天 15:30 定時），此處已換成 Moomoo 版本：
    quantlib.data（Moomoo 或 yfinance）→ schema 驗證 → 增量規劃與復權基準比對
    → MySQL（executemany + ON DUPLICATE KEY UPDATE）→ outputs/metrics.json（只含筆數與日期範圍）

用法（Project 根目錄；moomoo 需先啟動並登入 OpenD；MySQL 連線讀 .env）：
    .venv\\Scripts\\python.exe lessons\\L04-data-pipeline\\C06-market-data-collection\\src\\ingest_daily.py --init-schema
    ...\\ingest_daily.py                          # 增量更新（預設：全部自選股、前復權 + 不復權）
    ...\\ingest_daily.py --mode full --symbols PLTR
    ...\\ingest_daily.py --source yfinance        # 任何人都能重現（搭配 docker compose）

⚠️ 僅供教育與研究用途，不構成投資建議。原始行情只存在本機資料庫，不公開。
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from importlib import metadata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

from quantlib.data import get_source, load_symbols  # noqa: E402
from quantlib.db import DbConfig, MySQLRepository, ingest_daily  # noqa: E402
from quantlib.db.planner import DEFAULT_LOOKBACK, DEFAULT_START  # noqa: E402

CHECKIN_DIR = Path(__file__).resolve().parents[1]
METRICS = CHECKIN_DIR / 'outputs' / 'metrics.json'


def parse_args(argv=None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description='C06：自選股日線寫入 MySQL')
    p.add_argument('--source', choices=['moomoo', 'yfinance'], default='moomoo')
    p.add_argument('--mode', choices=['incremental', 'full'], default='incremental')
    p.add_argument('--symbols', nargs='+', help='預設為 config/symbols.yaml 全部標的')
    p.add_argument('--adjust', nargs='+', choices=['qfq', 'none'], default=['qfq', 'none'])
    p.add_argument('--start', type=dt.date.fromisoformat, default=DEFAULT_START,
                   help='沒有歷史資料時的起點（預設 2023-01-01）')
    p.add_argument('--lookback', type=int, default=DEFAULT_LOOKBACK, help='回看比對的已存交易日數')
    p.add_argument('--init-schema', action='store_true', help='建立資料庫（若不存在）並套用 db/schema.sql')
    p.add_argument('--no-metrics', action='store_true', help='不更新 outputs/metrics.json')
    return p.parse_args(argv)


def init_schema(cfg: DbConfig) -> None:
    conn = cfg.connect(with_database=False)
    try:
        with conn.cursor() as cur:
            cur.execute(f'CREATE DATABASE IF NOT EXISTS `{cfg.database}` '
                        'CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci')
        conn.commit()
    finally:
        conn.close()
    with cfg.connect() as conn:
        n = MySQLRepository(conn).apply_schema()
    print(f'已套用 db/schema.sql（{n} 個陳述式）→ {cfg.describe()}')


def write_metrics(repo: MySQLRepository, summary: dict, args: argparse.Namespace) -> None:
    versions = {}
    for pkg in ('moomoo-api', 'yfinance', 'pandas', 'pymysql'):
        try:
            versions[pkg] = metadata.version(pkg)
        except metadata.PackageNotFoundError:
            pass
    tables = [{**r, 'first': r['first'].isoformat(), 'last': r['last'].isoformat(),
               'null_amount': int(r['null_amount']), 'null_turnover': int(r['null_turnover'])}
              for r in repo.summary()]
    METRICS.parent.mkdir(parents=True, exist_ok=True)
    METRICS.write_text(json.dumps({
        'generated_on': dt.date.today().isoformat(),
        'versions': versions,
        'last_run': {
            'source': args.source, 'mode': args.mode, 'status': summary['status'],
            'last_closed_session': summary['last_session'], 'rows_written': summary['rows_written'],
            'results': [{'symbol': r.symbol, 'adjust': r.adjust, 'reason': r.reason, 'rows': r.rows,
                         'start': r.start, 'end': r.end, 'mismatched_dates': r.mismatched_dates}
                        for r in summary['results']],
        },
        'market_daily': tables,
    }, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def main(argv=None) -> int:
    args = parse_args(argv)
    cfg = DbConfig.from_env()
    if args.init_schema:
        init_schema(cfg)

    all_symbols = load_symbols()
    tickers = args.symbols or list(all_symbols)
    unknown = [t for t in tickers if t not in all_symbols]
    if unknown:
        print(f'config/symbols.yaml 沒有：{unknown}', file=sys.stderr)
        return 2
    symbols = [all_symbols[t] for t in tickers]

    print(f'{args.source} → {cfg.describe()}｜{args.mode}｜{", ".join(tickers)}｜{"/".join(args.adjust)}')
    with get_source(args.source) as src, cfg.connect() as conn:
        repo = MySQLRepository(conn)
        summary = ingest_daily(repo, src, symbols, adjusts=tuple(args.adjust), mode=args.mode,
                               default_start=args.start, lookback=args.lookback)
        for r in summary['results']:
            span = f'{r.start} ~ {r.end}' if r.start else ''
            extra = f'｜復權基準改變：{r.mismatched_dates}' if r.mismatched_dates else ''
            extra += f'｜{r.error}' if r.error else ''
            print(f'  {r.symbol:<6} {r.adjust:<4} {r.reason:<11} {r.rows:>5} 筆 {span}{extra}')
        print(f'run_id={summary["run_id"]} 狀態={summary["status"]} 共寫入 {summary["rows_written"]} 筆'
              f'（最後已收盤交易日 {summary["last_session"]}）')
        if not args.no_metrics:
            write_metrics(repo, summary, args)
            print(f'已更新 {METRICS.relative_to(ROOT)}')
    return 0 if summary['status'] == 'success' else 1


if __name__ == '__main__':
    sys.exit(main())
