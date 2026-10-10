# Moomoo vs yfinance Data Coverage Test

> Tested: 10 October 2026 | Symbols: `PLTR`, `IREN` (plus `NVDA` to verify the date issue)
> Versions: moomoo-api 10.10.7008 and 10.11.7108 (Python 3.13, identical results), yfinance 1.7.0

## 1. Summary

| Item | Moomoo | yfinance |
|---|---|---|
| 2025 daily bars | 250 | 250 |
| Close on 2025-12-31 (PLTR / IREN) | 177.75 / 37.77 | 177.75 / 37.77 |
| Quarterly periods (`num=12` requested) | **12** (all three statements) | **5–6** |
| Annual periods | 7–8 | 5 |
| Quarterly income statement items (PLTR / IREN) | 23 / 31 | 41 / 56 (row count, many empty) |
| Period dates | ⚠️ see section 2 | Correct period-end dates |

- **Daily bars** matched exactly in this test and are interchangeable.
- **Financial statements**: Moomoo offers roughly twice yfinance's history. Fundamental factors that need long histories (such as C23's quarterly factors) should use Moomoo; yfinance suits public reproduction and annual-level analysis.
- **Line items**: yfinance has more rows but many are empty; item names differ between the sources, so a mapping table is needed for cross-source comparison.

## 2. ⚠️ Finding: Moomoo's `date_time_str` is one day before the actual period end

| Symbol | `period_text` | `date_time_str` | `date_time` in UTC+8 | Actual period end |
|---|---|---|---|---|
| PLTR | 2026/Q2 | 2026-06-29 | 2026-06-30 00:00 | 2026-06-30 (calendar quarter) |
| PLTR | 2026/Q1 | 2026-03-30 | 2026-03-31 00:00 | 2026-03-31 |
| PLTR | 2025/Q4 | 2025-12-30 | 2025-12-31 00:00 | 2025-12-31 |
| NVDA | 2027/Q2 | 2026-07-25 | 2026-07-26 00:00 | 2026-07-26 (SEC filing) |

- The `date_time` timestamp is always **midnight UTC+8 on the period-end date**; `date_time_str` renders the same timestamp as a UTC date, so it falls one day early.
- [Inference] This is a systematic time-zone offset (consistent across six periods and two companies), not a difference in fiscal-quarter definitions.
- **Project rule**: always derive the period end from `date_time` converted to UTC+8, never use `date_time_str` directly, and normalise before merging with yfinance.

## 3. Finding: line-item counts vary between periods for the same company

NVDA's income statement has 23 items for 2027/Q2 but 22 for 2027/Q1 and 2026/Q4. Code must not assume a fixed item count; align on `field_id` and allow missing values.

## 4. Impact on the project

- The Moomoo loader in `quantlib/data/` needs a period-end correction with unit tests.
- Financial statements still lack announcement dates; backtests must source them separately to avoid look-ahead bias.
