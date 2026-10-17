---
id: C31
lesson: L16
title: 輿情感知與事件驅動
title_en: Sentiment Sensing and Event-Driven Signals
category: ai-agents
knowledge: [ai-agents, data-engineering, risk-management]
tags: [情感分析, 恐慌指數, Polymarket, Nanobot]
symbols: []
status: todo
phase: 5
order: 19
flagship: false
date:
confidence:
source: 16-舆情感知与事件驱动/1-舆情感知与事件驱动.pdf p.99
outputs:
  figures: []
  metrics:
---

# C31 輿情感知與事件驅動

> ⚠️ 免責聲明：本頁所有策略分析與回測結果僅供教育與研究用途，不構成投資建議或收益保證。

## 題目要求

- 建立 AI 投研中的 `sentiment-analysis` 技能，完成以下任務：
  - 執行恐慌指數監控，查看目前全球市場情緒（VIX + 10 年期公債）
  - 執行 Polymarket 監控，搜尋一個你關心的地緣政治議題
  - 選一檔你關注的股票，取得最近 7 天的新聞並做情感分析
  - 執行事件偵測，查看是否有重大事件
  - 如果偵測到事件，嘗試聯動 `read-pdf` 和 `write-report` 做深度分析
- 對應 CASE：`CASE-AI量化助手（nanobot）/skills/sentiment-analysis/`
- 替換方案【推論】：新聞來源改為美股；恐慌指數與 Polymarket 可直接沿用。

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
