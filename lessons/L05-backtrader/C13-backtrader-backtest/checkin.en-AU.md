# C13 Building a Stock Backtest

> ⚠️ Disclaimer: all strategy analysis and backtest results on this page are for educational and research purposes only and do not constitute investment advice or any guarantee of returns.

## Requirements

- Which trading strategy suited your watchlist stocks in 2025?
  - Use your own watchlist or Kweichow Moutai
  - Candidates: dual moving average, MACD, RSI, Bollinger Bands, momentum, MACD bullish divergence
  - Why does that strategy best reflect the market that year?
- Course example (Moutai 2025, initial capital 1,000,000, 0.02% commission, 95% position size): total return −8.94%, maximum drawdown 10.36% (course figures, not my results)
- Course code: `CASE-Backtrader回测/1-双均线策略.py` to `7-自定义策略.py`, `1b-摩擦成本与成交约束.py`

## Method

- **Data**: Moomoo forward-adjusted daily bars written to MySQL in C06. Symbols: `US.PLTR`, `US.IREN`, `US.NVDA`.
- **Two periods**:
  - **2025** (2025-01-02 to 2025-12-31): answers the course question.
  - **2026 out-of-sample** (2026-01-02 to 2026-10-16): tests whether the 2025 winner kept working the following year.
  - Each period warms up on the previous year's data so 30-day indicators are ready; no trading during warm-up.
- **Strategies**: the six course strategies with **the course's default parameters, not tuned to 2025**, to avoid hindsight optimisation. Each symbol also runs buy-and-hold as a benchmark.
- **Trading setup**: US$10,000 initial capital, 95% of capital per entry, whole shares.

```
MySQL market_daily → quantlib/strategies (six plug-in strategies, auto-loaded)
  → quantlib/backtest (Backtrader: next-open fills, US costs, slippage, volume cap)
  → metrics computed from daily NAV → charts + metrics.json
```

### Differences from the course version

| Item | Course version | This version |
|---|---|---|
| Transaction costs | Flat 0.02% (China A-shares) | US costs itemised: commission, platform fee, and on sells the SEC fee and FINRA TAF; regulatory rates follow the **trade date** (the SEC fee dropped to zero on 2025-05-14 and rose again on 2026-04-04) |
| Slippage | Not set in the main code | 5 bps on the opening fill, with 0/5/10/20 bps sensitivity analysis |
| Volume cap | Demonstrated in 1b (10% per bar) | Applied to every strategy |
| A-share rules | T+1 settlement, daily price limits | Not applicable to US stocks, removed |
| Share size | Fractional shares possible | Whole shares |
| Performance metrics | Backtrader analysers | Computed from daily NAV and cross-checked against QuantStats (Sharpe, Sortino and maximum drawdown match) |
| Benchmark | None | Buy-and-hold for every symbol, plus an out-of-sample test |

Cost sources: Moomoo Canada's published rates (commission US$0.0049/share, minimum US$0.99; platform fee US$0.005/share, minimum US$1.00); SEC fee rates from SEC advisories; the 2026 FINRA TAF rate is still to be confirmed against FINRA's official notice (see `config/costs.yaml`).

## Results

![2025 total return](outputs/figures/c13_returns_2025.png)

### 2025 (return / Sharpe / max drawdown / closed trades)

| Strategy | PLTR | IREN | NVDA |
|---|---|---|---|
| **Buy and hold** | +128.9% / 1.61 / 39.4% / — | +248.2% / 1.82 / 57.7% / — | +31.5% / 0.83 / 35.2% / — |
| Dual MA | +44.9% / 0.97 / 36.4% / 5 | +376.3% / 2.58 / 39.3% / 3 | +2.9% / 0.26 / 35.7% / 4 |
| MACD | +66.7% / 1.33 / 25.4% / 9 | +163.1% / 1.73 / 47.7% / 8 | −4.0% / 0.02 / 32.0% / 10 |
| RSI | No trades | +8.8% / 0.42 / 33.5% / 1 | **+46.6% / 1.69 / 13.7% / 1** |
| Bollinger | **+159.9% / 2.69 / 8.1% / 2** | −22.9% / −0.28 / 35.8% / 1 | +18.6% / 0.66 / 31.9% / 3 |
| Momentum | −0.2% / 0.27 / 50.1% / 6 | **+484.3% / 2.98 / 25.3% / 5** | +6.8% / 0.38 / 28.8% / 4 |
| MACD divergence | No trades | +32.3% / 1.07 / 20.2% / 2 | No trades |

