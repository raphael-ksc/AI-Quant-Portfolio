---
id: C26
lesson: L13
title: 實盤績效報告
title_en: Trading Performance Report
category: risk-management
knowledge: [risk-management, backtesting]
tags: [QuantStats, VaR, CVaR, 模擬盤]
symbols: []
status: todo
phase: 5
order: 24
flagship: false
date:
confidence:
source: 13-QuantStats绩效分析与报告/13-QuantStats绩效分析与报告.pdf p.96
outputs:
  figures: []
  metrics:
---

# C26 實盤績效報告

> ⚠️ 免責聲明：本頁所有策略分析與回測結果僅供教育與研究用途，不構成投資建議或收益保證。

## 題目要求

- 針對你的實盤交易，輸出績效報告：
  - 匯出歷史交易紀錄 csv
  - 使用 QuantStats 進行績效分析
  - 使用 SVD 對你的股票進行分析
- 思考：你的股票是走獨立行情，還是跟隨大盤？
- 對應 CASE：`CASE-QuantStats绩效分析与报告/3-实盘交易绩效分析.py`、`4-实盘交易绩效分析Plus.py`、`report_engine.py`
- ⚠️ 公開 repo 規則（CLAUDE.md 第 10.4 節）：真實交易紀錄、持倉與金額不可公開。本題改用 Moomoo **模擬盤**成交紀錄（來自 C32），或只公開不含金額的比率指標。

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
