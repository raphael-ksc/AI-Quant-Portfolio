# AI 量化交易作品集（AI Quantitative Trading Portfolio）

系統化記錄「AI 量化交易」課程的 36 項實作打卡：從多資料源數據工程、基本面與技術面研究、回測，到系統化策略、機器學習因子與 AI Agent 自動化。

🌐 **網站**：https://raphael-ksc.github.io/AI-Quant-Portfolio/ （繁體中文／English，三種主題）

> ⚠️ **免責聲明**：本 repo 所有策略分析、回測結果與訊號探討僅供教育與研究用途，不構成投資建議或收益保證。

## 技術環境

- 美股／港股行情與財務數據：**Moomoo OpenAPI**（原課程使用 QMT，已全面改寫為 Moomoo 版本）
- Moomoo 不支援的市場（如澳洲 ASX）：`yfinance`
- 回測：Backtrader；技術指標：TA-Lib；機器學習：XGBoost / LightGBM

## 能力地圖

| 知識分類 | 內容 | 對應打卡 |
|---|---|---|
| [數據工程](knowledge/data-engineering/) | 多資料源採集、資料庫設計 | C04, C06–C12, C28 |
| [基本面研究](knowledge/fundamentals/) | 財務科目、多因子打分、選股池 | C02, C05, C20 |
| [技術分析](knowledge/technical-analysis/) | 指標儀表盤、TA-Lib 策略優化 | C03, C14 |
| [回測](knowledge/backtesting/) | Backtrader、交易成本與滑價 | C01, C13 |
| [系統化策略](knowledge/strategies/) | 海龜、纏論、網格、策略融合 | C17, C18, C19, C21 |
| [機器學習因子](knowledge/machine-learning/) | RankIC、Purged K-Fold、截面預測、SVD、強化學習 | C22–C25, C27, C33–C36 |
| [AI Agent](knowledge/ai-agents/) | LLM Agent、Skill 工程化、RAG、輿情事件 | C15, C16, C28–C31 |
| [風險與回測偏差](knowledge/risk-management/) | 資料洩漏、倖存者偏差、過度擬合、績效報告、模擬盤交易 | C26, C32，並橫跨所有回測題 |

完整任務表見 [打卡清單.md](打卡清單.md)。

## Repo 結構

```
lessons/      按課程：Lxx-<課程>/Cxx-<打卡題>/（checkin.md、src/、notebooks/、outputs/）
knowledge/    按知識點分類的概念筆記
quantlib/     跨課共用程式庫（資料、特徵、回測、策略、ML、風控）
scripts/      建置腳本（掃描 checkin.md 產生展示頁資料）
site/         展示網站（Next.js 靜態匯出 → GitHub Pages）
tests/        單元測試
```

每題打卡的 `checkin.md` 以 front-matter 記錄編號、課程、分類、標籤、狀態與完成日期，展示網站依此自動分類呈現。

## 每題成果的固定結構

問題定義 → 方法 → 結果（圖表與指標）→ 風險檢查表（資料洩漏、倖存者偏差、過度擬合、交易成本、流動性）→ 限制與心得

## 本機開發

```
# 1. 驗證打卡資料並產生網站資料
.venv\Scripts\python.exe scripts\build_manifest.py
# 2. 啟動網站（http://localhost:3000/AI-Quant-Portfolio/）
cd site && npm install && npm run dev
# 3. 測試
.venv\Scripts\python.exe -m pytest tests
```

### 資料庫（C06 起各題共用）

```
# 複製 .env.example 為 .env 並填入 MySQL 帳號密碼（.env 不會進 repo）
# A. 本機 MySQL（MYSQL_PORT=3306）：第一次執行加 --init-schema 建立資料庫與資料表
.venv\Scripts\python.exe lessons\L04-data-pipeline\C06-market-data-collection\src\ingest_daily.py --init-schema
# B. Docker（MYSQL_PORT=3307）：不需要 Moomoo 帳號，任何人都能重現
docker compose up -d
.venv\Scripts\python.exe lessons\L04-data-pipeline\C06-market-data-collection\src\ingest_daily.py --source yfinance
```
