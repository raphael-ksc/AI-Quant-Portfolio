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

-- ===================== C07 財務數據 =====================

-- 原始財報長表：一列 = 一個科目在一期的數值（與 quantlib/data/schema.py 的 FINANCIAL_COLUMNS 一致）
-- field_id 只在同一張報表內唯一，所以主鍵包含 statement
CREATE TABLE IF NOT EXISTS financial_items (
    symbol         VARCHAR(20)   NOT NULL,
    source         VARCHAR(16)   NOT NULL,
    statement      VARCHAR(16)   NOT NULL COMMENT 'income / balance / cashflow',
    field_id       VARCHAR(64)   NOT NULL COMMENT 'Moomoo 為數字代碼；yfinance 為科目英文名',
    name           VARCHAR(128)  NOT NULL,
    period_end     DATE          NOT NULL COMMENT '報告期結束日（Moomoo 已修正早一天的問題）',
    fiscal_period  VARCHAR(16)   NULL     COMMENT '財年期別，例如 2027/Q2',
    freq           CHAR(1)       NOT NULL COMMENT 'Q 季報 / A 年報',
    value          DECIMAL(28,6) NULL,
    currency       CHAR(3)       NOT NULL,
    run_id         BIGINT        NULL,
    updated_at     DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (symbol, source, statement, field_id, period_end, freq),
    KEY idx_financial_items_period (period_end)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='財報原始科目（長表）';

-- 財報重編紀錄：數值被修正時保留舊值，回測才能還原「當時看到的數字」
CREATE TABLE IF NOT EXISTS financial_revisions (
    revision_id    BIGINT        NOT NULL AUTO_INCREMENT,
    symbol         VARCHAR(20)   NOT NULL,
    source         VARCHAR(16)   NOT NULL,
    statement      VARCHAR(16)   NOT NULL,
    field_id       VARCHAR(64)   NOT NULL,
    period_end     DATE          NOT NULL,
    freq           CHAR(1)       NOT NULL,
    old_value      DECIMAL(28,6) NULL,
    new_value      DECIMAL(28,6) NULL,
    detected_at    DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    run_id         BIGINT        NULL,
    PRIMARY KEY (revision_id),
    KEY idx_financial_revisions_key (symbol, statement, field_id, period_end)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='財報重編紀錄';

-- 衍生指標（寬表）：一列 = 一檔一期；比率為小數（0.25 = 25%）
-- available_date：回測時這期財報最早可用的日期（SEC 申報日隔天，或保守推算），防止前視偏差
CREATE TABLE IF NOT EXISTS financial_metrics (
    symbol              VARCHAR(20)   NOT NULL,
    source              VARCHAR(16)   NOT NULL,
    period_end          DATE          NOT NULL,
    freq                CHAR(1)       NOT NULL,
    fiscal_period       VARCHAR(16)   NULL,
    currency            CHAR(3)       NOT NULL,
    filing_date         DATE          NULL     COMMENT 'SEC 10-Q / 10-K 原始申報日',
    filing_form         VARCHAR(10)   NULL,
    available_date      DATE          NOT NULL,
    available_basis     VARCHAR(10)   NOT NULL COMMENT 'edgar / lag_rule',
    revenue             DECIMAL(28,6) NULL,
    gross_profit        DECIMAL(28,6) NULL,
    net_income          DECIMAL(28,6) NULL,
    eps_basic           DECIMAL(18,6) NULL,
    eps_diluted         DECIMAL(18,6) NULL,
    ocf                 DECIMAL(28,6) NULL,
    capex               DECIMAL(28,6) NULL,
    fcf                 DECIMAL(28,6) NULL,
    total_assets        DECIMAL(28,6) NULL,
    current_assets      DECIMAL(28,6) NULL,
    total_liabilities   DECIMAL(28,6) NULL,
    current_liabilities DECIMAL(28,6) NULL,
    total_equity        DECIMAL(28,6) NULL,
    revenue_ttm         DECIMAL(28,6) NULL,
    gross_profit_ttm    DECIMAL(28,6) NULL,
    net_income_ttm      DECIMAL(28,6) NULL,
    ocf_ttm             DECIMAL(28,6) NULL,
    capex_ttm           DECIMAL(28,6) NULL,
    fcf_ttm             DECIMAL(28,6) NULL,
    roe_ttm             DECIMAL(18,8) NULL,
    roa_ttm             DECIMAL(18,8) NULL,
    gross_margin_ttm    DECIMAL(18,8) NULL,
    net_margin_ttm      DECIMAL(18,8) NULL,
    fcf_margin_ttm      DECIMAL(18,8) NULL,
    ocf_to_ni_ttm       DECIMAL(18,8) NULL,
    debt_ratio          DECIMAL(18,8) NULL,
    current_ratio       DECIMAL(18,8) NULL,
    gross_margin_q      DECIMAL(18,8) NULL,
    net_margin_q        DECIMAL(18,8) NULL,
    run_id              BIGINT        NULL,
    updated_at          DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (symbol, source, period_end, freq),
    KEY idx_financial_metrics_available (available_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='衍生財務指標';

-- 相容課程 CASE 程式碼的 trade_stock_financial（第 4 課 wucai_trade.sql）
-- 課程的百分比欄位（ROE、毛利率…）在這裡 × 100；比率用近四季合計口徑；同一期兩個資料源都有時優先 Moomoo
CREATE OR REPLACE VIEW trade_stock_financial AS
SELECT
    f.symbol                    AS stock_code,
    f.period_end                AS report_date,
    f.revenue                   AS revenue,
    f.net_income                AS net_profit,
    f.eps_basic                 AS eps,
    f.roe_ttm * 100             AS roe,
    f.roa_ttm * 100             AS roa,
    f.gross_margin_ttm * 100    AS gross_margin,
    f.net_margin_ttm * 100      AS net_margin,
    f.debt_ratio * 100          AS debt_ratio,
    f.current_ratio             AS current_ratio,
    f.ocf                       AS operating_cashflow,
    f.total_assets              AS total_assets,
    f.total_equity              AS total_equity,
    f.source                    AS data_source,
    f.available_date            AS available_date
FROM financial_metrics f
WHERE f.freq = 'Q'
  AND (f.source = 'moomoo'
       OR NOT EXISTS (SELECT 1 FROM financial_metrics x
                      WHERE x.symbol = f.symbol AND x.period_end = f.period_end
                        AND x.freq = 'Q' AND x.source = 'moomoo'));
