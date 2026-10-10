---
id: C20
lesson: L10
title: 多因子選股（進階）
title_en: Multi-factor Stock Selection (Advanced)
category: fundamentals
knowledge: [fundamentals, backtesting, risk-management]
tags: [多因子, IC, 月度調倉, Top-N]
symbols: []
status: todo
phase: 6
order: 20
flagship: false
date:
confidence:
source: 10-网格与多因子/10-网格与多因子.pdf p.67
outputs:
  figures: []
  metrics:
---

# C20 多因子選股（進階）

> ⚠️ 免責聲明：本頁所有策略分析與回測結果僅供教育與研究用途，不構成投資建議或收益保證。

## 題目要求

- 針對你的股票池（也可以是全量 A 股）進行多因子選股：
  - 計算技術因子，分析 IC 值
  - 用 8 因子打分體系對全市場股票排名
  - 運行月度調倉回測，選擇最佳的 Top-N
  - 對比多因子選股 vs 小市值輪動的效果
- 你的自選股在因子打分中排名如何？
- 對應 CASE：`CASE-网格与多因子/4-多因子评价框架.py` ～ `6-小市值轮动策略.py`
- ⚠️ 風險：全市場回測需注意倖存者偏差（Survivorship Bias）——股票池需包含已下市股票。

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
