---
id: C32
lesson: L17
title: 實盤交易介面（Moomoo 模擬盤）
title_en: Trading API Integration (Moomoo Paper Trading)
category: risk-management
knowledge: [risk-management, strategies]
tags: [Moomoo, 模擬盤, 下單]
symbols: []
status: todo
phase: 5
order: 23
flagship: false
date:
confidence:
source: 17-Agent实战与QMT实盘接口/1-Agent实战与QMT实盘.pdf p.36
outputs:
  figures: []
  metrics:
---

# C32 實盤交易介面（Moomoo 模擬盤）

> ⚠️ 免責聲明：本頁所有策略分析與回測結果僅供教育與研究用途，不構成投資建議或收益保證。

## 題目要求

- 原課程：使用 QMT 完成以下任一任務，熟悉實盤操作：
  - 連接帳戶與資訊查詢
  - 下單與撤單
  - 回呼（Callback）／輪詢（Polling）機制
  - 策略訊號轉實盤訂單
- 對應 CASE：`CASE-QMT实盘交易/1-query_account.py` ～ `5-signal_to_order.py`
- **原課程為 QMT，此處已換成 Moomoo 版本**：
  - 連線改用 OpenD + `OpenSecTradeContext`，一律使用 `TrdEnv.SIMULATE`（模擬盤），不連真實帳戶（CLAUDE.md 第 7 節）
  - QMT 透過本機 miniQMT 與資金帳號連線；Moomoo 是登入 OpenD 後，下單前需解鎖交易
  - 實際 API 簽名與回呼機制，實作前先查證 Moomoo 官方文件

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
