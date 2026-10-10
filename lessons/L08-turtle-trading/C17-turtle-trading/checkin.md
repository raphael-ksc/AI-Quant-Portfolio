---
id: C17
lesson: L08
title: 海龜交易策略
category: strategies
knowledge: [strategies, machine-learning, backtesting]
tags: [海龜, ADX, ML 增強]
symbols: []
status: todo
date:
confidence:
source: 8-海龟交易法则/8-海龟交易法则.pdf p.64
outputs:
  figures: []
  metrics:
---

# C17 海龜交易策略

> ⚠️ 免責聲明：本頁所有策略分析與回測結果僅供教育與研究用途，不構成投資建議或收益保證。

## 題目要求

- 針對自選股使用海龜交易策略：
  - 使用自適應方法
  - 使用 ML 增強方法
  - 嘗試修改 ADX 閾值（從 15 改為 20 或 25），觀察對交易次數和收益的影響
- Thinking：同時使用 ADX 過濾 + ML 預測，雙重過濾會更好嗎？還是會過濾掉太多機會？
- 對應 CASE：`CASE-海龟交易法则/1-经典海龟策略.py` ～ `4-ML增强海龟策略.py`

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
