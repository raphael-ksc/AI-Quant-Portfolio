---
id: C30
lesson: L15
title: 撰寫 AI 投研報告
title_en: Writing an AI Equity Research Report
category: ai-agents
knowledge: [ai-agents, fundamentals]
tags: [DeepAgents, Skill, 五步法]
symbols: []
status: todo
phase: 5
order: 22
flagship: false
date:
confidence:
source: 15-智能研报生成/1-智能研报生成.pdf p.109
outputs:
  figures: []
  metrics:
---

# C30 撰寫 AI 投研報告

> ⚠️ 免責聲明：本頁所有策略分析與回測結果僅供教育與研究用途，不構成投資建議或收益保證。

## 題目要求

- 建立 AI 投研報告撰寫 Agent，完成以下任務：
  - 選擇一家你感興趣的上市公司
  - 先用 `preprocess.py` 或 `read-pdf` 技能讀取其最新年報
  - 在終端機執行 `python agent.py`，輸入「幫我撰寫 XX 深度投研報告」
  - 觀察 Agent 的工具呼叫過程：它選了哪些工具？搜尋了幾輪？
- 重點評估研報品質：
  - 資訊差：是否找到被市場忽視的關鍵數據？
  - 邏輯差：是否揭示了市場的錯誤推理？
  - 風險閉環：是否明確指出哪個假設出錯會導致結論崩塌？
- 對應 CASE：`CASE-智能研报生成/`（`agent.py`、`preprocess.py`、`skills/`）
- 替換方案【推論】：公司改為美股自選股；akshare 資料改用 Moomoo／yfinance。

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
