---
id: C15
lesson: L07
title: 打造你的量化交易同事
category: ai-agents
knowledge: [ai-agents]
tags: [Hermes, LLM, Skill]
symbols: []
status: todo
date:
confidence:
source: 7-Hermes：搭建你的量化交易同事/7-Hermes：搭建你的量化交易同事.pdf p.73
outputs:
  figures: []
  metrics:
---

# C15 打造你的量化交易同事

> ⚠️ 免責聲明：本頁所有策略分析與回測結果僅供教育與研究用途，不構成投資建議或收益保證。

## 題目要求

- 把同事跑起來並用上技能：
  - 一條命令裝好 Hermes，`hermes model` 接上 Qwen，完成第一次對話
  - 裝好 3 個技能包：複製進 `%LOCALAPPDATA%\hermes\skills\` → 替換路徑佔位符 → 設環境變數 `WUCAI_SQL_PASSWORD`，`hermes skills list` 看到皆為 enabled
  - 對話驗證三條鏈路都通：取茅台最近 60 天日線（akshare-kline）→ 算 MACD（talib）→ 跑雙均線回測（backtrader）
- 替換方案：資料技能可改接 Moomoo（自選美股）。
- ⚠️ 安全：`WUCAI_SQL_PASSWORD` 等密碼只能放環境變數或 `.env`，絕不可 commit。

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
