---
id: C01
lesson: L01
title: 貴州茅台的 2025 年交易策略
category: backtesting
knowledge: [backtesting, technical-analysis]
tags: [MACD, 雙均線, 網格]
symbols: []
status: todo
date:
confidence:
source: 1-量化世界的生存法则/1-量化世界的生存法则.pdf p.67
outputs:
  figures: []
  metrics:
---

# C01 貴州茅台的 2025 年交易策略

> ⚠️ 免責聲明：本頁所有策略分析與回測結果僅供教育與研究用途，不構成投資建議或收益保證。

## 題目要求

- 針對貴州茅台，編寫 MACD 交易策略／網格策略：
  1. 配置環境（安裝 Python、IDE）
  2. 制定 MACD 交易策略，例如 MA5 與 MA20，或 MA12 與 MA26
  3. 你會選擇怎樣的交易策略？
- 對應 CASE：`CASE-贵州茅台的2025年交易策略/2-macd_strategy_2025.py`、`3-grid_strategy_2025.py`
- 替換方案：資料下載 `1-qmt_download_data.py` → 改 Moomoo `request_history_kline`（自選美股）。
- 作品集亮點：策略 vs 買入持有（Buy & Hold）的淨值曲線對比圖。

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
