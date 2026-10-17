---
id: C29
lesson: L14
title: 創建你的 RAG 問答
title_en: 'Building a RAG Q&A System'
category: ai-agents
knowledge: [ai-agents, fundamentals]
tags: [RAG, LangChain, Faiss]
symbols: []
status: todo
phase: 6
order: 33
flagship: false
date:
confidence:
source: 14-RAG投研系统搭建/1-RAG投研系统搭建.pdf p.85
outputs:
  figures: []
  metrics:
---

# C29 創建你的 RAG 問答

> ⚠️ 免責聲明：本頁所有策略分析與回測結果僅供教育與研究用途，不構成投資建議或收益保證。

## 題目要求

- 結合你的業務場景，建立 RAG（檢索增強生成，Retrieval-Augmented Generation）問答（LangChain + DeepSeek + Faiss）：
  - Step 1：收集整理知識庫（例如財務報告 PDF）
  - Step 2：從 PDF 擷取文字，並記錄每行文字對應的頁碼
  - Step 3：處理文字並建立向量儲存
  - Step 4：執行相似度搜尋，找出與查詢相關的文件
  - Step 5：使用問答鏈回答使用者問題
  - Step 6：顯示每個文件區塊的來源頁碼（課程註明目前頁碼來源有問題，需要自行修正）
- 對應 CASE：`Case-ChatPDF-Faiss/`
- 替換方案【推論】：財報改用自選股的 10-K（SEC EDGAR 公開資料）；LLM 供應商待定。

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
