---
id: C34
lesson: L18
title: 搭建 DQN 擇時策略
title_en: DQN Market-Timing Strategy
category: machine-learning
knowledge: [machine-learning, strategies]
tags: [DQN, 強化學習, 擇時]
symbols: []
status: todo
phase: 4
order: 15
flagship: false
date:
confidence:
source: 18-强化学习入门与择时策略/1-强化学习入门与择时策略.pdf p.65
outputs:
  figures: []
  metrics:
---

# C34 搭建 DQN 擇時策略

> ⚠️ 免責聲明：本頁所有策略分析與回測結果僅供教育與研究用途，不構成投資建議或收益保證。

## 題目要求

- 以 `StockTradingEnv` 為訓練環境，建立 DQN Agent：
  - Q 網路結構，例如 20 → 64 → 64 → 3
  - 訓練 500 輪 Episode
  - 使用三個關鍵技巧：經驗回放（buffer = 10000）、目標網路（每 100 步同步）、Epsilon-Greedy（1.0 衰減到 0.01）
  - 訓練過程中觀察 Reward、Loss 與報酬率的變化
- 對應 CASE：`CASE-基于RL的交易策略/2-DQN择时策略.py`

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
