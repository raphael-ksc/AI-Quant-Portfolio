"""
debug_financials.py
====================
除錯用小工具：連上 Moomoo OpenD，抓一檔股票的財務報表，
把「Cash Flow（現金流量表）」裡實際的科目名稱（display_name）全部印出來。

用途：factor_engine.py 是用關鍵字比對科目名稱來找「資本支出」「營運現金流」，
若篩選結果一直顯示「資料不足」，代表關鍵字沒有對到 Moomoo 實際回傳的名稱，
跑這支腳本就能看到真正的名稱，回報給我就能快速修正。

新增功能：除了科目清單外，也印出 report_list[0] 的頂層 metadata 欄位
（排除 item_list），用來確認是否有公告日期（announce_date）之類的欄位。

用法：
    python debug_financials.py US.NVDA
"""

import json
import sys

import moomoo as ft

TICKER = sys.argv[1] if len(sys.argv) > 1 else "US.NVDA"


def print_metadata(report: dict) -> None:
    """印出單一期別的頂層 metadata（排除 item_list，避免被科目清單洗版）。"""
    meta = {k: v for k, v in report.items() if k != "item_list"}
    if meta:
        print("  [metadata] report_list[0] 頂層欄位：")
        print(json.dumps(meta, indent=4, ensure_ascii=False, default=str))
    else:
        print("  [metadata] 這一期沒有 item_list 以外的其他欄位")


def print_statement(quote_ctx, ticker: str, statement_type: int, label: str) -> None:
    print(f"\n===== {ticker} · {label} =====")
    ret, data = quote_ctx.get_financials_statements(
        ticker, statement_type=statement_type, financial_type=9, num=8
    )
    if ret != ft.RET_OK:
        print("錯誤：", data)
        return

    reports = data.get("report_list", [])
    print(f"共 {len(reports)} 期資料")
    if not reports:
        return

    # 先印頂層 metadata，確認有沒有公告日期等欄位
    print_metadata(reports[0])

    print("最新一期的科目清單：")
    for item in reports[0].get("item_list", []):
        print(
            f"  field_id={item.get('field_id')!s:>6}  "
            f"display_name={item.get('display_name')!r}  data={item.get('data')}"
        )


quote_ctx = ft.OpenQuoteContext(host="127.0.0.1", port=11111)

try:
    print_statement(quote_ctx, TICKER, statement_type=1, label="Income（利潤表）")
    print_statement(quote_ctx, TICKER, statement_type=3, label="CashFlow（現金流量表）")
    print_statement(quote_ctx, TICKER, statement_type=2, label="BalanceSheet（資產負債表）")
finally:
    quote_ctx.close()