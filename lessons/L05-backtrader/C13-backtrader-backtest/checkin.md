---
id: C13
lesson: L05
title: 搭建你的股票交易回測
category: backtesting
knowledge: [backtesting, technical-analysis, risk-management]
tags: [Backtrader, 雙均線, MACD, RSI, 布林帶, 動量]
symbols: []
status: todo
date:
confidence:
source: 5-掌握回测引擎 Backtrader/5-掌握回测引擎Backtrader.pdf p.61
outputs:
  figures: []
  metrics:
---

# C13 搭建你的股票交易回測

> ⚠️ 免責聲明：本頁所有策略分析與回測結果僅供教育與研究用途，不構成投資建議或收益保證。

## 題目要求

- 你的自選股在 2025 年採用哪種交易策略是適合的？
  - 可用自選股，也可用貴州茅台
  - 候選策略：雙均線、MACD、RSI、布林帶、動量、MACD 底背離
  - 你為什麼覺得哪種策略最能體現當年的交易行情？
- 課件示例（茅台 2025，初始資金 1,000,000、手續費萬分之 2、倉位 95%）：總收益率 −8.94%、最大回撤 10.36%（課件數據，非本人回測結果）
- 對應 CASE：`CASE-Backtrader回测/1-双均线策略.py` ～ `7-自定义策略.py`、`1b-摩擦成本与成交约束.py`
- ⚠️ 風險：單一年度、單一標的 → 過度擬合（Overfitting）風險高；需設定交易成本與滑價（Slippage）。

## 方法

（待填：資料來源、標的、期間、策略邏輯）

## 結果

（待填：圖表放 `outputs/figures/`，指標放 `outputs/metrics.json`）

## 風險檢查表

- [ ] 資料洩漏（Data Leakage）與前視偏差（Look-ahead Bias）
- [ ] 倖存者偏差（Survivorship Bias）
- [ ] 過度擬合（Overfitting）與樣本外測試（Out-of-sample Testing）
- [ ] 交易成本（Transaction Costs）與滑價（Slippage）
- [ ] 流動性限制（Liquidity Constraints）與市場衝擊（Market Impact）

## 限制與心得

（待填）
