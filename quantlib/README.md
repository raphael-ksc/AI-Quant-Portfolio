# quantlib — 跨課共用程式庫

各題打卡只寫自己的策略邏輯，資料載入、指標、回測等可重用部分放這裡。

- `data/`：資料載入：Moomoo / yfinance loader、統一 schema、幣別標註
- `features/`：技術指標與因子計算
- `backtest/`：Backtrader 包裝、交易成本與滑價模型、績效指標
- `strategies/`：可重用的策略類別
- `ml/`：時間序列交叉驗證（Purged K-Fold、Walk-Forward）、模型訓練
- `risk/`：部位控管、停損、風險指標

> `data/` 已完成（C04，2026-10-10）：Moomoo / yfinance 統一介面、schema 驗證、期末日修正、分頁與頻率限制處理，測試見 `tests/test_data_layer.py`。
> `db/` 已完成（C06，2026-10-17）：MySQL 連線設定、增量規劃（回看比對前復權基準）、存取層，測試見 `tests/test_db_layer.py`、`tests/test_db_mysql.py`。
> `backtest/`、`strategies/` 已完成（C13，2026-10-17）：Backtrader 包裝（t+1 開盤成交、成交量上限、滑價）、美股成本模型（`config/costs.yaml`）、績效指標、6 個課程策略外掛（放進 `strategies/` 即自動載入），測試見 `tests/test_backtest.py`。
> `fundamentals/`、`data/edgar.py` 已完成（C07，2026-10-17）：多候選科目比對（`config/financial_fields.yaml`）、期末日對齊、近四季合計與比率、SEC EDGAR 申報日 → `available_date`（防前視偏差），測試見 `tests/test_fundamentals.py`。
> 其他子目錄依審批流程逐步加入；第一版的 `factor_engine.py`、`screener.py` 留在 `lessons/L03-digital-office/legacy-homework/loaders/`，C05 時改寫進 `features/`。
