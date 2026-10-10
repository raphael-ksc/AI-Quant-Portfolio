---
id: C22
lesson: L11
title: 自選股因子分析
title_en: Watchlist Factor Analysis
category: machine-learning
knowledge: [machine-learning, fundamentals]
tags: [RankIC, Spearman, 因子分析]
symbols: []
status: todo
phase: 4
order: 11
flagship: false
date:
confidence:
source: 11-机器学习因子挖掘/11-机器学习因子挖掘.pdf p.32
outputs:
  figures: []
  metrics:
---

# C22 自選股因子分析

> ⚠️ 免責聲明：本頁所有策略分析與回測結果僅供教育與研究用途，不構成投資建議或收益保證。

## 題目要求

- 針對股票池進行因子分析：
  - 從 MySQL 拉日 K，呼叫 `calc_features` 生成技術面因子
  - 拉財務表，呼叫 `calc_fundamental_features` 合併基本面因子
  - 查看 `feature_engine` 中的因子分類（`FACTOR_TAXONOMY`）
  - 對每個因子與次日收益率算 RankIC（Spearman），彙總排名與按類別統計
- 通過因子分析，你的自選股有怎樣的規律？
- 對應 CASE：`CASE-机器学习因子挖掘/1-贵州茅台因子分析.py`、`feature_engine.py`

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
