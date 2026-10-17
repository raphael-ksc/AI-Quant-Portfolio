"""C13 搭建你的股票交易回測：6 個課程策略 × 3 檔自選股，2025 年回測 + 2026 年樣本外檢驗。

流程：
    MySQL market_daily（C06，Moomoo 前復權）→ quantlib.backtest（t+1 開盤成交、美股成本、滑價）
    → 每檔都和買入持有比較 → 成本敏感度 → outputs/figures/*.png + outputs/metrics.json

設計原則：
- 參數一律用課程預設值，不針對 2025 年最佳化（避免過度擬合）
- 「2025 年哪個策略最好」是事後解釋；另用 2026-01-02 起的樣本外資料檢驗它有沒有延續

用法（Project 根目錄；MySQL 連線讀 .env，需先跑過 C06）：
    .venv\\Scripts\\python.exe lessons\\L05-backtrader\\C13-backtrader-backtest\\src\\run_c13.py

⚠️ 僅供教育與研究用途，不構成投資建議。
"""
from __future__ import annotations

import datetime as dt
import json
import math
import sys
from importlib import metadata
from pathlib import Path

import matplotlib

matplotlib.use('Agg')
import matplotlib.lines  # noqa: E402
import matplotlib.patches  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import yaml  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm  # noqa: E402

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

from quantlib.backtest import BacktestConfig, USEquityCosts, run_backtest  # noqa: E402
from quantlib.db import DbConfig, MySQLRepository  # noqa: E402
from quantlib.strategies import load_strategies  # noqa: E402
from quantlib.strategies.buy_and_hold import BuyAndHold  # noqa: E402

CHECKIN_DIR = Path(__file__).resolve().parents[1]
OUTPUTS = CHECKIN_DIR / 'outputs'
FIGURES = OUTPUTS / 'figures'
SYMBOLS = ['PLTR', 'IREN', 'NVDA']
PERIODS = {
    # 名稱: (資料起點＝暖機起點, 評估起點, 評估終點)；暖機一年，確保 30 日指標都已算好
    '2025': (dt.date(2024, 1, 2), dt.date(2025, 1, 2), dt.date(2025, 12, 31)),
    '2026_oos': (dt.date(2025, 1, 2), dt.date(2026, 1, 2), None),  # None = 資料庫最新日
}
SLIPPAGE_GRID = [0.0, 5.0, 10.0, 20.0]
BASE_SLIPPAGE = 5.0

# 圖表：透明背景 + 中性灰文字，網站深色、淺色主題都看得清楚（顏色已用 dataviz validator 檢查兩種背景）
CHART_STYLE = {
    'figure.facecolor': 'none', 'axes.facecolor': 'none', 'savefig.transparent': True,
    'text.color': '#888888', 'axes.labelcolor': '#888888', 'axes.edgecolor': '#888888',
    'xtick.color': '#888888', 'ytick.color': '#888888', 'axes.grid': True,
    'grid.color': '#888888', 'grid.alpha': 0.2, 'font.size': 10,
    'font.sans-serif': ['Microsoft JhengHei', 'Noto Sans CJK TC', 'DejaVu Sans'],
    'axes.unicode_minus': False,
}
STRATEGY_COLOUR = '#3987e5'   # 策略（藍）
BENCH_COLOUR = '#d95926'      # 買入持有（橘）
DIVERGING = LinearSegmentedColormap.from_list('div', ['#e34948', '#d6d5d1', '#2a78d6'])
HEATMAP_CLIP = 1.5  # 色階截在 ±150%，避免 IREN 的極端值把其他格子都壓成灰色（格內數字仍為實際值）


def clean(x):
    """NaN / inf → None，讓 JSON 合法。"""
    if isinstance(x, float) and (math.isnan(x) or math.isinf(x)):
        return None
    if isinstance(x, (np.floating, np.integer)):
        return clean(x.item())
    return x


def load_all_bars(repo: MySQLRepository) -> dict[str, pd.DataFrame]:
    start = min(p[0] for p in PERIODS.values())
    return {s: repo.load_bars(s, start, dt.date.today()) for s in SYMBOLS}


def slice_period(bars: pd.DataFrame, period: str) -> tuple[pd.DataFrame, dt.date, dt.date]:
    data_start, trade_start, end = PERIODS[period]
    d = bars['date'].dt.date
    end = end or d.max()
    return bars[(d >= data_start) & (d <= end)].reset_index(drop=True), trade_start, end


