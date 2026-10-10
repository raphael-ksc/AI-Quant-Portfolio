# C08 Macroeconomic Data Collection

> ⚠️ Disclaimer: all strategy analysis and backtest results on this page are for educational and research purposes only and do not constitute investment advice or any guarantee of returns.

## Requirements

- Collect macroeconomic data (the course uses akshare for China A-share macro series)
- Target table: `trade_macro_indicator` (monthly macro indicators)
- Adaptation for US equities: a source such as FRED (Federal Reserve Economic Data) is a candidate; its API and licence terms must be verified before implementation.
- Together with C11, this forms one flagship piece: turning macro judgement into structured, time-stamped data that strategies can consume.

## Method

(To be completed: indicators, release-date handling, storage schema)

## Results

(To be completed)

## Risk checklist

- [ ] Data leakage and look-ahead bias (use release dates, not reference periods; account for revisions)
- [ ] Survivorship bias
- [ ] Overfitting and out-of-sample testing
- [ ] Transaction costs and slippage
- [ ] Liquidity constraints and market impact

## Limitations and reflections

(To be completed)
