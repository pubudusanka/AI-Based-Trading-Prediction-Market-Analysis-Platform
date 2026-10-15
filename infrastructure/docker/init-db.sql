-- =========================================================
-- AI-Based Trading Platform: PostgreSQL Database Schema
-- Reference: Section 9 (Phase 4 Database Design)
-- All 8 Core Tables Defined
-- =========================================================

-- Enable uuid and pgcrypto extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- 1. Market Symbol Master
CREATE TABLE IF NOT EXISTS market_symbol (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(32) NOT NULL,
    exchange VARCHAR(32) NOT NULL DEFAULT 'BINANCE',
    asset_type VARCHAR(32) NOT NULL DEFAULT 'CRYPTO',
    base_asset VARCHAR(16) NOT NULL,
    quote_asset VARCHAR(16) NOT NULL,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_symbol_exchange UNIQUE (symbol, exchange)
);

-- Seed initial symbol: BTC/USDT
INSERT INTO market_symbol (symbol, exchange, asset_type, base_asset, quote_asset, active)
VALUES ('BTC/USDT', 'BINANCE', 'CRYPTO', 'BTC', 'USDT', TRUE)
ON CONFLICT (symbol, exchange) DO NOTHING;

-- 2. Raw Market Candles (Immutable Raw Store)
CREATE TABLE IF NOT EXISTS market_candle (
    id BIGSERIAL PRIMARY KEY,
    symbol_id INT NOT NULL REFERENCES market_symbol(id) ON DELETE CASCADE,
    timeframe VARCHAR(10) NOT NULL,
    open_time TIMESTAMP WITH TIME ZONE NOT NULL,
    close_time TIMESTAMP WITH TIME ZONE NOT NULL,
    open NUMERIC(20, 8) NOT NULL,
    high NUMERIC(20, 8) NOT NULL,
    low NUMERIC(20, 8) NOT NULL,
    close NUMERIC(20, 8) NOT NULL,
    volume NUMERIC(28, 8) NOT NULL,
    quote_volume NUMERIC(28, 8) NOT NULL,
    trade_count INT NOT NULL DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_candle_symbol_tf_open UNIQUE (symbol_id, timeframe, open_time),
    CONSTRAINT chk_candle_high_low CHECK (high >= low),
    CONSTRAINT chk_candle_high_open CHECK (high >= open),
    CONSTRAINT chk_candle_high_close CHECK (high >= close),
    CONSTRAINT chk_candle_low_open CHECK (low <= open),
    CONSTRAINT chk_candle_low_close CHECK (low <= close),
    CONSTRAINT chk_candle_vol_positive CHECK (volume >= 0)
);

CREATE INDEX IF NOT EXISTS idx_candle_lookup 
ON market_candle (symbol_id, timeframe, open_time DESC);

