# C04 Watchlist Data Acquisition

> ⚠️ Disclaimer: all strategy analysis and backtest results on this page are for educational and research purposes only and do not constitute investment advice or any guarantee of returns.

## Requirements

- For your watchlist stocks, collect:
  - Daily bars, for example 2024-01-01 to 2025-12-31
  - Minute bars, for example for 2026-02-06
  - Financial statements (the course used tushare, akshare or QMT; this version uses the Moomoo OpenAPI)

## Method

- **Symbols**: `US.PLTR`, `US.IREN` (both Nasdaq-listed, USD; configured in `config/symbols.yaml`).
- **Data layer**: the new `quantlib/data/`. Moomoo and yfinance implement the same interface, emit a unified format and are validated by `schema.py`.
  - Primary source: Moomoo OpenAPI (LV1 quote permissions)
  - Cross-check and public reproduction: yfinance (`--source yfinance` runs for anyone, except minute bars)
- **Daily bars**: 2024-01-01 to 2025-12-31, forward-adjusted.
- **Minute bars**: 2026-02-06, regular session only (09:30–16:00 US Eastern), timestamped at bar close.
- **Financial statements**: the latest eight quarters of income statement, balance sheet and cash flow, reshaped into a long table (one row per line item per period).
- **Run**: `lessons/L03-digital-office/C04-watchlist-data/src/fetch_watchlist.py`. Raw data stays local in `data/C04/` and is not published.

### Improvements over the first version (`legacy-homework/`)

| Issue | First version | New version |
|---|---|---|
| Candlestick pagination | Only the first page of 1,000 rows — longer requests were **silently truncated** | Loops through every `page_req_key` |
| Financial period end | Columns were sequence numbers (`period_0`…) with no dates | Derived from `date_time` in UTC+8, correcting Moomoo's one-day-early date |
| Line-item matching | Keyword matching on item names | Keeps `(statement, field_id)`, since `field_id` is only unique within a statement |
| Financial pagination | Not handled | Loops through `next_key` |
| yfinance daily end date | `end` is exclusive, so the last day was missing | Adds one day automatically; start and end are both inclusive |
| Connections | Opened and closed in every function | One connection, ≥ 1.1 s between calls, 5 s back-off on rate limits |

## Results

| Item | PLTR | IREN |
|---|---|---|
| Daily bars (2024–2025) | 502 | 502 |
| Minute bars (2026-02-06) | 390 (09:31–16:00) | 390 (09:31–16:00) |
| Quarterly periods | 8 (2024/Q3–2026/Q2) | 8 (FY2025/Q1–FY2026/Q4) |
| Line items (income / balance / cash flow) | 23 / 36 / 26 | 32 / 52 / 30 |
| Daily cross-check vs yfinance | All 502 days matched, 0% close difference | All 502 days matched, 0% close difference |

- Historical candlestick quota: 2 symbols used, 98 remaining (per 30 days).
- yfinance reproduction mode: the same 502 daily bars; only six quarterly periods; minute bars for 2026-02-06 are outside yfinance's seven-day window.
- The closes match exactly because neither stock had a split or dividend in 2024–2025. **This does not prove the two sources adjust prices the same way**; symbols with corporate actions need a fresh comparison.
- IREN's fiscal year ends in June, so 2026-06-30 is its FY2026/Q4. Cross-company comparisons always align on period-end dates, never fiscal labels.

## Risk checklist

- [x] Data leakage and look-ahead bias: statements carry only the period-end date, not the announcement date. `announce_date` is left empty; any backtest must source announcement dates separately.
- [x] Survivorship bias: only two named stocks, no selection involved. Market-wide screening later must include delisted stocks.
- [ ] Overfitting and out-of-sample testing: no strategy in this check-in.
- [ ] Transaction costs and slippage: no trading in this check-in.
- [x] Liquidity constraints and market impact: minute bars cover the regular session only, excluding the thinner pre- and post-market hours.

## Limitations and reflections

- Forward-adjusted prices change when future corporate actions occur; "as seen at the time" prices require unadjusted data (`adjust='none'`).
- Moomoo's quota (100 symbols per 30 days) means a 50-stock cross-sectional study such as C24 needs quota planning, or yfinance for daily bars.
- (To be completed: personal reflections)
