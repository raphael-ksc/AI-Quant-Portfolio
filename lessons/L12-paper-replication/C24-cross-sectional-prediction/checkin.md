---
id: C24
lesson: L12
title: 股票截面預測
title_en: Cross-sectional Return Prediction
category: machine-learning
knowledge: [machine-learning, risk-management]
tags: [XGBoost, IC/ICIR, 截面預測, MASTER]
symbols: []
status: todo
phase: 6
order: 30
flagship: false
date:
confidence:
source: 12-论文复现与策略进化/12-论文复现与策略进化.pdf p.94
outputs:
  figures: []
  metrics:
---

# C24 股票截面預測

> ⚠️ 免責聲明：本頁所有策略分析與回測結果僅供教育與研究用途，不構成投資建議或收益保證。

## 題目要求

- 針對股票池進行截面預測（Cross-sectional Prediction），標籤例如未來 5 天的歸一化收益率：
  - Step 1：載入 50 只大盤股（原課程為 A 股）
  - Step 2：計算 52 維技術因子
  - Step 3：單因子 IC 分析——對每個因子計算截面 IC / ICIR，找出最有預測力的因子
  - Step 4：滾動 XGBoost 截面預測——120 天訓練窗口，每 5 天預測一次，共 120 次
  - Step 5：IC / ICIR 評估
- 你的自選股在未來 5 天的預期收益率如何？
- 對應 CASE：`CASE-论文复现与策略进化/1-MASTER数据与因子.py` ～ `3-XGBoost截面预测.py`
- 延伸：MASTER 論文（Market-Guided Stock Transformer）復現，見 `MASTER-master/`。

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
