"""C04 獲取你的自選股數據：日線、分鐘線、季度財報。

流程：
    quantlib.data（Moomoo 或 yfinance）→ schema 驗證 → data/C04/*.csv（本機，不進 repo）
    → outputs/figures/*.png + outputs/metrics.json（彙總結果，進 repo 並顯示在網站）

用法（Project 根目錄；moomoo 需先啟動並登入 OpenD）：
    .venv\\Scripts\\python.exe lessons\\L03-digital-office\\C04-watchlist-data\\src\\fetch_watchlist.py
    .venv\\Scripts\\python.exe lessons\\...\\fetch_watchlist.py --source yfinance   # 任何人都能重現（分鐘線除外）

⚠️ 僅供教育與研究用途，不構成投資建議。原始行情與財報數據只存在本機，不公開。
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
import matplotlib.dates as mdates  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

from quantlib.data import (  # noqa: E402
    DataUnavailableError, get_source, get_symbol, validate_bars, validate_financials,
)

CHECKIN_DIR = Path(__file__).resolve().parents[1]
OUTPUTS = CHECKIN_DIR / 'outputs'
FIGURES = OUTPUTS / 'figures'
DATA_DIR = ROOT / 'data' / 'C04'

# 圖表用中性灰色與透明背景，在網站深色、淺色主題下都看得清楚
CHART_STYLE = {
    'figure.facecolor': 'none', 'axes.facecolor': 'none', 'savefig.transparent': True,
    'text.color': '#888888', 'axes.labelcolor': '#888888', 'axes.edgecolor': '#888888',
    'xtick.color': '#888888', 'ytick.color': '#888888', 'axes.grid': True,
    'grid.color': '#888888', 'grid.alpha': 0.25, 'font.size': 10,
}
LINE_COLOURS = ['#ffa028', '#4e88c7', '#4db848']


def parse_args(argv=None):
    p = argparse.ArgumentParser(description='C04 獲取自選股數據')
    p.add_argument('--source', choices=('moomoo', 'yfinance'), default='moomoo')
    p.add_argument('--symbols', nargs='+', default=['PLTR', 'IREN'])
    p.add_argument('--daily-start', type=dt.date.fromisoformat, default=dt.date(2024, 1, 1))
    p.add_argument('--daily-end', type=dt.date.fromisoformat, default=dt.date(2025, 12, 31))
    p.add_argument('--minute-day', type=dt.date.fromisoformat, default=dt.date(2026, 2, 6))
    p.add_argument('--periods', type=int, default=8, help='季報期數')
    p.add_argument('--no-cross-check', action='store_true', help='不與 yfinance 日線交叉比對')
    return p.parse_args(argv)


def version(pkg: str) -> str | None:
    try:
        return metadata.version(pkg)
    except metadata.PackageNotFoundError:
        return None


def summarise_bars(df: pd.DataFrame, time_col: str) -> dict:
    return {
        'rows': int(len(df)),
        'first': str(df[time_col].min()),
        'last': str(df[time_col].max()),
    }


def summarise_financials(df: pd.DataFrame) -> dict:
    periods = sorted(df['period_end'].dt.date.unique(), reverse=True)
    by_period = df.drop_duplicates('period_end').set_index('period_end')['fiscal_period']
    return {
        'freq': df['freq'].iloc[0],
        'currency': df['currency'].iloc[0],
        'periods': [str(p) for p in periods],
        'fiscal_periods': [by_period.get(pd.Timestamp(p)) for p in periods],
        'items_by_statement': {s: int(g['field_id'].nunique()) for s, g in df.groupby('statement')},
        'announce_date_available': bool(df['announce_date'].notna().any()),
    }


def cross_check(primary: pd.DataFrame, other: pd.DataFrame) -> dict:
    """比對兩個資料源的日線收盤價：共同交易日數與收盤價差異（百分比）。"""
    merged = primary.merge(other, on=['symbol', 'date'], suffixes=('', '_other'))
    if merged.empty:
        return {'matched_days': 0}
    diff = (merged['close'] - merged['close_other']).abs() / merged['close_other'] * 100
    only_primary = len(set(primary['date']) - set(other['date']))
    only_other = len(set(other['date']) - set(primary['date']))
    return {
        'matched_days': int(len(merged)),
        'only_in_primary': only_primary,
        'only_in_yfinance': only_other,
        'max_abs_close_diff_pct': round(float(diff.max()), 4),
        'mean_abs_close_diff_pct': round(float(diff.mean()), 4),
    }


def plot_daily(daily: dict[str, pd.DataFrame], path: Path, source: str) -> None:
    with plt.rc_context(CHART_STYLE):
        fig, axes = plt.subplots(len(daily), 1, figsize=(10, 3.2 * len(daily)), sharex=True)
        axes = [axes] if len(daily) == 1 else axes
        for ax, (ticker, df), colour in zip(axes, daily.items(), LINE_COLOURS):
            ax.plot(df['date'], df['close'], color=colour, linewidth=1.4)
            ax.set_title(f'{ticker} daily close (forward-adjusted, {df["currency"].iloc[0]})', loc='left')
            ax.set_ylabel('Price')
        axes[-1].set_xlabel(f'Source: {source}')
        fig.tight_layout()
        fig.savefig(path, dpi=130)
        plt.close(fig)


def plot_minute(minute: dict[str, pd.DataFrame], path: Path, day: dt.date, source: str) -> None:
    with plt.rc_context(CHART_STYLE):
        fig, ax = plt.subplots(figsize=(10, 3.6))
        for (ticker, df), colour in zip(minute.items(), LINE_COLOURS):
            base = df['close'].iloc[0]
            ax.plot(df['ts'].dt.tz_localize(None), (df['close'] / base - 1) * 100,
                    color=colour, linewidth=1.2, label=ticker)
        ax.set_title(f'Intraday 1-minute close, {day} regular session (% from first bar)', loc='left')
        ax.set_ylabel('%')
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        ax.set_xlabel(f'US Eastern time · Source: {source}')
        ax.legend(frameon=False)
        fig.tight_layout()
        fig.savefig(path, dpi=130)
        plt.close(fig)


def main(argv=None) -> int:
    args = parse_args(argv)
    FIGURES.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    symbols = {t: get_symbol(t) for t in args.symbols}

    daily, minute, financials, notes = {}, {}, {}, []
    with get_source(args.source) as src:
        for ticker, sym in symbols.items():
            print(f'[{ticker}] 日線 {args.daily_start} ~ {args.daily_end}')
            daily[ticker] = validate_bars(src.get_daily_bars(sym, args.daily_start, args.daily_end), 'daily')
            print(f'[{ticker}] 分鐘線 {args.minute_day}')
            try:
                minute[ticker] = validate_bars(src.get_minute_bars(sym, args.minute_day), 'minute')
            except DataUnavailableError as e:
                notes.append(f'{ticker} 分鐘線：{e}')
                print(f'  略過：{e}')
            print(f'[{ticker}] 財報 {args.periods} 期')
            financials[ticker] = validate_financials(src.get_financials(sym, 'Q', args.periods))
        quota = src.quota() if hasattr(src, 'quota') else None

    checks = {}
    if not args.no_cross_check and args.source != 'yfinance':
        with get_source('yfinance') as yf_src:
            for ticker, sym in symbols.items():
                other = yf_src.get_daily_bars(sym, args.daily_start, args.daily_end)
                checks[ticker] = cross_check(daily[ticker], other)

    # 原始資料只存本機（data/ 已被 .gitignore 排除）
    for name, frames in (('daily', daily), ('minute', minute), ('financials', financials)):
        if frames:
            pd.concat(frames.values()).to_csv(DATA_DIR / f'{name}_{args.source}.csv', index=False)

    plot_daily(daily, FIGURES / 'daily_close.png', args.source)
    if minute:
        plot_minute(minute, FIGURES / f'minute_{args.minute_day}.png', args.minute_day, args.source)

    metrics = {
        'generated_on': dt.date.today().isoformat(),
        'source': args.source,
        'versions': {'moomoo-api': version('moomoo-api'), 'yfinance': version('yfinance'),
                     'pandas': version('pandas')},
        'params': {'daily': [str(args.daily_start), str(args.daily_end)], 'minute_day': str(args.minute_day),
                   'session': 'regular (09:30-16:00 ET)', 'adjust': 'qfq (forward-adjusted)',
                   'financial_periods': args.periods},
        'symbols': {
            t: {
                'name_en': symbols[t].name_en,
                'exchange': symbols[t].exchange,
                'currency': symbols[t].currency,
                'daily': summarise_bars(daily[t], 'date'),
                'minute': summarise_bars(minute[t], 'ts') if t in minute else None,
                'financials': summarise_financials(financials[t]),
                'cross_check_vs_yfinance': checks.get(t),
            } for t in symbols
        },
        'history_kline_quota': quota,
        'notes': notes,
    }
    (OUTPUTS / 'metrics.json').write_text(json.dumps(metrics, ensure_ascii=False, indent=2, default=str) + '\n',
                                          encoding='utf-8')
    print(json.dumps(metrics['symbols'], ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == '__main__':
    sys.exit(main())