-- 3. Ingestion Runs Tracker
CREATE TABLE IF NOT EXISTS data_ingestion_run (
    id BIGSERIAL PRIMARY KEY,
    provider VARCHAR(50) NOT NULL,
    symbol VARCHAR(32) NOT NULL,
    timeframe VARCHAR(10) NOT NULL,
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE NOT NULL,
    status VARCHAR(20) NOT NULL, -- PENDING, RUNNING, COMPLETED, FAILED
    records_received INT DEFAULT 0,
    records_inserted INT DEFAULT 0,
    error_message TEXT,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_ingestion_status 
ON data_ingestion_run (status, started_at DESC);

-- 4. Feature Snapshots
CREATE TABLE IF NOT EXISTS feature_snapshot (
    id BIGSERIAL PRIMARY KEY,
    candle_id BIGINT NOT NULL REFERENCES market_candle(id) ON DELETE CASCADE,
    feature_version VARCHAR(50) NOT NULL,
    rsi NUMERIC(10, 4),
    ema_20 NUMERIC(20, 8),
    ema_50 NUMERIC(20, 8),
    ema_200 NUMERIC(20, 8),
    macd NUMERIC(12, 6),
    macd_signal NUMERIC(12, 6),
    atr NUMERIC(12, 6),
    adx NUMERIC(10, 4),
    features JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_feature_candle_version UNIQUE (candle_id, feature_version)
);

CREATE INDEX IF NOT EXISTS idx_feature_snapshot_version 
ON feature_snapshot (feature_version, candle_id);

-- 5. Predictions
CREATE TABLE IF NOT EXISTS prediction (
    id BIGSERIAL PRIMARY KEY,
    symbol VARCHAR(32) NOT NULL,
    timeframe VARCHAR(10) NOT NULL,
    candle_time TIMESTAMP WITH TIME ZONE NOT NULL,
    model_version VARCHAR(50) NOT NULL,
    feature_version VARCHAR(50) NOT NULL,
    probability_up NUMERIC(6, 5) NOT NULL,
    probability_down NUMERIC(6, 5) NOT NULL,
    probability_neutral NUMERIC(6, 5) NOT NULL,
    predicted_class VARCHAR(10) NOT NULL, -- UP, DOWN, NEUTRAL
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_prediction_time 
ON prediction (symbol, timeframe, candle_time DESC);

-- 6. Prediction Outcomes (Evaluation & Calibration)
CREATE TABLE IF NOT EXISTS prediction_outcome (
    id BIGSERIAL PRIMARY KEY,
    prediction_id BIGINT NOT NULL REFERENCES prediction(id) ON DELETE CASCADE,
    future_return NUMERIC(10, 6),
    maximum_favorable_excursion NUMERIC(10, 6),
    maximum_adverse_excursion NUMERIC(10, 6),
    actual_class VARCHAR(10), -- UP, DOWN, NEUTRAL
    target_hit BOOLEAN,
    stop_hit BOOLEAN,
    evaluated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_outcome_prediction 
ON prediction_outcome (prediction_id);

-- 7. Model Version Registry
CREATE TABLE IF NOT EXISTS model_version (
    id SERIAL PRIMARY KEY,
    model_name VARCHAR(100) NOT NULL,
    model_type VARCHAR(50) NOT NULL, -- XGBOOST, RANDOM_FOREST, LOGISTIC_REGRESSION
    version VARCHAR(50) NOT NULL UNIQUE,
    dataset_version VARCHAR(50),
    feature_version VARCHAR(50),
    hyperparameters JSONB,
    training_start TIMESTAMP WITH TIME ZONE,
    training_end TIMESTAMP WITH TIME ZONE,
    validation_start TIMESTAMP WITH TIME ZONE,
    validation_end TIMESTAMP WITH TIME ZONE,
    test_start TIMESTAMP WITH TIME ZONE,
    test_end TIMESTAMP WITH TIME ZONE,
    metrics JSONB,
    artifact_location VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_model_version_lookup 
ON model_version (model_name, version);

-- 8. Backtest Runs Tracker
CREATE TABLE IF NOT EXISTS backtest_run (
    id BIGSERIAL PRIMARY KEY,
    strategy_version VARCHAR(50) NOT NULL,
    model_version VARCHAR(50) NOT NULL,
    symbol VARCHAR(32) NOT NULL,
    timeframe VARCHAR(10) NOT NULL,
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE NOT NULL,
    initial_capital NUMERIC(20, 4) NOT NULL DEFAULT 10000.0000,
    fees NUMERIC(10, 6) NOT NULL DEFAULT 0.001,
    slippage NUMERIC(10, 6) NOT NULL DEFAULT 0.0005,
    total_trades INT NOT NULL DEFAULT 0,
    win_rate NUMERIC(6, 4),
    profit_factor NUMERIC(10, 4),
    max_drawdown NUMERIC(6, 4),
    sharpe_ratio NUMERIC(8, 4),
    total_return NUMERIC(10, 4),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_backtest_lookup 
ON backtest_run (strategy_version, model_version, symbol);
