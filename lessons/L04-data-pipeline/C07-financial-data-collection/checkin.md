---
id: C07
lesson: L04
title: 財務數據採集
title_en: Financial Data Collection
category: data-engineering
knowledge: [data-engineering, fundamentals]
tags: [Moomoo, yfinance, SEC EDGAR, MySQL, 財報, 前視偏差, 盈餘品質]
symbols: [US.PLTR, US.IREN, US.NVDA]
status: wip
phase: 1
order: 4
flagship: false
date:
confidence:
source: 4-数据获取与清洗/4-数据获取与清洗.pdf p.54
outputs:
  figures: [outputs/figures/c07_earnings_quality.png]
  metrics: outputs/metrics.json
---

# C07 財務數據採集

> ⚠️ 免責聲明：本頁所有策略分析與回測結果僅供教育與研究用途，不構成投資建議或收益保證。

## 題目要求

- 使用 Akshare、tushare 或 QMT 進行財務數據採集
- 資料表：`trade_stock_financial`（季度財務）
- **原課程為 QMT／Akshare，此處已換成 Moomoo 版本**：`get_financials_statements`（透過 C04 的 `quantlib/data`），yfinance 供公開重現。

## 方法

- **標的**：`US.PLTR`、`US.IREN`、`US.NVDA`，Moomoo 最近 12 季季報。
- **流程**：

```
quantlib.data.get_financials（期末日 UTC+8 修正、分頁、頻率限制）→ schema 驗證
  → financial_items（原始科目長表；數值改變時舊值寫入 financial_revisions）
  → config/financial_fields.yaml 多候選科目比對（依財年期別對齊期末日）
  → 單季值 → 近四季合計 → 比率
  → SEC EDGAR 申報日 → available_date
  → financial_metrics → VIEW trade_stock_financial（相容課程）
```

- **多候選科目**（課程 p.46 的 `get_field`）：每個指標依優先順序列出候選的 `(報表, field_id)`。全部找不到就留空並寫進報告，不推算、不猜。
- **近四季合計（TTM）**：連續 4 季都有值才計算，缺一季就留空。ROE、毛利率等比率都用近四季合計。股東權益為負時 ROE 留空；淨利為負時盈餘品質比值留空。
- **可交易日 `available_date`**：財報只有期末日，沒有公告日。
  - 優先用 SEC EDGAR 的 10-Q／10-K **原始申報日的隔天**。
  - 查不到時用保守推算：季報為期末日 + 46 天，財年第 4 季為期末日 + 76 天。
- **排程**：每週六台北時間 07:00 自動重抓（`scripts/run_weekly_financials.ps1`），財報被重編時會記錄下來。
- **執行**：`lessons/L04-data-pipeline/C07-financial-data-collection/src/ingest_financials.py`；共用程式在 `quantlib/fundamentals/`、`quantlib/data/edgar.py`。

### 和課程版本不同的地方

| 問題 | 課程版本 | 本人版本 |
|---|---|---|
| 公告時點 | 只有報告期 `report_date` | 另存 `available_date`（SEC 申報日隔天）。PLTR 2026 Q2 期末日是 06-30，08-04 才申報；直接用期末日回測會提前 5 週知道財報 |
| 財報重編 | `ON DUPLICATE KEY UPDATE` 直接覆寫 | 覆寫前把舊值寫入 `financial_revisions`，回測可以還原「當時看到的數字」 |
| 比率口徑 | 單期 | 近四季合計（季報的流量科目是單季值，直接除會失真）；單季毛利率、淨利率另外保留 |
| 科目比對 | 欄位名稱候選清單 | `(報表, field_id)` 候選清單：`field_id` 只在同一張報表內唯一（例：8015 在利潤表是 Other Taxes、在現金流量表是 Operating Cash Flow） |
| 期末日不一致 | 未處理 | 同一財年期別在不同報表的期末日不同時，取多數報表的日期並記錄 |
| 百分比 | 存成百分比 | 存成小數；課程相容 VIEW 再 × 100 |

## 結果

### 資料完整度

| 標的 | 季數 | 期間 | 科目筆數 | EDGAR 對上 | 備註 |
|---|---|---|---|---|---|
| PLTR | 12 | 2023-09-30 ～ 2026-06-30 | 986 | 12 / 12 | 全部科目齊全 |
| IREN | 13 | 2023-06-30 ～ 2026-06-30 | 1,124 | 5 / 13 | FY2026 起才申報 10-Q／10-K；之前是外國發行人（20-F／6-K），改用保守推算 |
| NVDA | 12 | 2023-10-29 ～ 2026-07-26 | 1,165 | 12 / 12 | FY2025 Q1 期末日校正（見下方） |

