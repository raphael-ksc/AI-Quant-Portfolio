---
id: C36
lesson: L18
title: 智能拆單
title_en: Smart Order Execution with RL
category: machine-learning
knowledge: [machine-learning, risk-management]
tags: [PPO, TWAP, VWAP, 市場衝擊]
symbols: []
status: todo
phase: 4
order: 17
flagship: false
date:
confidence:
source: 18-强化学习入门与择时策略/1-强化学习入门与择时策略.pdf p.94
outputs:
  figures: []
  metrics:
---

# C36 智能拆單

> ⚠️ 免責聲明：本頁所有策略分析與回測結果僅供教育與研究用途，不構成投資建議或收益保證。

## 題目要求

- 以買入 10 萬股（約占日均成交量 1.12%）為例，建立 `OrderExecutionEnv` 拆單環境，一天分 48 個時段：
  - 狀態空間 5 維（剩餘量／剩餘時間／價格偏移／波動率／VWAP 偏離），動作空間連續（執行比例 0～1）
  - 使用 Stable-Baselines3 的 PPO 演算法訓練 50,000 步，與 TWAP／VWAP 基準做 100 次模擬比較
  - 課程結論：PPO 學會自適應拆成約 10 片執行（而不是 TWAP 的 48 片平均拆），集中在衝擊小的時段執行
- 對應 CASE：`CASE-基于RL的交易策略/4-智能拆单环境.py`、`5-TWAP与RL拆单对比.py`
- 依 CLAUDE.md 第 4 節裁決，以 PDF 為準；課程補充 HTML 的版本為狀態 9 維、訓練 500,000 步。

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
