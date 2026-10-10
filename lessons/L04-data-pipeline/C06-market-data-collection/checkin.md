---
id: C06
lesson: L04
title: 行情數據採集
category: data-engineering
knowledge: [data-engineering]
tags: [Moomoo, MySQL, 日線]
symbols: []
status: todo
date:
confidence:
source: 4-数据获取与清洗/4-数据获取与清洗.pdf p.43
outputs:
  figures: []
  metrics:
---

# C06 行情數據採集

> ⚠️ 免責聲明：本頁所有策略分析與回測結果僅供教育與研究用途，不構成投資建議或收益保證。

## 題目要求

- 使用 QMT 進行行情數據採集，寫入 MySQL
- 資料表：`trade_stock_daily`（日線）
- 替換方案：原課程為 QMT，此處換成 Moomoo `request_history_kline`；資料表結構見 `CASE-数据采集/wucai_trade.sql`。

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
