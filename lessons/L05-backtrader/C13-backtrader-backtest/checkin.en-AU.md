# C13 Building a Stock Backtest

> ⚠️ Disclaimer: all strategy analysis and backtest results on this page are for educational and research purposes only and do not constitute investment advice or any guarantee of returns.

## Requirements

- Which trading strategy best suited your watchlist stock in 2025?
  - Use a stock from your own watchlist, or Kweichow Moutai as in the course
  - Candidate strategies: dual moving average, MACD, RSI, Bollinger Bands, momentum, MACD bullish divergence
  - Why does your chosen strategy best reflect that year's market behaviour?
- Course example (Moutai 2025; initial capital 1,000,000, commission 0.02%, 95% position size): total return −8.94%, maximum drawdown 10.36% (course figures, not my own backtest results)
- Course CASE files: `1-双均线策略.py` to `7-自定义策略.py`, plus `1b-摩擦成本与成交约束.py` (transaction costs and fill constraints)
- ⚠️ Risk: a single year and a single symbol carry a high risk of overfitting; transaction costs and slippage must be modelled.

## Method

(To be completed: data source, symbols, period, strategy logic)

## Results

(To be completed: charts in `outputs/figures/`, metrics in `outputs/metrics.json`)

## Risk checklist

- [ ] Data leakage and look-ahead bias
- [ ] Survivorship bias
- [ ] Overfitting and out-of-sample testing
- [ ] Transaction costs and slippage
- [ ] Liquidity constraints and market impact

## Limitations and reflections

(To be completed)
