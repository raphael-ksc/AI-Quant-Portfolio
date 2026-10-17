---
id: C25
lesson: L13
title: SVD 因子分析
title_en: SVD Factor Analysis
category: machine-learning
knowledge: [machine-learning, risk-management]
tags: [SVD, 市場狀態, 因子分析]
symbols: []
status: todo
phase: 4
order: 13
flagship: false
date:
confidence:
source: 13-QuantStats绩效分析与报告/13-QuantStats绩效分析与报告.pdf p.77
outputs:
  figures: []
  metrics:
---

# C25 SVD 因子分析

> ⚠️ 免責聲明：本頁所有策略分析與回測結果僅供教育與研究用途，不構成投資建議或收益保證。

## 題目要求

- 針對你的股票池（也可以是全市場股票）進行 SVD（奇異值分解，Singular Value Decomposition）因子分析：
  - 對收益率矩陣做 SVD 分解，找出市場的主要驅動力
  - 市場狀態監控：用滾動 SVD 監控第一因子的變異數占比，判斷市場處於齊漲齊跌、板塊分化，還是個股行情階段
- 思考：你的自選股是走獨立行情，還是跟隨大盤？
- 對應 CASE：`CASE-QuantStats绩效分析与报告/2-SVD因子挖掘与分析.py`
- 替換方案【推論】：股票池改為美股（自選股 + 大型股子集）；成分股需用當期名單，避免倖存者偏差。

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
