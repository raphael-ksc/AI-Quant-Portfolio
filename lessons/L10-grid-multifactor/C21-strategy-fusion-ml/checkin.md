---
id: C21
lesson: L10
title: 策略融合與 ML 增強
title_en: Strategy Fusion and ML Enhancement
category: strategies
knowledge: [strategies, machine-learning]
tags: [LightGBM, Walk-Forward, 特徵重要性]
symbols: []
status: todo
phase: 3
order: 10
flagship: true
date:
confidence:
source: 10-网格与多因子/10-网格与多因子.pdf p.95
outputs:
  figures: []
  metrics:
---

# C21 策略融合與 ML 增強

> ⚠️ 免責聲明：本頁所有策略分析與回測結果僅供教育與研究用途，不構成投資建議或收益保證。

## 題目要求

- 針對你的股票池進行：
  - 用網格適配因子打分，選出適合做網格的標的
  - 對選出的標的運行中樞網格回測
  - 構建 13 維特徵，運行 LightGBM Walk-Forward 回測
  - 分析特徵重要性，與纏論 ML／海龜 ML 的特徵重要性對比
- Thinking：為你的投資組合設計策略方案——哪些標的適合網格？哪些適合趨勢跟蹤？如何用因子選股優化標的選擇？
- 對應 CASE：`CASE-网格与多因子/7-因子选股+中枢网格.py`、`8-ML增强多因子.py`

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