def run_grid(all_bars, specs, costs) -> list[dict]:
    rows = []
    cfg = BacktestConfig(slippage_bps=BASE_SLIPPAGE, costs=costs)
    for period in PERIODS:
        for sym in SYMBOLS:
            bars, trade_start, end = slice_period(all_bars[sym], period)
            runs = [('buy_and_hold', '買入持有', 'Buy and Hold', BuyAndHold)]
            runs += [(k, s.meta['name'], s.meta['name_en'], s.cls) for k, s in specs.items()]
            for key, name, name_en, cls in runs:
                r = run_backtest(cls, bars, trade_start, symbol=sym, config=cfg)
                rows.append({'period': period, 'symbol': sym, 'strategy': key, 'name': name,
                             'name_en': name_en, 'start': r.start.isoformat(), 'end': r.end.isoformat(),
                             **{k: clean(v) for k, v in r.metrics().items()}, '_nav': r.nav})
    return rows


def run_sensitivity(all_bars, specs, costs) -> list[dict]:
    """2025 年：滑價 0／5／10／20 bps，另加完全不計成本的對照組。"""
    out = []
    zero = USEquityCosts.from_config('zero_cost')
    grid = [('zero_cost', 0.0, zero)] + [('moomoo_reference', s, costs) for s in SLIPPAGE_GRID]
    for sym in SYMBOLS:
        bars, trade_start, _ = slice_period(all_bars[sym], '2025')
        for key, spec in specs.items():
            for profile, slip, c in grid:
                r = run_backtest(spec.cls, bars, trade_start, symbol=sym,
                                 config=BacktestConfig(slippage_bps=slip, costs=c))
                m = r.metrics()
                out.append({'symbol': sym, 'strategy': key, 'cost_profile': profile, 'slippage_bps': slip,
                            'total_return': clean(m['total_return']), 'sharpe': clean(m['sharpe']),
                            'total_costs': clean(m['total_costs'])})
    return out


def winners(rows) -> dict:
    """每檔、每期以 Sharpe 最高者為「最能體現行情」的策略（不含買入持有）。"""
    out = {}
    for period in PERIODS:
        out[period] = {}
        for sym in SYMBOLS:
            cand = [r for r in rows if r['period'] == period and r['symbol'] == sym
                    and r['strategy'] != 'buy_and_hold' and r['sharpe'] is not None]
            best = max(cand, key=lambda r: r['sharpe'])
            bench = next(r for r in rows if r['period'] == period and r['symbol'] == sym
                         and r['strategy'] == 'buy_and_hold')
            out[period][sym] = {'strategy': best['strategy'], 'sharpe': best['sharpe'],
                                'total_return': best['total_return'],
                                'bh_total_return': bench['total_return'], 'bh_sharpe': bench['sharpe']}
    return out


# ======================= 圖表 =======================

def _pct(ax, axis='x'):
    fmt = matplotlib.ticker.PercentFormatter(1.0, decimals=0)
    (ax.xaxis if axis == 'x' else ax.yaxis).set_major_formatter(fmt)


def plot_returns_2025(rows, specs):
    """小多圖：每檔一格，橫條為 6 個策略的 2025 年總報酬，橘色虛線為買入持有。"""
    fig, axes = plt.subplots(1, 3, figsize=(12, 4.2), sharey=True)
    order = list(specs)
    for ax, sym in zip(axes, SYMBOLS):
        data = {r['strategy']: r for r in rows if r['period'] == '2025' and r['symbol'] == sym}
        vals = [data[k]['total_return'] for k in order]
        y = np.arange(len(order))
        ax.barh(y, vals, height=0.6, color=STRATEGY_COLOUR, edgecolor='none')
        bh = data['buy_and_hold']['total_return']
        ax.axvline(bh, color=BENCH_COLOUR, linewidth=2, linestyle='--')
        ax.axvline(0, color='#888888', linewidth=0.8)
        for yi, v in zip(y, vals):
            ax.text(v, yi, f' {v:+.0%} ' if v >= 0 else f' {v:+.0%} ', va='center',
                    ha='left' if v >= 0 else 'right', fontsize=8.5, color='#888888')
        ax.set_title(f'{sym}（買入持有 {bh:+.0%}）', fontsize=10.5)
        ax.set_yticks(y, [specs[k].meta['name'] for k in order])
        _pct(ax)
        ax.grid(axis='y', visible=False)
        lo, hi = min(vals + [bh, 0]), max(vals + [bh, 0])
        pad = (hi - lo) * 0.25
        ax.set_xlim(lo - pad, hi + pad)
    fig.legend(handles=[matplotlib.patches.Patch(color=STRATEGY_COLOUR, label='策略'),
                        matplotlib.lines.Line2D([], [], color=BENCH_COLOUR, lw=2, ls='--', label='買入持有')],
               loc='lower center', ncol=2, frameon=False, fontsize=9)
    fig.suptitle('2025 年總報酬：6 個課程策略 vs 買入持有（含成本與 5 bps 滑價）', fontsize=11)
    fig.tight_layout(rect=(0, 0.06, 1, 1))
    fig.savefig(FIGURES / 'c13_returns_2025.png', dpi=150)
    plt.close(fig)


