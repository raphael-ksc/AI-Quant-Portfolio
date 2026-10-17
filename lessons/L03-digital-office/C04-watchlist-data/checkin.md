---
id: C04
lesson: L03
title: 獲取你的自選股數據
title_en: Watchlist Data Acquisition
category: data-engineering
knowledge: [data-engineering]
tags: [Moomoo, yfinance, 日線, 分鐘線, 財務數據]
symbols: [US.PLTR, US.IREN]
status: done
phase: 1
order: 1
flagship: false
date: 2026-10-17
confidence: 5
source: 3-打造数字化办公室/3-基础设施打造（构建数字化办公室）.pdf p.81
outputs:
  figures: [outputs/figures/daily_close.png, outputs/figures/minute_2026-02-06.png]
  metrics: outputs/metrics.json
---

# C04 獲取你的自選股數據

> ⚠️ 免責聲明：本頁所有策略分析與回測結果僅供教育與研究用途，不構成投資建議或收益保證。

## 題目要求

- 針對自選股獲取：
  - 日線，例如 20240101 至 20251231
  - 分鐘線，例如 20260206 的分鐘 K 線
  - 財務數據（原課程用 tushare、akshare 或 QMT；此處已換成 Moomoo OpenAPI 版本）

## 方法

- **標的**：`US.PLTR`、`US.IREN`（皆在 Nasdaq 掛牌、USD 計價；設定見 `config/symbols.yaml`）。
- **資料層**：新寫的 `quantlib/data/`，Moomoo 與 yfinance 實作同一組介面，輸出統一格式並經 `schema.py` 驗證。
  - 主要資料源：Moomoo OpenAPI（行情權限 LV1）
  - 交叉比對與公開重現：yfinance（`--source yfinance` 任何人都能執行，分鐘線除外）
- **日線**：2024-01-01 至 2025-12-31，前復權（QFQ）。
- **分鐘線**：2026-02-06，只取正常交易時段（美東 09:30–16:00），時間標記為 K 棒結束時間。
- **財報**：最近 8 季的利潤表、資產負債表、現金流量表，轉成長表（一列 = 一個科目在一期的數值）。
- **執行**：`lessons/L03-digital-office/C04-watchlist-data/src/fetch_watchlist.py`；原始數據只存本機 `data/C04/`，不公開。

### 從第一版（`legacy-homework/`）改進的地方

| 問題 | 第一版 | 新版 |
|---|---|---|
| K 線分頁 | 只取第一頁 1,000 筆，超過會**默默截斷** | 依 `page_req_key` 迴圈取完 |
| 財報期末日 | 欄名是 `period_0` 等序號，沒有日期 | 用 `date_time` 換算 UTC+8，修正 Moomoo 早一天的問題 |
| 財報科目比對 | 用科目名稱關鍵字 | 保留 `(報表, field_id)`，`field_id` 只在同一張報表內唯一 |
| 財報分頁 | 未處理 | 依 `next_key` 迴圈取完 |
| yfinance 日線 | `end` 不含當天，少抓最後一天 | 自動 +1 天，start、end 皆包含 |
| 連線 | 每個函式各開關一次 | 單一連線，呼叫間隔 ≥ 1.1 秒，遇頻率限制等 5 秒重試 |

## 結果

| 項目 | PLTR | IREN |
|---|---|---|
| 日線筆數（2024–2025） | 502 | 502 |
| 分鐘線筆數（2026-02-06） | 390（09:31–16:00） | 390（09:31–16:00） |
| 季報期數 | 8（2024/Q3–2026/Q2） | 8（財年 2025/Q1–2026/Q4） |
| 科目數（利潤／資產負債／現金流） | 23 / 36 / 26 | 32 / 52 / 30 |
| 與 yfinance 日線比對 | 502 天全部對上，收盤價差 0% | 502 天全部對上，收盤價差 0% |

- 歷史 K 線額度：已用 2 檔，剩餘 98 檔（每 30 天）。
- yfinance 重現模式：日線同樣 502 筆；季報只有 6 期；2026-02-06 的分鐘線超出 yfinance 7 天範圍，無法取得。
- 兩個資料源收盤價完全一致，是因為這兩檔在 2024–2025 年沒有分割或配息，**不代表兩邊的復權算法相同**；遇到有公司行動的標的需要重新比對。
- IREN 的財年在 6 月結束，所以 2026-06-30 是它的 2026/Q4；跨公司比較一律用期末日對齊，不用財年編號。

## 風險檢查表

- [x] 資料洩漏（Data Leakage）與前視偏差（Look-ahead Bias）：財報只有報告期結束日，沒有公告日；`announce_date` 欄位保留為空，之後做回測必須另外補公告日。
- [x] 倖存者偏差（Survivorship Bias）：本題只抓指定的兩檔，不涉及選股；之後做全市場選股時必須納入已下市股票。
- [ ] 過度擬合（Overfitting）與樣本外測試（Out-of-sample Testing）：本題不涉及策略。
- [ ] 交易成本（Transaction Costs）與滑價（Slippage）：本題不涉及交易。
- [x] 流動性限制（Liquidity Constraints）與市場衝擊（Market Impact）：分鐘線只取正常時段，盤前盤後流動性較差的時段已排除。

## 限制與心得

- 前復權價格會隨未來的公司行動改變；需要「當時看到的價格」時，要改抓不復權（`adjust='none'`）資料。
- Moomoo 有額度限制（每 30 天 100 檔），C24 這類 50 檔的截面研究需要先規劃額度，或日線改用 yfinance。
### 我的心得

1. **時間對齊是財報數據的第一關。** 各公司財年不同（IREN 的財年在 6 月結束），Moomoo 的 `date_time_str` 又會早一天；如果直接用財年編號或原始日期欄位，跨公司比較就會錯位。統一用「期末日」對齊，是之後所有基本面研究的地基。
2. **兩個資料源，各有定位。**
   - **Moomoo**：券商官方 API，連線與數據比較穩定，適合當實盤交易的資料與下單管道。
   - **yfinance**：方便做研究和公開重現，但它是開源套件，不是 Yahoo 官方介面，穩定度沒有保證（介面可能改版、數據可能缺漏），只適合研究用途。
3. **回測不等於實盤。** 數據源、復權方式、公告時點、成交價格，任何一個環節和實盤不一致，回測結果都可能失真。從數據層就要把這些差異記錄清楚，之後的回測結論才有意義。
