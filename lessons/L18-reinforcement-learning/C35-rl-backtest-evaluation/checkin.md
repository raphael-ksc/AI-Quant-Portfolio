---
id: C35
lesson: L18
title: 策略回測與評估
title_en: RL Strategy Backtest and Evaluation
category: machine-learning
knowledge: [machine-learning, backtesting, risk-management]
tags: [DQN, 樣本外測試]
symbols: []
status: todo
phase: 4
order: 16
flagship: false
date:
confidence:
source: 18-强化学习入门与择时策略/1-强化学习入门与择时策略.pdf p.73
outputs:
  figures: []
  metrics:
---

# C35 策略回測與評估

> ⚠️ 免責聲明：本頁所有策略分析與回測結果僅供教育與研究用途，不構成投資建議或收益保證。

## 題目要求

- 載入 C34 訓練好的 DQN 模型（`dqn_best.pth`）進行回測：
  - 在樣本外區間 2025-07-01 ～ 2026-04-09 回測
  - 回測時 epsilon = 0（純利用、不探索）
  - 比較 DQN 與買入持有（Buy and Hold）
- 課程範例結果（`510050.SH`，**非本人結果**）：DQN 總報酬 +13.75%、夏普比率 0.99、最大回撤 10.28%；買入持有總報酬 +14.62%、夏普比率 0.78、最大回撤 11.42%
- 對應 CASE：`CASE-基于RL的交易策略/3-策略回测与评估.py`
- 注意：課程補充資料指出訓練集報酬 +254%，樣本外大幅縮水，是過度擬合的典型案例。

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
