# quantlib — 跨課共用程式庫

各題打卡只寫自己的策略邏輯，資料載入、指標、回測等可重用部分放這裡。

- `data/`：資料載入：Moomoo / yfinance loader、統一 schema、幣別標註
- `features/`：技術指標與因子計算
- `backtest/`：Backtrader 包裝、交易成本與滑價模型、績效指標
- `strategies/`：可重用的策略類別
- `ml/`：時間序列交叉驗證（Purged K-Fold、Walk-Forward）、模型訓練
- `risk/`：部位控管、停損、風險指標

> `data/` 已完成（C04，2026-10-10）：Moomoo / yfinance 統一介面、schema 驗證、期末日修正、分頁與頻率限制處理，測試見 `tests/test_data_layer.py`。
> 其他子目錄依審批流程逐步加入；第一版的 `factor_engine.py`、`screener.py` 留在 `lessons/L03-digital-office/legacy-homework/loaders/`，C05 時改寫進 `features/`。
