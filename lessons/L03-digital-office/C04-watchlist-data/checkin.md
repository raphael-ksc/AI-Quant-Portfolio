---
id: C04
lesson: L03
title: 獲取你的自選股數據
category: data-engineering
knowledge: [data-engineering]
tags: [Moomoo, yfinance, 日線, 分鐘線, 財務數據]
symbols: []
status: wip
date:
confidence:
source: 3-打造数字化办公室/3-基础设施打造（构建数字化办公室）.pdf p.81
outputs:
  figures: []
  metrics:
---

# C04 獲取你的自選股數據

> ⚠️ 免責聲明：本頁所有策略分析與回測結果僅供教育與研究用途，不構成投資建議或收益保證。

## 題目要求

- 針對自選股獲取：
  - 日線，例如 20240101 至 20251231
  - 分鐘線，例如 20260206 的分鐘 K 線
  - 財務數據（tushare、akshare 或 QMT 任一）
- 目前進度：`homework_multi_source/` 已以 Moomoo（PLTR、IREN）＋ yfinance（BHP.AX）完成日線與財務數據抓取，並有 Flask 儀表板。
- 待確認：分鐘線是否已完成？（yfinance `1m` 僅能抓近 7 天，指定歷史日期的分鐘線需改用 Moomoo）

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