def plot_excess_heatmap(rows, specs):
    """策略 × 標的的超額報酬（策略 − 買入持有）：左 2025、右 2026 樣本外。"""
    order = list(specs)
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.2))
    mats, idle = {}, {}
    for period in PERIODS:
        m = np.zeros((len(order), len(SYMBOLS)))
        z = np.zeros_like(m, dtype=bool)
        for j, sym in enumerate(SYMBOLS):
            data = {r['strategy']: r for r in rows if r['period'] == period and r['symbol'] == sym}
            for i, k in enumerate(order):
                m[i, j] = data[k]['total_return'] - data['buy_and_hold']['total_return']
                z[i, j] = data[k]['fills'] == 0
        mats[period], idle[period] = m, z
    lim = HEATMAP_CLIP
    norm = TwoSlopeNorm(vmin=-lim, vcenter=0, vmax=lim)
    titles = {'2025': '2025 年', '2026_oos': '2026 年樣本外（至最新資料日）'}
    for ax, period in zip(axes, PERIODS):
        m = mats[period]
        shown = np.where(idle[period], 0.0, np.clip(m, -lim, lim))   # 無交易的格子塗中性灰
        ax.imshow(shown, cmap=DIVERGING, norm=norm, aspect='auto')
        for i in range(m.shape[0]):
            for j in range(m.shape[1]):
                strong = abs(shown[i, j]) > lim * 0.55
                label = '無交易' if idle[period][i, j] else f'{m[i, j]:+.0%}'
                ax.text(j, i, label, ha='center', va='center', fontsize=9,
                        color='white' if strong else '#1f1f1f')
        ax.set_xticks(range(len(SYMBOLS)), SYMBOLS)
        ax.set_yticks(range(len(order)), [specs[k].meta['name'] for k in order])
        ax.set_title(titles[period], fontsize=10)
        ax.grid(False)
        ax.set_xticks(np.arange(-0.5, len(SYMBOLS)), minor=True)
        ax.set_yticks(np.arange(-0.5, len(order)), minor=True)
        ax.grid(which='minor', color='white', linewidth=2)   # 格子間 2px 間隔
        ax.tick_params(which='minor', length=0)
    fig.suptitle('超額報酬（策略報酬減買入持有）：藍 = 勝過買入持有，紅 = 落後；色階截於 ±150%', fontsize=11)
    fig.tight_layout()
    fig.savefig(FIGURES / 'c13_excess_heatmap.png', dpi=150)
    plt.close(fig)


def plot_equity_winners(rows, specs, win):
    """2025 年每檔 Sharpe 最高的策略 vs 買入持有：淨值曲線（以 1 為起點）。"""
    fig, axes = plt.subplots(1, 3, figsize=(12, 3.8), sharey=False)
    for ax, sym in zip(axes, SYMBOLS):
        best = win['2025'][sym]['strategy']
        for key, colour, label in [(best, STRATEGY_COLOUR, specs[best].meta['name']),
                                   ('buy_and_hold', BENCH_COLOUR, '買入持有')]:
            r = next(x for x in rows if x['period'] == '2025' and x['symbol'] == sym and x['strategy'] == key)
            nav = r['_nav'] / r['_nav'].iloc[0]
            ax.plot(nav.index, nav.values, color=colour, linewidth=2, label=label)
            ax.annotate(f'{label} {nav.iloc[-1] - 1:+.0%}', (nav.index[-1], nav.iloc[-1]),
                        xytext=(4, 0), textcoords='offset points', fontsize=8.5, color='#888888', va='center')
        ax.set_title(sym, fontsize=11)
        ax.axhline(1, color='#888888', linewidth=0.8)
        ax.legend(loc='upper left', fontsize=8.5, frameon=False)
        ax.xaxis.set_major_locator(matplotlib.dates.MonthLocator(bymonth=[1, 4, 7, 10]))
        ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter('%Y-%m'))
        ax.margins(x=0.02)
    fig.suptitle('2025 年：Sharpe 最高的策略 vs 買入持有（淨值，起點 = 1）', fontsize=11)
    fig.tight_layout()
    fig.savefig(FIGURES / 'c13_equity_winners_2025.png', dpi=150)
    plt.close(fig)


