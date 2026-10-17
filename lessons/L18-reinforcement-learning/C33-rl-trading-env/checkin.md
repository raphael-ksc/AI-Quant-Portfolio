---
id: C33
lesson: L18
title: 搭建 RL 交易環境
title_en: Building an RL Trading Environment
category: machine-learning
knowledge: [machine-learning, backtesting]
tags: [強化學習, Gymnasium]
symbols: []
status: todo
phase: 4
order: 14
flagship: false
date:
confidence:
source: 18-强化学习入门与择时策略/1-强化学习入门与择时策略.pdf p.28
outputs:
  figures: []
  metrics:
---

# C33 搭建 RL 交易環境

> ⚠️ 免責聲明：本頁所有策略分析與回測結果僅供教育與研究用途，不構成投資建議或收益保證。

## 題目要求

- 以 `510050.SH`（上證 50 ETF）為例，使用 Gymnasium 建立強化學習（RL，Reinforcement Learning）交易環境：
  - 建立 `StockTradingEnv` 自訂交易環境
  - 狀態空間：回看 5 日 OHLC，用過去 252 日收盤價做 Z-score 標準化，得到 20 維觀測向量
  - 動作空間：離散 3 個動作——持倉（0）、買入（1）、賣出（2）
  - 獎勵函數：4 種情況（空倉買入／空倉持有／持倉持有／持倉賣出）
  - 用隨機 Agent 跑 3 輪完整 Episode，驗證環境的 API 呼叫、獎勵計算、終止條件是否正常
- 對應 CASE：`CASE-基于RL的交易策略/1-搭建RL交易环境.py`
- 替換方案【推論】：標的改為美股 ETF（例如 `US.SPY`，使用前查證）；課程補充資料內建 A 股佣金與印花稅，美股需改用美股成本假設（無印花稅）。

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
