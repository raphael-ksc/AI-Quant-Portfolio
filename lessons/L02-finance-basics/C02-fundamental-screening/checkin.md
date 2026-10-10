---
id: C02
lesson: L02
title: 制定你的基本面選股
category: fundamentals
knowledge: [fundamentals]
tags: [ROE, 負債率, Moomoo]
symbols: []
status: todo
date:
confidence:
source: 2-金融基础速通/2-金融基础速通.pdf p.53
outputs:
  figures: []
  metrics:
---

# C02 制定你的基本面選股

> ⚠️ 免責聲明：本頁所有策略分析與回測結果僅供教育與研究用途，不構成投資建議或收益保證。

## 題目要求

- 依個人偏好制定基本面選股策略，例如：
  - 排除：ST 股、金融行業（銀行／保險／證券等）
  - ROE：連續 2 年（2023、2024 年報）ROE ≥ 15%
  - 負債率：資產負債率 ≤ 50%
  - 品質條件：例如淨利潤同比增長 ≥ 0%
- **輸出你的基本面選股池**
- 替換方案：Moomoo `get_financials_statements`；ROE 用 `Net Income to Parent Company / Total Equity`（見 `CLAUDE.md` 第 8 節）。美股無「ST 股」概念，需自訂替代排除條件。
- ⚠️ 風險：財報接口無公告日期，用年報篩選時注意前視偏差（Look-ahead Bias）。

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
