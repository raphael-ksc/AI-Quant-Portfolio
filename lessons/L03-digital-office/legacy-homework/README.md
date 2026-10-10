# 量化自選股數據終端（AI量化交易第一期 · 第三節課作業）

> 📦 **封存版本（v1，2026-09）**：這是 C04／C05 的第一版作業，保留原樣以呈現演進過程。
> 新版資料層已改寫為 `quantlib/data/`（修正 K 線分頁截斷、財報期末日偏移、yfinance 結束日少一天等問題），
> 請以新版為準。本資料夾的 BHP.AX 範例不在目前「先只做美股」的範圍內。


以 Moomoo OpenAPI（美股：PLTR、IREN）與 yfinance（澳股：BHP.AX）
建立的雙資料源股票數據抓取專案，包含 Jupyter Notebook 分析版本，
以及一個本機網頁儀表板（按鈕觸發即時抓取 K 線與財務數據）。

⚠️ 免責聲明：本專案之數據與呈現僅供教育與研究用途，不構成任何投資建議。

## 專案結構

```
homework_multi_source/
├── loaders/
│   ├── moomoo_loader.py     PLTR / IREN → Moomoo OpenAPI
│   ├── yfinance_loader.py   BHP.AX → yfinance
│   └── unify_schema.py      統一格式、幣別標註
├── webapp/
│   ├── app.py                Flask 後端
│   ├── templates/            index.html（主控台）、notes.html（學習筆記）
│   └── static/                style.css、main.js
├── notebook/
│   └── analysis.ipynb        互動式分析版本
├── requirements.txt
└── .gitignore
```

## 前置需求

- Python 3.10+
- **PLTR / IREN 兩檔標的**需要：
  1. 已開通 Moomoo（新加坡）帳戶並具備美股行情權限
  2. 已下載安裝並登入 **moomoo OpenD**（`moomoo.com/download/OpenAPI`）
  3. OpenD 保持在背景執行且顯示已連線狀態
- **BHP 這一檔**不需要任何帳戶，yfinance 直接可用

## 安裝

```bash
git clone <your-repo-url>
cd homework_multi_source
pip install -r requirements.txt
```

## 驗證 Moomoo 安裝

```bash
python -c "import moomoo as ft; print('OK', ft.__version__)"
```

## 啟動網頁儀表板

```bash
cd webapp
python app.py
```

啟動後在瀏覽器打開：http://127.0.0.1:5000

- **主控台**（`/`）：選標的（PLTR / IREN / BHP）與週期，按「抓取數據」顯示 K 線圖（國際盤色系：漲=綠、跌=紅）與近 8 季財務數據
- **多因子選股**（`/screener`）：輸入板塊關鍵字（如 `semiconductor`），設定 ROE 門檻，自動抓該板塊市值前 30 大成分股，計算 ROE(TTM) 與三個 Capex 相關比率的趨勢，篩選並排序
- **學習筆記**（`/notes`）：這次課程的雙語學習記錄
- **架構說明**（`/about`）：面向求職展示的專案說明頁（問題背景、架構圖、設計決策、已知限制）
- 右上角可切換語言（中文 / English）

## 使用 Notebook

```bash
jupyter notebook notebook/analysis.ipynb
```

Notebook 直接 import `loaders/` 底下的函式，可自由調整日期區間、加上
自己的因子計算邏輯，作為「多因子選股」作業的延伸。

## 已知限制（Known Limitations）

- Moomoo OpenAPI 目前不支援新加坡、日本、澳洲市場的行情數據，
  故本專案不使用 Moomoo 抓取 BHP，改用 yfinance 的 `BHP.AX`。
- yfinance 分鐘線資料有官方時間範圍限制（1 分鐘僅近 7 天、
  其他分鐘線僅近 60 天），超出範圍會回傳空結果。
- Moomoo 歷史 K 線額度每 30 天有上限，大量抓取前建議先呼叫
  `moomoo_loader.check_quota()` 確認。
- `get_financials_statements()` 的實際回傳欄位名稱請以執行時
  `print(df.columns)` 為準，官方文件版本更新可能造成落差。

## 安全提醒

`.gitignore` 已排除 OpenD 設定檔與任何 `.env`／密碼類檔案，
**請勿**將您的 Moomoo 帳號密碼、OpenD 設定檔提交到 GitHub。
Clone 這個專案的其他人，需要自行申請 Moomoo 帳號並啟動自己的 OpenD
才能使用 PLTR / IREN 功能；BHP（yfinance）部分則任何人都能直接執行。
