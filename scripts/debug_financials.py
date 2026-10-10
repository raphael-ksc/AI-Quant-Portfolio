"""印出某標的最新一期的 Moomoo 財報科目清單（field_id、科目名稱、數值），用來核對新股票的科目命名。

用法（需先啟動並登入 OpenD）：
    .venv\\Scripts\\python.exe scripts\\debug_financials.py PLTR
    .venv\\Scripts\\python.exe scripts\\debug_financials.py NVDA --statement cashflow --freq A

標的必須先在 config/symbols.yaml 設定。不要用猜的比對科目，先跑這支看實際清單（docs/moomoo_api_notes.md 第 8 節）。
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from quantlib.data import get_source, get_symbol  # noqa: E402
from quantlib.data.schema import STATEMENTS  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('ticker')
    parser.add_argument('--statement', choices=STATEMENTS, default=None, help='預設三張報表都印')
    parser.add_argument('--freq', choices=('Q', 'A'), default='Q')
    args = parser.parse_args()

    symbol = get_symbol(args.ticker)
    with get_source('moomoo') as src:
        df = src.get_financials(symbol, freq=args.freq, periods=1)
    if args.statement:
        df = df[df['statement'] == args.statement]

    for statement, group in df.groupby('statement', sort=False):
        first = group.iloc[0]
        print(f'\n== {statement}｜{first["fiscal_period"]}｜期末日 {first["period_end"].date()}'
              f'｜{first["currency"]}｜{len(group)} 個科目 ==')
        for row in group.itertuples():
            print(f'{row.field_id:>6}  {row.name:<55} {row.value}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
