# C06 Market Data Collection

> ⚠️ Disclaimer: all strategy analysis and backtest results on this page are for educational and research purposes only and do not constitute investment advice or any guarantee of returns.

## Requirements

- Collect market data with QMT and write it to MySQL
- Table: `trade_stock_daily` (daily bars)
- **The course uses QMT; this version uses Moomoo instead.** QMT's `get_market_data_ex` is replaced by the Moomoo source in `quantlib/data` (`request_history_kline`), with yfinance available for anyone without a Moomoo account.

## Method

- **Symbols**: `US.PLTR`, `US.IREN`, `US.NVDA` (configured in `config/symbols.yaml`), 2023-01-03 to 2026-10-16.
- **Pipeline**:

```
config/symbols.yaml → DataSource (Moomoo / yfinance) → validate_bars
  → IncrementalPlanner (fill missing dates + 5-day look-back check) → MySQL market_daily
  → ingest_runs (run log) → VIEW trade_stock_daily (compatible with the course code)
```

- **Schema** (`db/schema.sql`):
  - `market_daily`: primary key `(symbol, trade_date, adjust, source)`. Forward-adjusted (qfq) and unadjusted (none) prices sit side by side, as do Moomoo and yfinance, so sources can be cross-checked.
  - `instruments`: symbol master with `is_active` and `delisted_date` reserved, so delisted stocks can be included in later market-wide research.
  - `ingest_runs`: source, row count, status and error message for every run.
  - VIEW `trade_stock_daily`: column names match the course (`stock_code`, `open_price`, …), so the `data_loader.py` scripts in lessons 13 and 18 can read it directly.
- **Two environments, one codebase**: switching only changes `MYSQL_PORT` in `.env`.
  - Local MySQL80 (3306): day-to-day research.
  - Docker (3307): `docker compose up -d` creates the tables automatically; with `--source yfinance`, anyone can reproduce the pipeline.
- **Run**: `lessons/L04-data-pipeline/C06-market-data-collection/src/ingest_daily.py`; shared code lives in `quantlib/db/`.

### Differences from the course version

| Issue | Course version | This version |
|---|---|---|
| Price precision | `DECIMAL(10,2)` | `DECIMAL(18,6)`: forward-adjusted prices often have three or more decimals, and two decimals distort them |
| Adjustment basis | Only appends new dates | Re-checks the last five stored sessions on every run; a mismatched close means a split or dividend has changed the adjustment basis, so the whole series is refetched |
| Unfinished bars | Uses "today" to decide whether data is current | Uses US Eastern time to find the last closed session, so an intraday run never writes an unfinished bar |
| Price adjustment | Forward-adjusted only | Both forward-adjusted and unadjusted; backtests that need "prices as seen at the time" use unadjusted data |
| Turnover rate | Calculated from free-float shares | Uses Moomoo's `turnover_rate` (a ratio); the view converts it to the percentage the course uses |
| Writes | `ON DUPLICATE KEY UPDATE` with `VALUES()` | Same batched upsert, using MySQL 8's `AS new` alias (`VALUES()` is deprecated) |
| Run log | Printed to the terminal only | Written to `ingest_runs`; if one symbol fails, the run is marked `partial` and the other symbols still load |

## Results

| Item | Result |
|---|---|
| First full load into local MySQL80 (Moomoo) | 3 symbols × 2 adjustments × 951 sessions = **5,706 rows**, status success |
| Second run | All six combinations `up_to_date`, 0 rows written (re-runs never duplicate data) |
| Re-run after deleting PLTR's last three days | Looked back from 2026-10-07 and wrote 8 rows (5 overlapping + 3 new); overlapping closes matched |
| Docker (3307) + yfinance | Tables created automatically; 951 sessions each for PLTR and NVDA, 3,804 rows written, view reads correctly |
| Moomoo traded value and turnover | Present for all 5,706 rows; yfinance does not provide them, so they are stored as NULL |
| Historical candlestick quota | Adding NVDA used one more symbol (3 of 100 symbols per 30 days) |
| Tests | 27 unit tests (no database needed) plus 6 MySQL integration tests; CI starts a MySQL container and runs the integration tests on every deploy |

**NVDA's 10-for-1 split shows why both adjustments are stored**: on 2024-06-07, the last session before the split, the unadjusted close is about 10.03 times the forward-adjusted close. The factor of 10 comes from the split; the cause of the extra ~0.28% is not yet verified ([inference] possibly dividend adjustment or Moomoo's adjustment method, to be checked against yfinance). Storing forward-adjusted prices alone would hide the price the market actually traded at.

Row counts and date ranges are in [`outputs/metrics.json`](outputs/metrics.json) (counts and dates only, no prices).

## Risk checklist

- [x] Data leakage and look-ahead bias: unfinished bars are never written. Forward-adjusted prices change with future corporate actions, so unadjusted data is kept as well and backtests can choose the right one.
- [x] Survivorship bias: this check-in covers only three watchlist stocks; `instruments` reserves delisting fields, and market-wide research must include delisted stocks.
- [ ] Overfitting and out-of-sample testing: no strategy in this check-in.
- [ ] Transaction costs and slippage: no trading in this check-in.
- [x] Liquidity constraints and market impact: volume, traded value and turnover are stored so later strategy check-ins can set liquidity thresholds.

## Limitations and reflections

- The "last closed session" logic excludes weekends but not US public holidays. Data sources return no bar on a holiday, so correctness is unaffected; it just costs one extra query.
- The course runs automatically at 15:30 each day. The US market closes at 4–5 am Taipei time, so this check-in runs manually for now. To automate it, Windows Task Scheduler can run `ingest_daily.py` daily at 06:00 Taipei time.
- Moomoo's historical candlestick quota is 100 symbols per 30 days, so larger universes need quota planning or yfinance.
- (To be completed: personal reflections)
