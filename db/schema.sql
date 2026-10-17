-- quant_portfolio 資料庫結構（C06 起各題共用）
-- 可重複執行：資料表用 IF NOT EXISTS，VIEW 用 CREATE OR REPLACE。
-- 本機 MySQL80：python ...\C06-market-data-collection\src\ingest_daily.py --init-schema
-- Docker：docker compose up 第一次啟動時自動執行（掛載到 /docker-entrypoint-initdb.d/）

-- 標的主檔：由 config/symbols.yaml 同步；is_active / delisted_date 預留給全市場研究，避免倖存者偏差
CREATE TABLE IF NOT EXISTS instruments (
    symbol         VARCHAR(20)  NOT NULL COMMENT '內部代碼，例如 PLTR',
    name_en        VARCHAR(100) NOT NULL,
    name_zh        VARCHAR(100) NOT NULL,
    exchange       VARCHAR(20)  NOT NULL COMMENT '實際掛牌交易所',
    currency       CHAR(3)      NOT NULL,
    timezone       VARCHAR(40)  NOT NULL COMMENT '交易所時區，例如 America/New_York',
    moomoo_code    VARCHAR(30)  NULL,
    yfinance_code  VARCHAR(30)  NULL,
    is_active      TINYINT(1)   NOT NULL DEFAULT 1,
    delisted_date  DATE         NULL,
    updated_at     DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (symbol)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='標的主檔';

-- 每次寫入的紀錄：方便追查哪次執行寫了什麼、是否失敗
CREATE TABLE IF NOT EXISTS ingest_runs (
    run_id        BIGINT       NOT NULL AUTO_INCREMENT,
    job           VARCHAR(40)  NOT NULL COMMENT '例如 market_daily',
    source        VARCHAR(16)  NOT NULL,
    mode          VARCHAR(16)  NOT NULL COMMENT 'full / incremental',
    symbols       VARCHAR(1000) NOT NULL,
    rows_written  INT          NOT NULL DEFAULT 0,
    status        VARCHAR(16)  NOT NULL DEFAULT 'running' COMMENT 'running / success / partial / failed',
    message       TEXT         NULL,
    started_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    finished_at   DATETIME     NULL,
    PRIMARY KEY (run_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='資料寫入紀錄';

-- 日線：前復權（qfq）與不復權（none）並存，Moomoo 與 yfinance 並存可交叉比對
-- 價格用 DECIMAL(18,6)：課程的 DECIMAL(10,2) 只到小數 2 位，前復權後的低價股會失真
CREATE TABLE IF NOT EXISTS market_daily (
    symbol         VARCHAR(20)   NOT NULL,
    trade_date     DATE          NOT NULL COMMENT '交易所當地日期',
    adjust         VARCHAR(8)    NOT NULL COMMENT 'qfq 前復權 / none 不復權',
    source         VARCHAR(16)   NOT NULL COMMENT 'moomoo / yfinance',
    open           DECIMAL(18,6) NOT NULL,
    high           DECIMAL(18,6) NOT NULL,
    low            DECIMAL(18,6) NOT NULL,
    close          DECIMAL(18,6) NOT NULL,
    volume         DECIMAL(20,4) NOT NULL COMMENT '成交量（股）',
    amount         DECIMAL(24,4) NULL     COMMENT '成交額；yfinance 不提供',
    turnover_rate  DECIMAL(12,8) NULL     COMMENT '換手率，比例（0.0115 = 1.15%）；yfinance 不提供',
    currency       CHAR(3)       NOT NULL,
    run_id         BIGINT        NULL     COMMENT '對應 ingest_runs.run_id',
    updated_at     DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (symbol, trade_date, adjust, source),
    KEY idx_market_daily_date (trade_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='日 K 線';

-- 相容課程 CASE 程式碼（第 13、18 課的 data_loader.py 讀 trade_stock_daily）
-- 只取前復權；同一天兩個資料源都有時優先 Moomoo；換手率換算成課程使用的百分比
CREATE OR REPLACE VIEW trade_stock_daily AS
SELECT
    m.symbol             AS stock_code,
    m.trade_date         AS trade_date,
    m.open               AS open_price,
    m.high               AS high_price,
    m.low                AS low_price,
    m.close              AS close_price,
    m.volume             AS volume,
    m.amount             AS amount,
    m.turnover_rate * 100 AS turnover_rate,
    m.source             AS source
FROM market_daily m
WHERE m.adjust = 'qfq'
  AND (m.source = 'moomoo'
       OR NOT EXISTS (SELECT 1 FROM market_daily x
                      WHERE x.symbol = m.symbol AND x.trade_date = m.trade_date
                        AND x.adjust = 'qfq' AND x.source = 'moomoo'));