- 重複執行兩次，重編筆數都是 0，表示寫入流程具冪等性（重複執行不會改變結果）。
- **資料源問題，全部有記錄，沒有隱藏：**
  - **IREN 早期缺科目**：2023-09 ～ 2024-06 共 4 季沒有 `8001` 總營收，改用第二候選 `8002` Total Operating Revenue。這 4 季加上 2023-06 共 5 季沒有營運現金流科目。可以用現金恆等式推算，但推算結果和 Moomoo 的自由現金流對不上，差額剛好是匯率影響，所以留空不推算。
  - **NVDA 期末日不一致**：FY2025 Q1 的利潤表期末日是 2024-04-27，資產負債表和現金流量表是 2024-04-28（實際季末），已統一為 04-28。
  - **兩個資料源不一致**：IREN FY2025 Q4 的自由現金流，Moomoo 是 −2.55 億美元，yfinance 是 +0.49 億美元（yfinance 該季缺營運現金流）。

### 最新一期（近四季合計）

| 標的 | 期末日 | 可交易日 | 營收 | 淨利 | 營運現金流 | ROE | 毛利率 | 營運現金流 ÷ 淨利 | 負債比 | 流動比率 |
|---|---|---|---|---|---|---|---|---|---|---|
| PLTR | 2026-06-30 | 2026-08-05 | 61.6 億 | 30.2 億 | 34.0 億 | 30.5% | 84.8% | 1.13 | 15.4% | 7.23 |
| IREN | 2026-06-30 | 2026-08-28 | 7.1 億 | −7.0 億 | 21.0 億 | −16.8% | 62.3% | —（淨利為負） | 73.5% | 3.55 |
| NVDA | 2026-07-26 | 2026-08-27 | 3,029.7 億 | 1,928.8 億 | 1,343.6 億 | 84.2% | 74.7% | 0.70 | 28.5% | 4.59 |

金額單位為美元。

![盈餘品質](outputs/figures/c07_earnings_quality.png)

### 盈餘品質（課程 p.45：利潤有沒有變成現金）

- **PLTR**：營運現金流一直高於淨利，盈餘品質好。比值從 2025 年中的 2.3 倍降到 1.13，是因為淨利成長得更快。【推論】股票薪酬屬於非現金費用，會讓營運現金流高於淨利，PLTR 的股票薪酬占比偏高。
- **NVDA**：過去兩年淨利大多高於營運現金流，2026 年差距擴大，最新比值 0.70。依課程 p.45 的標準，這是需要追蹤的訊號。【推論】可能是營收快速成長時，應收帳款與存貨占用了現金；下一步可以用資產負債表的應收、存貨科目驗證。
- **IREN**：近四季淨利轉負，但營運現金流在最新一季跳升到 18.1 億美元（Moomoo 與 yfinance 數字一致），同一季資本支出 19.8 億美元。【推論】可能與客戶預付款有關，需要查 10-K 才能確認。

## 風險檢查表

- [x] 資料洩漏（Data Leakage）與前視偏差（Look-ahead Bias）：每期都有 `available_date`，回測時只能用 `available_date ≤ 當天` 的財報；重編前的舊值另外保存。
- [x] 倖存者偏差（Survivorship Bias）：本題只有 3 檔自選股；全市場研究要沿用 `instruments` 的下市欄位。
- [ ] 過度擬合（Overfitting）與樣本外測試（Out-of-sample Testing）：本題不涉及策略。
- [ ] 交易成本（Transaction Costs）與滑價（Slippage）：本題不涉及交易。
- [ ] 流動性限制（Liquidity Constraints）與市場衝擊（Market Impact）：本題不涉及交易。

## 限制與心得

- 可交易日用的是 SEC 申報日，比財報發布日（earnings release）晚幾天到幾週，屬於保守做法。如果策略要捕捉財報發布當天的反應，需要另外取得發布日。
- IREN 在 FY2026 以前是外國發行人（以 20-F／6-K 申報），Moomoo 早期季報的口徑可能和後來的 10-Q 不同，使用時要謹慎。
- 只抓了最近 12 季，近四季合計最早只到 2024 年。更長的歷史要改抓年報，或用 SEC 的 XBRL 財報資料。
- （待你補充：自己的心得）
