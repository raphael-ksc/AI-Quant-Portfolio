---
id: C23
lesson: L11
title: 股票漲跌預測
title_en: Next-day Direction Prediction
category: machine-learning
knowledge: [machine-learning, risk-management]
tags: [XGBoost, LightGBM, Purged K-Fold]
symbols: []
status: todo
phase: 4
order: 12
flagship: false
date:
confidence:
source: 11-机器学习因子挖掘/11-机器学习因子挖掘.pdf p.91
outputs:
  figures: []
  metrics:
---

# C23 股票漲跌預測

> ⚠️ 免責聲明：本頁所有策略分析與回測結果僅供教育與研究用途，不構成投資建議或收益保證。

## 題目要求

- 針對股票池進行次日漲跌預測：
  - 使用 XGBoost 或 LightGBM
  - 提取 52 個技術因子 + 4 個基本面因子
  - 構建 target：次日漲跌或 5 日後漲跌
  - 使用 Purged K-Fold 對驗證集的未來數據進行驗證
- 漲跌預測器準確率如何？有哪些方式可以提升預測準確率？
- 對應 CASE：`CASE-机器学习因子挖掘/3-XGBoost涨跌预测.py`、`4-LightGBM对比与调参.py`
- ⚠️ 風險：資料洩漏（Data Leakage）是此題重點；財務因子需以公告日（非報告期結束日）對齊。

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