# ======================= 主程式 =======================

def main() -> int:
    FIGURES.mkdir(parents=True, exist_ok=True)
    specs = load_strategies()
    costs = USEquityCosts.from_config('moomoo_reference')
    with DbConfig.from_env().connect() as conn:
        all_bars = load_all_bars(MySQLRepository(conn))

    rows = run_grid(all_bars, specs, costs)
    sens = run_sensitivity(all_bars, specs, costs)
    win = winners(rows)

    plt.rcParams.update(CHART_STYLE)
    plot_returns_2025(rows, specs)
    plot_excess_heatmap(rows, specs)
    plot_equity_winners(rows, specs, win)

    cost_cfg = yaml.safe_load((ROOT / 'config' / 'costs.yaml').read_text(encoding='utf-8'))
    versions = {}
    for pkg in ('backtrader', 'pandas', 'numpy', 'matplotlib'):
        try:
            versions[pkg] = metadata.version(pkg)
        except metadata.PackageNotFoundError:
            pass
    metrics = {
        'generated_on': dt.date.today().isoformat(),
        'versions': versions,
        'params': {
            'data': 'MySQL market_daily（Moomoo，前復權 qfq）',
            'symbols': SYMBOLS,
            'periods': {k: {'warmup_from': v[0].isoformat(), 'trade_from': v[1].isoformat(),
                            'to': (v[2].isoformat() if v[2] else 'latest')} for k, v in PERIODS.items()},
            'initial_cash_usd': 10_000, 'position_pct': 95, 'sizing': '整數股',
            'fill': '訊號 t 日收盤 → t+1 日開盤成交；單根 K 線最多成交當天成交量 10%',
            'slippage_bps': BASE_SLIPPAGE, 'risk_free': 0.0,
            'cost_profile': 'moomoo_reference', 'cost_source': cost_cfg['profiles']['moomoo_reference']['source'],
            'sec_fee_source': cost_cfg['sec_fee']['source'], 'taf_source': cost_cfg['finra_taf']['source'],
            'strategy_params': {k: s.meta['params'] for k, s in specs.items()},
            'winner_rule': '每檔、每期取 Sharpe 最高的策略（不含買入持有）',
        },
        'results': [{k: v for k, v in r.items() if k != '_nav'} for r in rows],
        'winners': win,
        'sensitivity_2025': sens,
    }
    (OUTPUTS / 'metrics.json').write_text(json.dumps(metrics, ensure_ascii=False, indent=2) + '\n',
                                          encoding='utf-8')

    # 終端機摘要
    for period in PERIODS:
        print(f'\n=== {period} ===')
        for sym in SYMBOLS:
            sub = sorted((r for r in rows if r['period'] == period and r['symbol'] == sym),
                         key=lambda r: -(r['sharpe'] if r['sharpe'] is not None else -99))
            print(f'  {sym}  ({sub[0]["start"]} ~ {sub[0]["end"]})')
            for r in sub:
                sh = f'{r["sharpe"]:.2f}' if r['sharpe'] is not None else '  — '
                print(f'    {r["name"]:<8} 報酬 {r["total_return"]:+7.1%}  Sharpe {sh:>5}  '
                      f'MDD {r["max_drawdown"]:6.1%}  交易 {r["trades"]:>2}  成交 {r["fills"]:>2}  '
                      f'拒單 {r["rejected_orders"]}  成本 ${r["total_costs"]:.2f}  曝險 {r["exposure"]:.0%}')
    print(f'\n已輸出：{OUTPUTS.relative_to(ROOT)}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
