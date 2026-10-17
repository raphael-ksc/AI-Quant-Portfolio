---
id: C06
lesson: L04
title: 行情數據採集
title_en: Market Data Collection
category: data-engineering
knowledge: [data-engineering]
tags: [Moomoo, yfinance, MySQL, Docker, 日線, 增量更新]
symbols: [US.PLTR, US.IREN, US.NVDA]
status: wip
phase: 1
order: 2
flagship: false
date:
confidence:
source: 4-数据获取与清洗/4-数据获取与清洗.pdf p.43
outputs:
  figures: []
  metrics: outputs/metrics.json
---

# C06 行情數據採集

> ⚠️ 免責聲明：本頁所有策略分析與回測結果僅供教育與研究用途，不構成投資建議或收益保證。

## 題目要求

- 使用 QMT 進行行情數據採集，寫入 MySQL
- 資料表：`trade_stock_daily`（日線）
- **原課程為 QMT，此處已換成 Moomoo 版本**：QMT 的 `get_market_data_ex` 改為 `quantlib/data` 的 Moomoo 資料源（`request_history_kline`），另提供 yfinance 給沒有 Moomoo 帳號的人重現。

## 方法

- **標的**：`US.PLTR`、`US.IREN`、`US.NVDA`（設定見 `config/symbols.yaml`），2023-01-03 至 2026-10-16。
- **流程**：

```
config/symbols.yaml → DataSource（Moomoo / yfinance）→ validate_bars
  → IncrementalPlanner（只補缺的日期 + 回看 5 天比對）→ MySQL market_daily
  → ingest_runs（執行紀錄）→ VIEW trade_stock_daily（相容課程程式碼）
```

- **資料庫結構**（`db/schema.sql`）：
  - `market_daily`：主鍵 `(symbol, trade_date, adjust, source)`，前復權（qfq）與不復權（none）並存，Moomoo 與 yfinance 也並存，方便交叉比對。
  - `instruments`：標的主檔，預留 `is_active`、`delisted_date`，之後做全市場研究時可納入已下市股票。
  - `ingest_runs`：每次執行的資料源、筆數、狀態與錯誤訊息。
  - VIEW `trade_stock_daily`：欄位名稱對齊課程（`stock_code`、`open_price`…），第 13、18 課的 `data_loader.py` 可以直接讀。
- **兩種執行環境**，同一份程式，切換時只改 `.env` 的 `MYSQL_PORT`：
  - 本機 MySQL80（3306）：日常研究用。
  - Docker（3307）：`docker compose up -d` 自動建表，搭配 `--source yfinance`，任何人都能重現。
- **執行**：`lessons/L04-data-pipeline/C06-market-data-collection/src/ingest_daily.py`；共用程式在 `quantlib/db/`。

### 和課程版本不同的地方

| 問題 | 課程版本 | 本人版本 |
|---|---|---|
| 價格精度 | `DECIMAL(10,2)` | `DECIMAL(18,6)`：前復權後的價格常有 3 位以上小數，只留 2 位會失真 |
| 前復權基準 | 只往後補新日期 | 每次回看最近 5 個已存交易日；收盤價對不上，就代表分割或配息改變了復權基準，整段重抓 |
| 當天未收盤的 K 線 | 以「今天」判斷是否已最新 | 以美東時間判斷「最後已收盤交易日」，盤中執行不會寫入當天未完成的 K 線 |
| 復權方式 | 只存前復權 | 前復權與不復權都存；回測需要「當時看到的價格」時用不復權 |
| 換手率 | 用流通股本自行計算 | 直接用 Moomoo 回傳的 `turnover_rate`（比例）；VIEW 換算成課程用的百分比 |
| 寫入 | `ON DUPLICATE KEY UPDATE` + `VALUES()` | 同樣批次寫入，改用 MySQL 8 的 `AS new` 別名寫法（`VALUES()` 已棄用） |
| 執行紀錄 | 只印在終端機 | 寫入 `ingest_runs`，單一標的失敗時狀態記為 `partial`，不中斷其他標的 |

## 結果

| 項目 | 結果 |
|---|---|
| 本機 MySQL80 首次全量寫入（Moomoo） | 3 檔 × 2 種復權 × 951 個交易日 = **5,706 筆**，狀態 success |
| 第二次執行 | 6 組全部 `up_to_date`，寫入 0 筆（重複執行不會重複寫入） |
| 刪掉 PLTR 最後 3 天後重跑 | 從 2026-10-07 回看，補寫 8 筆（5 天重疊 + 3 天新資料），重疊日收盤價一致 |
| Docker（3307）+ yfinance | 自動建表；PLTR、NVDA 各 951 個交易日，寫入 3,804 筆，VIEW 讀取正常 |
| Moomoo 成交額、換手率 | 全部 5,706 筆皆有值；yfinance 不提供，存為 NULL |
| 歷史 K 線額度 | 新增 NVDA 用掉 1 檔（共 3 / 100 檔，30 天內） |
| 測試 | 單元測試 27 項（不需資料庫）＋ MySQL 整合測試 6 項；CI 每次部署都會啟動 MySQL 容器跑整合測試 |

**NVDA 的 1 拆 10 驗證了為什麼兩種復權都要存**：2024-06-07（拆股前最後一天）不復權收盤價約為前復權的 10.03 倍。10 倍來自拆股；額外約 0.28% 的差異原因尚未查證（【推論】可能是配息調整或 Moomoo 的復權算法，之後與 yfinance 比對再確認）。只存前復權的話，看不出當時市場上的實際價格。

詳細筆數與日期範圍見 [`outputs/metrics.json`](outputs/metrics.json)（只含筆數與日期，不含價格）。

## 風險檢查表

- [x] 資料洩漏（Data Leakage）與前視偏差（Look-ahead Bias）：不寫入未收盤的 K 線；前復權價格會隨未來的公司行動改變，所以同時保留不復權資料，回測可依需要選擇。
- [x] 倖存者偏差（Survivorship Bias）：本題只有 3 檔自選股；`instruments` 預留下市欄位，全市場研究時必須納入已下市股票。
- [ ] 過度擬合（Overfitting）與樣本外測試（Out-of-sample Testing）：本題不涉及策略。
- [ ] 交易成本（Transaction Costs）與滑價（Slippage）：本題不涉及交易。
- [x] 流動性限制（Liquidity Constraints）與市場衝擊（Market Impact）：保存成交量、成交額與換手率，之後的策略題可以用來設定流動性門檻。

## 限制與心得

- 「最後已收盤交易日」只排除週末，不處理美股國定假日。假日當天資料源不會回傳 K 線，所以不影響正確性，只是會多一次查詢。
- 課程每天 15:30 自動執行；美股收盤是台北時間凌晨 4–5 點，本題先手動執行。要自動化可以用 Windows 工作排程器，每天台北時間 06:00 執行 `ingest_daily.py`。
- Moomoo 歷史 K 線額度是 30 天 100 檔，大量標的要先規劃額度，或改用 yfinance。
- （待你補充：自己的心得）