Bold marks the highest-Sharpe strategy for each symbol.

![Highest-Sharpe strategy vs buy-and-hold, 2025](outputs/figures/c13_equity_winners_2025.png)

### 2026 out-of-sample: the 2025 winners did not persist

![Excess return heatmap](outputs/figures/c13_excess_heatmap.png)

| Symbol | 2025 winner | 2025 excess return | Same strategy in 2026 | 2026 buy-and-hold | 2026 excess return |
|---|---|---|---|---|---|
| PLTR | Bollinger | +31% | −2.9% | +6.2% | **−9%** |
| IREN | Momentum | +236% | −49.4% | −39.6% | **−10%** |
| NVDA | RSI | +15% | No trades (0%) | +11.3% | **−11%** |

### Transaction cost sensitivity (2025)

- On US$10,000 of capital, a full year of costs ranges from about US$4 to US$125. Moving from no costs to costs plus 20 bps of slippage cuts most strategies' returns by less than 6 percentage points (IREN momentum loses about 14 points because its capital had already multiplied several times), and **the strategy ranking for each symbol does not change**.
- The one exception is MACD on IREN: at 20 bps of slippage the return rises from +161% to +210%. On 2025-01-17 a gap up plus slippage left the 95% position short of cash, so the buy order was rejected and the strategy happened to skip a losing trade; every later trade size then changed too. This is **path dependence**, not a benefit of higher costs.

## A trader's view: which strategy best reflects 2025?

**There is no single answer; it depends on each stock's market regime that year.**

- **IREN: a persistent, strong trend, so trend-following won.** Buy-and-hold returned +248%; momentum and dual MA reached +484% and +376% with smaller maximum drawdowns. The mean-reversion strategies (Bollinger, RSI) kept "selling too early" in a strong trend, and Bollinger even lost 23%.
- **PLTR and NVDA: uptrends interrupted by sharp V-shaped sell-offs, so buying the dip with mean reversion won.** PLTR's Bollinger strategy traded only twice, buying the January and April lows; NVDA's RSI strategy made a single trade all year, buying the April oversold zone. [Inference] The April low coincides with the broad sell-off triggered by tariff news in early April.
- **But these "winners" mostly rest on a handful of lucky trades.** PLTR Bollinger's +160% comes from two trades and NVDA RSI's from one. With samples this small, even a high Sharpe ratio carries no statistical weight.

**The out-of-sample test confirms it:** in 2026 all three "2025 winners" trailed buy-and-hold by 9 to 11 percentage points. Choosing 2025's best strategy from 2025's results is hindsight, not a forecast you can trade.

## Risk checklist

- [x] Data leakage and look-ahead bias: signals use day-t close and fill at the day-t+1 open (verified by a unit test); no trading during warm-up. There were no splits in 2025–2026, so forward adjustment has little effect.
- [x] Survivorship bias: all three are watchlist stocks that still trade and rallied hard in 2025, so the conclusions **do not generalise to the wider market**.
- [x] Overfitting and out-of-sample testing: parameters are untuned; 6 strategies × 3 symbols = 18 attempts, and picking the best is itself a multiple-testing problem; the 2026 out-of-sample results show the winners did not persist.
- [x] Transaction costs and slippage: US costs itemised, with 0–20 bps sensitivity analysis.
- [x] Liquidity constraints and market impact: fills are capped at 10% of each bar's volume; at US$10,000 these three stocks are far more liquid than needed.

## Limitations and reflections

- Each symbol has only 1 to 10 trades, too few for any statistical conclusion about a single strategy. C17 and C21 should use more symbols or longer periods.
- A 95% position size gets rejected on gap ups, creating path dependence (for example IREN MACD). Later strategy check-ins will size with a cash buffer or calculate shares from the opening price.
- MACD divergence never triggered on PLTR or NVDA: the course's loose divergence condition (MACD > prior low × 0.8) rarely holds in an uptrend. The code follows the course as written.
- Cost rates are Moomoo Canada's published schedule; once my own account's plan is confirmed, add a profile to `config/costs.yaml` and re-run.
- (To be completed: personal reflections)
