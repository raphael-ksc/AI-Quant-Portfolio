"""C07 財務數據採集：自選股季報 → MySQL（原始科目、重編紀錄、衍生指標、課程相容 VIEW）。

原課程為 QMT／Akshare，此處已換成 Moomoo 版本（get_financials_statements），yfinance 供公開重現：
    quantlib.data.get_financials → schema 驗證 → financial_items（數值改變時舊值寫入 financial_revisions）
    → config/financial_fields.yaml 多候選科目比對 → 近四季合計與比率
    → SEC EDGAR 申報日 → available_date（防前視偏差）→ financial_metrics → VIEW trade_stock_financial
    → outputs/metrics.json + outputs/figures/c07_earnings_quality.png

用法（Project 根目錄；moomoo 需先啟動 OpenD；MySQL 連線與 SEC_USER_AGENT 讀 .env）：
    .venv\\Scripts\\python.exe lessons\\L04-data-pipeline\\C07-financial-data-collection\\src\\ingest_financials.py --init-schema
    ...\\ingest_financials.py --source yfinance          # 任何人都能重現（季報約 5–6 期）
    ...\\ingest_financials.py --no-edgar                 # 不查 SEC，可交易日全部用保守推算

⚠️ 僅供教育與研究用途，不構成投資建議。
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from importlib import metadata
from pathlib import Path

import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

from quantlib.data import get_source, load_symbols  # noqa: E402
from quantlib.data.edgar import EdgarClient  # noqa: E402
from quantlib.db import DbConfig, MySQLRepository  # noqa: E402
from quantlib.fundamentals import ingest_financials  # noqa: E402

CHECKIN_DIR = Path(__file__).resolve().parents[1]
OUTPUTS = CHECKIN_DIR / 'outputs'
FIGURES = OUTPUTS / 'figures'

# 圖表：透明背景 + 中性灰文字；兩個顏色已用 dataviz validator 檢查淺色與深色背景
CHART_STYLE = {
    'figure.facecolor': 'none', 'axes.facecolor': 'none', 'savefig.transparent': True,
    'text.color': '#888888', 'axes.labelcolor': '#888888', 'axes.edgecolor': '#888888',
    'xtick.color': '#888888', 'ytick.color': '#888888', 'axes.grid': True,
    'grid.color': '#888888', 'grid.alpha': 0.2, 'font.size': 10,
    'font.sans-serif': ['Microsoft JhengHei', 'Noto Sans CJK TC', 'DejaVu Sans'],
    'axes.unicode_minus': False,
}
OCF_COLOUR = '#3987e5'   # 營運現金流（藍）
NI_COLOUR = '#d95926'    # 淨利（橘）


def parse_args(argv=None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description='C07：自選股季報寫入 MySQL')
    p.add_argument('--source', choices=['moomoo', 'yfinance'], default='moomoo')
    p.add_argument('--symbols', nargs='+', help='預設為 config/symbols.yaml 全部標的')
    p.add_argument('--periods', type=int, default=12, help='最近幾季（Moomoo 約 12 季；yfinance 約 5–6 季）')
    p.add_argument('--no-edgar', action='store_true', help='不查 SEC EDGAR，可交易日全部用保守推算')
    p.add_argument('--init-schema', action='store_true', help='套用 db/schema.sql（可重複執行）')
    p.add_argument('--no-outputs', action='store_true', help='不更新 metrics.json 與圖表（排程用）')
    return p.parse_args(argv)


def load_metrics(conn, source: str, symbols: list[str]) -> pd.DataFrame:
    with conn.cursor() as cur:
        cur.execute(f'SELECT symbol, period_end, fiscal_period, available_date, available_basis, filing_form, '
                    f'net_income_ttm, ocf_ttm, revenue_ttm, roe_ttm, gross_margin_ttm, ocf_to_ni_ttm, debt_ratio, '
                    f'current_ratio FROM financial_metrics WHERE source=%s AND freq=%s '
                    f'AND symbol IN ({", ".join(["%s"] * len(symbols))}) ORDER BY symbol, period_end',
                    (source, 'Q', *symbols))
        cols = [d[0] for d in cur.description]
        df = pd.DataFrame(cur.fetchall(), columns=cols)
    for c in cols[6:]:
        df[c] = pd.to_numeric(df[c], errors='coerce')
    return df


def plot_earnings_quality(df: pd.DataFrame, symbols: list[str]) -> Path:
    """盈餘品質（第 4 課 p.45）：近四季淨利 vs 近四季營運現金流；每檔一格，各自的 y 軸。"""
    plt.rcParams.update(CHART_STYLE)
    fig, axes = plt.subplots(1, len(symbols), figsize=(4 * len(symbols), 3.8))
    for ax, sym in zip(axes if len(symbols) > 1 else [axes], symbols):
        d = df[(df['symbol'] == sym) & df['net_income_ttm'].notna()]
        for col, colour, label in [('ocf_ttm', OCF_COLOUR, '營運現金流'), ('net_income_ttm', NI_COLOUR, '淨利')]:
            s = d[['period_end', col]].dropna()
            ax.plot(pd.to_datetime(s['period_end']), s[col] / 1e9, color=colour, linewidth=2, marker='o',
                    markersize=4, label=label)
        ax.axhline(0, color='#888888', linewidth=0.8)
        ax.set_title(sym, fontsize=11)
        ax.set_ylabel('近四季合計（十億美元）', fontsize=9)
        ax.xaxis.set_major_locator(matplotlib.dates.MonthLocator(bymonth=[3, 9]))
        ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter('%Y-%m'))
        ax.tick_params(axis='x', labelsize=8.5)
        ax.legend(loc='upper left', fontsize=8.5, frameon=False)
    fig.suptitle('盈餘品質：近四季淨利 vs 營運現金流（現金流長期低於淨利 = 獲利沒有變成現金）', fontsize=11)
    fig.tight_layout()
    FIGURES.mkdir(parents=True, exist_ok=True)
    path = FIGURES / 'c07_earnings_quality.png'
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def clean(v):
    if isinstance(v, float) and pd.isna(v):
        return None
    if isinstance(v, (dt.date, pd.Timestamp)):
        return pd.Timestamp(v).date().isoformat()
    return v


def write_metrics(summary: dict, df: pd.DataFrame, args) -> None:
    versions = {}
    for pkg in ('moomoo-api', 'yfinance', 'pandas', 'pymysql'):
        try:
            versions[pkg] = metadata.version(pkg)
        except metadata.PackageNotFoundError:
            pass
    latest = df.sort_values('period_end').groupby('symbol').tail(1)
    OUTPUTS.mkdir(parents=True, exist_ok=True)
    (OUTPUTS / 'metrics.json').write_text(json.dumps({
        'generated_on': dt.date.today().isoformat(),
        'versions': versions,
        'params': {'source': args.source, 'freq': 'Q', 'periods_requested': args.periods,
                   'edgar': not args.no_edgar,
                   'availability_rule': 'SEC 10-Q/10-K 原始申報日隔天；查不到時季報 +46 天、財年 Q4 +76 天',
                   'ttm_rule': '連續 4 季都有值才計算'},
        'run': {'run_id': summary['run_id'], 'status': summary['status']},
        'symbols': {r.symbol: {'status': r.status, 'periods': r.periods, 'items': r.items,
                               'revisions': r.revisions, 'first': r.first, 'last': r.last,
                               'edgar_matched': r.edgar_matched, 'edgar_error': r.edgar_error,
                               'field_report': r.report, 'error': r.error} for r in summary['results']},
        'latest': [{k: clean(v) for k, v in row.items()} for row in latest.to_dict('records')],
        'series': [{k: clean(v) for k, v in row.items()} for row in df.to_dict('records')],
    }, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def main(argv=None) -> int:
    args = parse_args(argv)
    cfg = DbConfig.from_env()
    all_symbols = load_symbols()
    tickers = args.symbols or list(all_symbols)
    unknown = [t for t in tickers if t not in all_symbols]
    if unknown:
        print(f'config/symbols.yaml 沒有：{unknown}', file=sys.stderr)
        return 2
    edgar = None if args.no_edgar else EdgarClient()

    print(f'{args.source} → {cfg.describe()}｜{", ".join(tickers)}｜最近 {args.periods} 季｜'
          f'可交易日：{"保守推算" if edgar is None else "SEC EDGAR"}')
    with cfg.connect() as conn:
        repo = MySQLRepository(conn)
        if args.init_schema:
            print(f'已套用 db/schema.sql（{repo.apply_schema()} 個陳述式）')
        with get_source(args.source) as src:
            summary = ingest_financials(repo, src, [all_symbols[t] for t in tickers], edgar=edgar,
                                        periods=args.periods)
        for r in summary['results']:
            if r.status == 'failed':
                print(f'  {r.symbol:<6} 失敗：{r.error}')
                continue
            missing = {k: len(v) for k, v in r.report['missing'].items()}
            print(f'  {r.symbol:<6} {r.periods} 季 {r.first} ~ {r.last}｜科目 {r.items} 筆｜重編 {r.revisions}｜'
                  f'EDGAR 對上 {r.edgar_matched} 季' + (f'｜缺值 {missing}' if missing else '')
                  + (f'｜期末日校正 {r.report["aligned_period_ends"]}' if r.report['aligned_period_ends'] else ''))
        print(f'run_id={summary["run_id"]} 狀態={summary["status"]}')
        if not args.no_outputs:
            df = load_metrics(conn, args.source, tickers)
            print(f'已輸出 {plot_earnings_quality(df, tickers).relative_to(ROOT)}')
            write_metrics(summary, df, args)
            print(f'已更新 {(OUTPUTS / "metrics.json").relative_to(ROOT)}')
    return 0 if summary['status'] == 'success' else 1


if __name__ == '__main__':
    sys.exit(main())
