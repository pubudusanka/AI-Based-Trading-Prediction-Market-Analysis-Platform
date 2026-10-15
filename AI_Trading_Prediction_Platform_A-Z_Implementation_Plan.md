# AI-Based Trading Prediction & Market Analysis Platform

## A-Z Step-by-Step Implementation Plan

**Document Version:** 1.0\
**Project Status:** Planning\
**Primary Goal:** Build a research-oriented, production-style platform
that collects market data, generates technical/market features, trains
machine-learning models, produces probabilistic trading signals,
evaluates them through rigorous backtesting, and displays real-time
analysis.

------------------------------------------------------------------------

# 1. Project Vision

## 1.1 Project Objective

Build an AI-assisted trading analysis platform that can:

1.  Collect historical and real-time market data from
    licensed/authorized market-data providers.
2.  Store raw OHLCV/candle data without modification.
3.  Calculate technical indicators and market-structure features.
4.  Detect candlestick and chart patterns.
5.  Calculate Fibonacci and support/resistance-related features.
6.  Generate machine-learning labels from future market outcomes.
7.  Build clean, leakage-free training datasets.
8.  Train and compare multiple ML models.
9.  Produce probabilistic predictions rather than claiming certainty.
10. Generate BUY / SELL / HOLD or UP / DOWN / NEUTRAL signals based on
    configurable rules.
11. Backtest strategies using historical data.
12. Perform walk-forward/out-of-sample evaluation.
13. Include realistic fees, spread, slippage, and execution assumptions.
14. Provide a real-time dashboard with charts, indicators, predictions,
    signals, and performance.
15. Maintain model versions and prediction history.
16. Support paper trading before any consideration of live trading.
17. Provide a foundation for future deep-learning, chart-image,
    sentiment, and multi-asset research.

## 1.2 Core Principle

The project must **not** claim to predict the market with certainty.

The model should answer a measurable question such as:

> Given the market information available at time T, what is the
> probability that a predefined price target will be reached before a
> predefined stop threshold within the next N candles?

Example:

-   Target: +1%
-   Stop: -0.5%
-   Horizon: next 20 candles

Possible labels:

-   `UP`
-   `DOWN`
-   `NEUTRAL`

## 1.3 Project Philosophy

Follow these principles throughout development:

-   Data first.
-   Reproducibility first.
-   No data leakage.
-   No look-ahead bias.
-   Backtesting before paper/live trading.
-   Simple models before deep learning.
-   One asset/timeframe before multi-asset expansion.
-   Raw data must never be overwritten.
-   Every experiment must be reproducible.
-   Every model must have a version.
-   Every prediction should be traceable to the model and feature
    version that generated it.
-   Never present backtest performance as guaranteed future performance.

------------------------------------------------------------------------

# 2. Recommended Initial Scope

To prevent scope explosion, Version 1 should use:

### Asset

`BTC/USDT`

### Market

Crypto spot market initially.

### Primary timeframe

`15-minute`

### Historical data

Start with approximately 1--2 years, depending on data availability and
provider limits.

### Primary model

`XGBoost` classification model.

### Baseline models

-   Logistic Regression
-   Random Forest
-   XGBoost

### Backend

-   Java 21+
-   Spring Boot
-   Spring Data JPA
-   REST APIs
-   WebSocket where required

### ML/Data Science

-   Python
-   Pandas
-   NumPy
-   scikit-learn
-   XGBoost
-   PyTorch later

### Database

-   PostgreSQL

### Cache

-   Redis

### Frontend

-   Next.js / React
-   TypeScript

### Infrastructure

-   Docker
-   Docker Compose initially
-   CI/CD later

### Initial architecture

Use a modular architecture first. Do not create unnecessary
microservices on day one.

------------------------------------------------------------------------

# 3. High-Level System Architecture

``` text
                    MARKET DATA PROVIDER
                           |
                 REST API / WebSocket
                           |
                           v
                 +--------------------+
                 | Data Ingestion     |
                 | Spring Boot        |
                 +---------+----------+
                           |
                           v
                 +--------------------+
                 | Raw Market Data    |
                 | PostgreSQL         |
                 +---------+----------+
                           |
                           v
                 +--------------------+
                 | Feature Pipeline   |
                 | Python             |
                 +---------+----------+
                           |
             +-------------+-------------+
             |                           |
             v                           v
      Feature Generation          Label Generation
             |                           |
             +-------------+-------------+
                           |
                           v
                 +--------------------+
                 | Training Dataset   |
                 +---------+----------+
                           |
                           v
                 +--------------------+
                 | ML Training        |
                 | Logistic/RF/XGB    |
                 +---------+----------+
                           |
                           v
                 +--------------------+
                 | Model Registry     |
                 +---------+----------+
                           |
                           v
                 +--------------------+
                 | Prediction Service |
                 | Python             |
                 +---------+----------+
                           |
                           v
                 +--------------------+
                 | Signal Engine      |
                 | Spring Boot        |
                 +---------+----------+
                           |
              +------------+------------+
              |                         |
              v                         v
       Backtesting Engine          Real-time Engine
              |                         |
              +------------+------------+
                           |
                           v
                 +--------------------+
                 | Next.js Dashboard  |
                 +--------------------+
```

------------------------------------------------------------------------

# 4. Critical Data Rules

These rules are mandatory.

## 4.1 Raw data immutability

Raw OHLCV data must be stored exactly as received after basic schema
validation.

Do not overwrite raw historical records with calculated values.

## 4.2 No future information in features

For prediction at time `T`, features may only use information available
at or before `T`.

Allowed:

``` text
T-20
T-19
...
T-1
T
```

Not allowed:

``` text
T+1
T+2
T+10
```

Future candles may only be used to create the training label.

## 4.3 Chronological splitting

Do not randomly split time-series data.

Preferred:

``` text
TRAIN       VALIDATION       TEST
|-----------|----------------|
Past        Later            Future
```

Use walk-forward validation for serious evaluation.

## 4.4 Reproducibility

Every training run must record:

-   dataset version
-   feature version
-   label configuration
-   model type
-   hyperparameters
-   training period
-   validation period
-   test period
-   random seed
-   software version
-   metrics

------------------------------------------------------------------------

# 5. Phase 0 --- Project Definition

## Tasks

-   [ ] Define project name.
-   [ ] Define project objective.
-   [ ] Define initial asset.
-   [ ] Define initial timeframe.
-   [ ] Define prediction horizon.
-   [ ] Define target/stop methodology.
-   [ ] Define initial ML target.
-   [ ] Define initial technical features.
-   [ ] Define non-goals for Version 1.
-   [ ] Define success criteria.

## Deliverable

`PROJECT_SCOPE.md`

## Done Criteria

The team/AI agent can answer:

-   What are we predicting?
-   From which data?
-   At what timeframe?
-   How is the target generated?
-   How will success be measured?
-   What is explicitly out of scope?

------------------------------------------------------------------------

# 6. Phase 1 --- Repository and Development Environment

## Repository structure

Recommended:

``` text
ai-trading-platform/
├── backend/
├── ml/
├── frontend/
├── data-pipeline/
├── infrastructure/
├── docs/
├── scripts/
├── tests/
├── .github/
├── docker-compose.yml
├── README.md
└── .gitignore
```

## Backend

``` text
backend/
└── src/
    ├── main/
    └── test/
```

## ML

``` text
ml/
├── notebooks/
├── src/
│   ├── ingestion/
│   ├── preprocessing/
│   ├── features/
│   ├── labels/
│   ├── training/
│   ├── evaluation/
│   ├── inference/
│   └── backtesting/
├── models/
├── datasets/
└── tests/
```

## Frontend

``` text
frontend/
├── app/
├── components/
├── features/
├── services/
├── hooks/
├── types/
└── tests/
```

## Tasks

-   [ ] Create Git repository.
-   [ ] Create branch strategy.
-   [ ] Add README.
-   [ ] Add `.gitignore`.
-   [ ] Add environment configuration.
-   [ ] Configure Java.
-   [ ] Configure Python virtual environment.
-   [ ] Configure Node/Next.js.
-   [ ] Configure PostgreSQL.
-   [ ] Configure Redis.
-   [ ] Create Docker Compose.
-   [ ] Configure formatting/linting.
-   [ ] Configure unit-test frameworks.
-   [ ] Configure CI skeleton.

## Done Criteria

A new developer can clone the repository and start the project using
documented commands.

------------------------------------------------------------------------

# 7. Phase 2 --- Market Data Provider Research and Selection

## Goal

Select an authorized market-data source.

Potential categories:

-   Crypto exchange APIs
-   Stock market-data APIs
-   Forex data providers
-   Licensed aggregated market-data providers

For the initial implementation, use one provider only.

## Selection criteria

Evaluate:

-   Historical data availability
-   Real-time data
-   WebSocket support
-   OHLCV/Kline support
-   Rate limits
-   Data licensing
-   Geographic availability
-   Cost
-   Reliability
-   Symbol coverage
-   Timeframe coverage

## Important

Do not scrape websites or chart pages.

Do not assume that because data is visible on a website it is licensed
for automated collection or redistribution.

Keep the provider implementation behind an interface so it can later be
replaced.

Example:

``` java
public interface MarketDataProvider {
    List<Candle> getHistoricalCandles(
        String symbol,
        String timeframe,
        Instant start,
        Instant end
    );
}
```

## Deliverable

`DATA_PROVIDER_DECISION.md`

------------------------------------------------------------------------

# 8. Phase 3 --- Raw Market Data Ingestion

## Goal

Collect historical OHLCV data.

Initial data:

``` text
BTCUSDT
15m
```

## Candle model

Required fields:

``` text
symbol
exchange
timeframe
openTime
closeTime
open
high
low
close
volume
quoteVolume
tradeCount
```

Use provider-specific fields only where useful.

## Tasks

-   [ ] Implement historical API client.
-   [ ] Implement pagination.
-   [ ] Handle provider rate limits.
-   [ ] Handle retries.
-   [ ] Handle duplicate candles.
-   [ ] Validate OHLC relationships.
-   [ ] Validate timestamps.
-   [ ] Store raw candles.
-   [ ] Add unique constraint.
-   [ ] Add ingestion logs.
-   [ ] Add provider metadata.
-   [ ] Add data-quality checks.

## Data validation

Check:

``` text
high >= max(open, close)
low <= min(open, close)
volume >= 0
timestamp is valid
no duplicate candle
```

## Done Criteria

The system can automatically download historical BTCUSDT 15-minute
candles and persist them without duplication.

------------------------------------------------------------------------

# 9. Phase 4 --- Database Design

## Main tables

### `market_symbol`

``` text
id
symbol
exchange
asset_type
base_asset
quote_asset
active
created_at
```

### `market_candle`

``` text
id
symbol_id
timeframe
open_time
close_time
open
high
low
close
volume
quote_volume
trade_count
created_at
```

### `data_ingestion_run`

``` text
id
provider
symbol
timeframe
start_time
end_time
status
records_received
records_inserted
error_message
started_at
completed_at
```

### `feature_snapshot`

``` text
id
candle_id
feature_version
rsi
ema_20
ema_50
ema_200
macd
macd_signal
atr
adx
...
```

### `prediction`

``` text
id
symbol
timeframe
candle_time
model_version
feature_version
probability_up
probability_down
probability_neutral
predicted_class
created_at
```

### `prediction_outcome`

``` text
id
prediction_id
future_return
maximum_favorable_excursion
maximum_adverse_excursion
actual_class
target_hit
stop_hit
evaluated_at
```

### `model_version`

``` text
id
model_name
model_type
version
dataset_version
feature_version
hyperparameters
training_start
training_end
validation_start
validation_end
test_start
test_end
metrics
artifact_location
created_at
```

### `backtest_run`

``` text
id
strategy_version
model_version
symbol
timeframe
start_time
end_time
initial_capital
fees
slippage
total_trades
win_rate
profit_factor
max_drawdown
sharpe_ratio
total_return
created_at
```

------------------------------------------------------------------------

# 10. Phase 5 --- Historical Data Quality Pipeline

Before ML, verify the dataset.

## Checks

-   [ ] Missing candles.
-   [ ] Duplicate candles.
-   [ ] Invalid OHLC.
-   [ ] Zero/negative prices.
-   [ ] Abnormal volume.
-   [ ] Timestamp gaps.
-   [ ] Wrong timezone handling.
-   [ ] Provider inconsistencies.
-   [ ] Duplicate imports.
-   [ ] Incorrect symbol mapping.

## Output

Generate a data-quality report:

``` text
Total candles:
Missing candles:
Duplicate candles:
Invalid candles:
Date range:
Coverage:
```

## Done Criteria

No known unresolved data-quality issue remains in the initial dataset.

------------------------------------------------------------------------

# 11. Phase 6 --- Feature Engineering Framework

Create a versioned feature pipeline.

Each feature must document:

-   name
-   formula/logic
-   required historical window
-   input columns
-   output type
-   missing-value behavior
-   leakage risk

## Feature groups

### A. Price features

``` text
close
open
high
low
volume
returns
log_returns
percentage_change
```

### B. Candle features

``` text
body_size
body_percentage
upper_wick
lower_wick
range
body_to_range_ratio
bullish/bearish flag
```

### C. Moving averages

``` text
SMA_20
SMA_50
SMA_200
EMA_9
EMA_21
EMA_50
EMA_200
```

### D. Momentum

``` text
RSI
MACD
MACD_signal
MACD_histogram
Stochastic
ROC
```

### E. Volatility

``` text
ATR
Bollinger_width
rolling_std
volatility
```

### F. Trend

``` text
ADX
EMA slopes
price_vs_EMA
moving_average_cross
```

### G. Volume

``` text
volume_ma
volume_ratio
volume_change
OBV
```

------------------------------------------------------------------------

# 12. Phase 7 --- Candlestick Pattern Engine

Implement deterministic pattern detection first.

Initial patterns:

-   Doji
-   Hammer
-   Inverted Hammer
-   Shooting Star
-   Hanging Man
-   Bullish Engulfing
-   Bearish Engulfing
-   Morning Star
-   Evening Star
-   Harami
-   Inside Bar

Represent patterns as features.

Example:

``` text
hammer = 1
bullish_engulfing = 0
doji = 0
```

Do not assume a pattern is profitable simply because technical-analysis
literature describes it as bullish/bearish.

The model/backtest must test its historical usefulness.

## Done Criteria

Every pattern detector has unit tests with positive and negative
examples.

------------------------------------------------------------------------

# 13. Phase 8 --- Market Structure Engine

Detect:

-   Swing highs
-   Swing lows
-   Higher high
-   Higher low
-   Lower high
-   Lower low
-   Trend direction
-   Break of structure
-   Support
-   Resistance
-   Breakout
-   Retest

Avoid future leakage.

Swing detection must define exactly when a swing becomes known in real
time.

For example, a centered rolling window can accidentally use future
candles. Such logic must be designed carefully.

------------------------------------------------------------------------

# 14. Phase 9 --- Fibonacci Feature Engine

Calculate Fibonacci levels from clearly defined swing points.

Initial levels:

``` text
0.236
0.382
0.500
0.618
0.786
1.000
```

Features:

``` text
distance_to_236
distance_to_382
distance_to_500
distance_to_618
distance_to_786
near_618
near_382
```

Document the swing-selection algorithm.

Do not manually copy Fibonacci levels from TradingView.

------------------------------------------------------------------------

# 15. Phase 10 --- Feature Dataset Creation

Combine:

``` text
Raw candles
+
Technical indicators
+
Candlestick patterns
+
Market structure
+
Fibonacci
+
Volume
```

into a feature table.

Example:

``` text
timestamp
close
return_1
return_5
rsi
ema_20
ema_50
ema_200
macd
macd_signal
atr
adx
volume_ratio
hammer
bullish_engulfing
swing_trend
support_distance
resistance_distance
fib_382_distance
fib_618_distance
...
```

## Feature versioning

Example:

``` text
feature_version = v1.0
```

If a formula changes:

``` text
v1.1
```

Never silently change an existing feature definition.

------------------------------------------------------------------------

# 16. Phase 11 --- Target / Label Generation

This is a critical phase.

Define the prediction problem mathematically.

Initial example:

``` text
Prediction horizon = 20 candles

Take Profit = +1.0%
Stop Loss = -0.5%
```

For every candle `T`:

1.  Read price at `T`.
2.  Examine future candles from `T+1` to `T+20`.
3.  Determine whether TP or SL is reached first.
4.  If TP first → `UP`.
5.  If SL first → `DOWN`.
6.  If neither → `NEUTRAL`.

## Important edge case

If both TP and SL appear to be touched within the same candle, OHLC
alone may not tell you which occurred first.

Define a conservative rule or use higher-resolution data where
appropriate.

Document the rule.

## Additional labels

Store:

``` text
future_return_5
future_return_10
future_return_20
max_future_return
min_future_return
time_to_target
time_to_stop
```

This allows future experiments.

------------------------------------------------------------------------

# 17. Phase 12 --- Dataset Versioning

Create:

``` text
dataset_version
```

Example:

``` text
btc_15m_v1
```

Store metadata:

``` text
symbol
timeframe
data provider
date range
feature version
label version
row count
created_at
```

Do not train models from an untracked CSV.

------------------------------------------------------------------------

# 18. Phase 13 --- Exploratory Data Analysis

Before training:

-   Class distribution.
-   Feature distributions.
-   Missing values.
-   Outliers.
-   Correlations.
-   Feature importance candidates.
-   Target balance.
-   Performance by market regime.
-   Performance by time period.

Example:

``` text
UP       38%
DOWN     34%
NEUTRAL  28%
```

If highly imbalanced:

``` text
UP       80%
DOWN     10%
NEUTRAL  10%
```

do not celebrate high accuracy. Investigate the imbalance.

------------------------------------------------------------------------

# 19. Phase 14 --- Baseline Strategy

Before ML, create a simple rule-based baseline.

Example:

``` text
IF
RSI < 30
AND price > EMA200
AND bullish engulfing
THEN BUY
```

This gives you a baseline.

The ML model must beat or provide meaningful additional value over
reasonable baselines.

------------------------------------------------------------------------

# 20. Phase 15 --- ML Baseline Models

Train:

### Model 1

Logistic Regression

### Model 2

Random Forest

### Model 3

XGBoost

Compare:

``` text
Accuracy
Precision
Recall
F1
ROC-AUC where appropriate
PR-AUC where appropriate
Log loss
Calibration
```

For trading usefulness also evaluate:

``` text
Win rate
Profit factor
Average trade return
Maximum drawdown
Sharpe ratio
Turnover
```

------------------------------------------------------------------------

# 21. Phase 16 --- Time-Series Validation

Never use a normal random train/test split for the main evaluation.

Use chronological splits.

Example:

``` text
2023 ---------------- 2024
        TRAIN

2025
VALIDATION

2026
TEST
```

Then use walk-forward testing:

``` text
Train: 2023
Test:  early 2024

Train: 2023 + early 2024
Test:  late 2024

Train: 2023 + 2024
Test: 2025

...
```

This better represents real deployment.

------------------------------------------------------------------------

# 22. Phase 17 --- Probability Calibration

The system should not only output a class.

It should output probabilities.

Example:

``` json
{
  "UP": 0.68,
  "DOWN": 0.17,
  "NEUTRAL": 0.15
}
```

Check whether probabilities are calibrated.

A prediction of 70% should historically happen approximately 70% of the
time within the defined outcome class, subject to statistical
uncertainty.

------------------------------------------------------------------------

# 23. Phase 18 --- Feature Importance and Explainability

Determine which features contribute to predictions.

Use appropriate methods such as:

-   XGBoost feature importance
-   permutation importance
-   SHAP

Dashboard example:

``` text
Prediction: UP 68%

Important factors:
1. EMA trend
2. RSI
3. Volume ratio
4. ATR
5. Fib 0.618 distance
```

Do not claim that feature importance proves causation.

------------------------------------------------------------------------

# 24. Phase 19 --- Model Registry

Every trained model receives a version.

Example:

``` text
BTC_15M_XGB_v1.0
```

Store:

``` text
model version
feature version
dataset version
training date
training range
hyperparameters
metrics
artifact
status
```

Statuses:

``` text
EXPERIMENTAL
VALIDATED
STAGING
PRODUCTION
RETIRED
```

------------------------------------------------------------------------

# 25. Phase 20 --- Backtesting Engine

The backtester must simulate historical trading.

Inputs:

``` text
symbol
timeframe
initial capital
model version
strategy version
fees
slippage
position size
stop loss
take profit
date range
```

Process:

``` text
Historical candle
      ↓
Feature generation
      ↓
Prediction
      ↓
Signal
      ↓
Position
      ↓
Exit
      ↓
P&L
```

## Metrics

Calculate:

-   Total return
-   Annualized return where meaningful
-   Number of trades
-   Win rate
-   Loss rate
-   Average win
-   Average loss
-   Profit factor
-   Maximum drawdown
-   Sharpe ratio
-   Sortino ratio
-   Exposure
-   Turnover
-   Consecutive wins/losses
-   Average holding period

------------------------------------------------------------------------

# 26. Phase 21 --- Realistic Backtesting

Include:

### Trading fees

Model provider/exchange fees.

### Slippage

Do not assume every order executes at the exact candle close.

### Spread

Where applicable.

### Position sizing

Examples:

``` text
Fixed quantity
Fixed percentage of capital
Risk-based position sizing
```

### Execution assumptions

Document:

-   signal timestamp
-   entry timestamp
-   entry price
-   exit price
-   order type assumptions

The backtester must not give the strategy an unrealistic advantage.

------------------------------------------------------------------------

# 27. Phase 22 --- Backtest Anti-Overfitting Controls

Watch for:

-   Too many indicators.
-   Too many hyperparameters.
-   Repeated testing against the same test set.
-   Selecting the best result from hundreds of experiments.
-   Data leakage.
-   Look-ahead bias.
-   Survivorship bias.
-   Unrealistic fees.
-   Unrealistic execution.
-   Overfitting to one asset.
-   Overfitting to one timeframe.

Keep the final test period untouched until the model/strategy is
finalized.

------------------------------------------------------------------------

# 28. Phase 23 --- Paper Trading

Before live trading:

``` text
Real-time market data
       ↓
Production-like prediction
       ↓
Signal
       ↓
Virtual order
       ↓
Virtual P&L
```

No real money.

Record:

``` text
signal
timestamp
entry
stop
target
prediction probability
model version
outcome
```

Compare paper performance with backtest performance.

------------------------------------------------------------------------

# 29. Phase 24 --- Real-Time Data Pipeline

Implement real-time market data.

Preferred flow:

``` text
Market WebSocket
      ↓
Data Collector
      ↓
Redis / event layer
      ↓
Feature calculation
      ↓
Prediction
      ↓
Signal engine
      ↓
WebSocket
      ↓
Frontend
```

Important:

Only generate a finalized candle prediction when the required candle is
closed, unless the system explicitly supports intrabar prediction.

------------------------------------------------------------------------

# 30. Phase 25 --- Prediction Service

Create a Python inference service.

Example:

``` text
POST /predict
```

Request:

``` json
{
  "symbol": "BTCUSDT",
  "timeframe": "15m",
  "timestamp": "..."
}
```

Response:

``` json
{
  "modelVersion": "BTC_15M_XGB_v1.0",
  "prediction": "UP",
  "probabilityUp": 0.68,
  "probabilityDown": 0.17,
  "probabilityNeutral": 0.15
}
```

The service must load a specific model version rather than silently
using an arbitrary file.

------------------------------------------------------------------------

# 31. Phase 26 --- Signal Engine

Separate ML prediction from trading signal logic.

Example:

``` text
ML:
UP = 68%

Technical score:
78/100

Risk:
acceptable

Signal:
BUY
```

Possible signal states:

``` text
BUY
SELL
HOLD
NO_SIGNAL
```

Signal rules should be configurable.

Never hard-code business logic into the ML model.

------------------------------------------------------------------------

# 32. Phase 27 --- Risk Management

Create a dedicated risk-management module.

Features:

-   Maximum position size
-   Maximum daily loss
-   Maximum open positions
-   Stop loss
-   Take profit
-   Risk/reward ratio
-   Volatility-based sizing
-   Maximum drawdown protection
-   Cooldown after losses

Example:

``` text
Risk per trade = 1% of virtual capital
```

This is an example configuration, not a universal recommendation.

------------------------------------------------------------------------

# 33. Phase 28 --- Backend API

Spring Boot modules:

``` text
market
 ├── candles
 ├── symbols
 └── data-status

features
 ├── indicators
 ├── patterns
 └── market-structure

predictions
 ├── latest
 ├── history
 └── details

signals
 ├── latest
 └── history

backtests
 ├── create
 ├── run
 ├── results
 └── trades

models
 ├── list
 ├── details
 └── metrics
```

Use DTOs.

Do not expose JPA entities directly.

------------------------------------------------------------------------

# 34. Phase 29 --- Frontend Dashboard

Main screens:

## Dashboard

Show:

-   Selected symbol
-   Timeframe
-   Current price
-   Trend
-   Latest prediction
-   Prediction probabilities
-   Signal
-   Risk information

## Chart

Show:

-   Candlesticks
-   EMA
-   SMA
-   Bollinger Bands
-   Support/resistance
-   Fibonacci
-   Buy/sell markers
-   Pattern markers

## Prediction panel

``` text
UP       68%
DOWN     17%
NEUTRAL  15%
```

## Model panel

Show:

-   model version
-   feature version
-   prediction time
-   model metrics

## Backtesting panel

Show:

-   equity curve
-   drawdown
-   trade list
-   win rate
-   profit factor
-   Sharpe/Sortino
-   total return

## Data quality panel

Show:

-   latest candle
-   ingestion status
-   missing candles
-   provider status

------------------------------------------------------------------------

# 35. Phase 30 --- Real-Time Frontend Updates

Use WebSocket/SSE as appropriate.

Example:

``` text
New candle
   ↓
Backend
   ↓
Prediction
   ↓
Signal
   ↓
WebSocket
   ↓
React state
   ↓
Chart update
```

Do not refresh the entire page for every market update.

------------------------------------------------------------------------

# 36. Phase 31 --- Notifications

Later support:

-   Browser notification
-   Email
-   Telegram/other permitted notification channels

Example:

``` text
BTCUSDT 15m

New BUY signal

UP probability: 72%
Technical score: 81
Model: XGB_v1.2
```

Notifications must be optional.

------------------------------------------------------------------------

# 37. Phase 32 --- Authentication and Authorization

If the platform becomes multi-user:

-   User registration
-   Login
-   JWT/OAuth2
-   Role-based access
-   Admin role
-   User role

Protect:

-   Model management
-   Backtest creation
-   Data-provider credentials
-   Administrative APIs

Never expose API keys to the frontend.

------------------------------------------------------------------------

# 38. Phase 33 --- Secrets and Configuration

Never commit:

``` text
API keys
database passwords
JWT secrets
provider credentials
```

Use:

``` text
.env
environment variables
secret manager
```

Production secrets must not be stored in Git.

------------------------------------------------------------------------

# 39. Phase 34 --- Testing

## Backend

-   Unit tests
-   Repository tests
-   Service tests
-   Controller tests
-   Integration tests

## ML

-   Feature tests
-   Label-generation tests
-   Dataset tests
-   Model-loading tests
-   Prediction tests
-   Leakage tests

## Backtesting

Create deterministic test scenarios.

Example:

``` text
Known candle sequence
→ expected entry
→ expected stop
→ expected P&L
```

## Frontend

-   Component tests
-   API integration tests
-   WebSocket update tests

------------------------------------------------------------------------

# 40. Phase 35 --- Data Leakage Test Suite

Create explicit automated tests for leakage.

Examples:

-   Feature at T must not depend on T+1.
-   Rolling features must use past/current data only.
-   Swing detection must respect confirmation timing.
-   Fibonacci calculation must not use future confirmed swings.
-   Normalization/scaling must be fitted on training data only.
-   Feature selection must be performed without using the test period.
-   Hyperparameter tuning must not use the final test set.

This phase is mandatory.

------------------------------------------------------------------------

# 41. Phase 36 --- Monitoring

Monitor:

### Data

-   Provider availability
-   Last candle time
-   Missing candles
-   API errors
-   Rate-limit errors

### Model

-   Prediction distribution
-   Feature distribution
-   Probability distribution
-   Model latency
-   Prediction failures

### Strategy

-   Recent win rate
-   Drawdown
-   Profit factor
-   Drift

------------------------------------------------------------------------

# 42. Phase 37 --- Model Drift

Market behavior changes.

Monitor whether:

``` text
Training feature distribution
```

differs significantly from:

``` text
Current feature distribution
```

Monitor:

-   Feature drift
-   Prediction drift
-   Outcome drift
-   Performance degradation

When necessary:

``` text
Collect new data
      ↓
Re-evaluate features
      ↓
Retrain
      ↓
Validate
      ↓
Paper test
      ↓
Deploy
```

Never automatically deploy a retrained model without validation gates.

------------------------------------------------------------------------

# 43. Phase 38 --- Experiment Tracking

Every ML experiment should record:

``` text
Experiment ID
Dataset
Feature version
Label version
Model
Hyperparameters
Training period
Validation period
Metrics
Backtest metrics
Notes
```

Example:

``` text
EXP-00031
XGBoost
BTCUSDT
15m
Features v1.3
Labels v1.0
Max depth = 6
Learning rate = 0.05
```

This prevents losing track of experiments.

------------------------------------------------------------------------

# 44. Phase 39 --- Model Comparison Framework

Build a standard comparison table:

  Model             Accuracy   F1   Log Loss   Win Rate   Profit Factor   Max DD
  --------------- ---------- ---- ---------- ---------- --------------- --------
  Logistic                                                              
  Random Forest                                                         
  XGBoost                                                               

Do not select a model using accuracy alone.

------------------------------------------------------------------------

# 45. Phase 40 --- Advanced ML

Only after Version 1 is stable.

Possible models:

### LSTM

For sequential patterns.

### GRU

Simpler recurrent architecture.

### Temporal CNN

Alternative sequence model.

### Transformer

For longer sequence relationships.

### Ensemble

Combine:

``` text
XGBoost
+
LSTM
+
Technical score
```

Do not assume a more complex model will perform better.

------------------------------------------------------------------------

# 46. Phase 41 --- Chart Image ML

This is a separate research experiment.

Pipeline:

``` text
OHLCV
 ↓
Chart renderer
 ↓
Image dataset
 ↓
CNN / Vision Transformer
 ↓
Classification
```

Create consistent images:

-   Same dimensions
-   Same candle count
-   Same timeframe
-   Same scaling rules
-   No future candles
-   Same visual configuration

Compare image model performance with numerical model performance.

------------------------------------------------------------------------

# 47. Phase 42 --- Multi-Timeframe Analysis

After the single-timeframe model works:

``` text
5m
15m
1h
4h
```

Generate features such as:

``` text
5m trend
15m trend
1h trend
4h trend
```

Then:

``` text
Lower timeframe signal
+
Higher timeframe confirmation
```

------------------------------------------------------------------------

# 48. Phase 43 --- Multi-Asset Support

Later support:

``` text
BTCUSDT
ETHUSDT
SOLUSDT
...
```

Then consider:

-   Asset-specific models
-   One global model
-   Asset embedding
-   Market regime features

Do not add many assets until the data pipeline is stable.

------------------------------------------------------------------------

# 49. Phase 44 --- Market Regime Detection

Identify regimes such as:

``` text
Trending
Sideways
High volatility
Low volatility
Bullish
Bearish
```

Possible approaches:

-   Rule-based regime classification
-   Clustering
-   Hidden Markov Models
-   ML classifiers

Then evaluate model performance by regime.

------------------------------------------------------------------------

# 50. Phase 45 --- Sentiment / External Data

Future features may include:

-   News sentiment
-   Social sentiment
-   Funding rates
-   Open interest
-   Liquidations
-   On-chain metrics
-   Economic events

Keep these as separate feature groups.

Always timestamp them correctly so future information cannot leak into
past predictions.

------------------------------------------------------------------------

# 51. Phase 46 --- TradingView Integration

TradingView should be treated primarily as a
visualization/alert/integration layer where permitted.

Possible uses:

-   Chart visualization
-   User alerts
-   Webhook integration
-   External chart interaction

Do not scrape chart images or bypass provider restrictions.

All data usage must comply with the relevant provider's terms and
licensing.

------------------------------------------------------------------------

# 52. Phase 47 --- Paper Trading Engine

Create virtual accounts:

``` text
paper_account
paper_order
paper_position
paper_trade
paper_balance_history
```

Support:

``` text
Market order simulation
Limit order simulation
Stop loss
Take profit
Fees
Slippage
```

No real-money execution in the initial project.

------------------------------------------------------------------------

# 53. Phase 48 --- Optional Broker/Exchange Execution

Only after:

1.  Historical backtesting.
2.  Walk-forward testing.
3.  Out-of-sample evaluation.
4.  Paper trading.
5.  Stability monitoring.
6.  Strong risk controls.

If implemented, start with an explicit disabled-by-default execution
mode.

Use:

``` text
ANALYSIS
PAPER
LIVE
```

as separate environments.

Never allow accidental live execution from development code.

------------------------------------------------------------------------

# 54. Phase 49 --- Dockerization

Containers:

``` text
postgres
redis
backend
ml-service
frontend
```

Optional later:

``` text
kafka
monitoring
model registry
```

Provide:

``` bash
docker compose up
```

for local development.

------------------------------------------------------------------------

# 55. Phase 50 --- CI/CD

Pipeline:

``` text
Pull Request
    ↓
Build
    ↓
Unit Tests
    ↓
Integration Tests
    ↓
ML Tests
    ↓
Leakage Tests
    ↓
Security Checks
    ↓
Build Docker Images
    ↓
Deploy
```

ML model deployment should have separate validation gates.

------------------------------------------------------------------------

# 56. Phase 51 --- Documentation

Required documents:

``` text
README.md
PROJECT_SCOPE.md
ARCHITECTURE.md
DATA_PROVIDER_DECISION.md
DATABASE.md
DATA_PIPELINE.md
FEATURES.md
LABELING.md
ML_MODEL.md
BACKTESTING.md
API.md
REALTIME.md
DEPLOYMENT.md
SECURITY.md
EXPERIMENTS.md
MODEL_REGISTRY.md
```

Every major design decision should be documented.

------------------------------------------------------------------------

# 57. Phase 52 --- Security

Security requirements:

-   Encrypt credentials.
-   Use HTTPS in production.
-   Validate API input.
-   Apply authentication.
-   Apply authorization.
-   Rate-limit public endpoints.
-   Avoid exposing stack traces.
-   Protect admin endpoints.
-   Rotate secrets.
-   Log security events.
-   Never log API keys.
-   Validate webhook signatures where supported.
-   Store secrets outside source control.

------------------------------------------------------------------------

# 58. Phase 53 --- Performance

Measure:

``` text
Data ingestion latency
Feature calculation latency
Model inference latency
API latency
WebSocket latency
Database query latency
Backtest runtime
```

Optimize only after measuring.

Use:

-   Database indexes
-   Batch inserts
-   Redis caching
-   Async processing where justified
-   Vectorized Pandas/NumPy operations
-   Efficient model inference

------------------------------------------------------------------------

# 59. Phase 54 --- Observability

Implement:

-   Structured logging
-   Correlation IDs
-   Metrics
-   Health endpoints
-   Error tracking

Useful health checks:

``` text
/database
/provider
/redis
/ml-service
```

Example:

``` text
GET /actuator/health
```

for Spring Boot.

------------------------------------------------------------------------

# 60. Phase 55 --- Production Readiness Checklist

Before calling Version 1 production-ready:

### Data

-   [ ] Raw data verified.
-   [ ] Missing data handled.
-   [ ] Duplicate handling implemented.
-   [ ] Provider failure handling implemented.

### ML

-   [ ] No known leakage.
-   [ ] Chronological validation.
-   [ ] Walk-forward testing.
-   [ ] Model versioning.
-   [ ] Probability calibration evaluated.
-   [ ] Drift monitoring planned.

### Backtesting

-   [ ] Fees included.
-   [ ] Slippage included.
-   [ ] Execution assumptions documented.
-   [ ] Drawdown calculated.
-   [ ] Out-of-sample test completed.

### Application

-   [ ] Authentication.
-   [ ] Authorization.
-   [ ] API validation.
-   [ ] Logging.
-   [ ] Monitoring.
-   [ ] Error handling.

### Deployment

-   [ ] Docker.
-   [ ] CI/CD.
-   [ ] Secrets management.
-   [ ] Backups.
-   [ ] Health checks.

------------------------------------------------------------------------

# 61. Version Roadmap

## Version 0.1 --- Data Foundation

``` text
Market API
↓
Historical candles
↓
PostgreSQL
↓
Data quality report
```

## Version 0.2 --- Feature Engine

``` text
OHLCV
↓
Indicators
↓
Candlestick patterns
↓
Market structure
↓
Fibonacci
```

## Version 0.3 --- Dataset

``` text
Features
+
Labels
↓
Versioned training dataset
```

## Version 0.4 --- ML

``` text
Logistic Regression
Random Forest
XGBoost
↓
Model comparison
```

## Version 0.5 --- Backtesting

``` text
ML predictions
↓
Trading simulation
↓
Performance metrics
```

## Version 0.6 --- API

``` text
Spring Boot
↓
Prediction API
↓
Backtest API
```

## Version 0.7 --- Dashboard

``` text
Next.js
↓
Chart
Prediction
Signal
Backtest
```

## Version 0.8 --- Real-time

``` text
WebSocket
↓
Live candles
↓
Live features
↓
Live prediction
```

## Version 0.9 --- Paper Trading

``` text
Real-time signal
↓
Virtual execution
↓
Virtual P&L
```

## Version 1.0 --- Integrated Platform

``` text
Data
+
Features
+
ML
+
Backtesting
+
Real-time
+
Dashboard
+
Paper Trading
```

------------------------------------------------------------------------

# 62. AI Agent Operating Instructions

This section is intended to be given to an AI coding agent together with
the repository.

## 62.1 Primary instruction

You are implementing the AI-Based Trading Prediction & Market Analysis
Platform according to this document.

Follow the implementation phases sequentially.

Do not skip foundational phases merely to implement advanced
functionality.

## 62.2 Before modifying code

Always:

1.  Inspect the current repository.
2.  Identify existing architecture.
3.  Read relevant documentation.
4.  Identify completed phases.
5.  Identify the current phase.
6.  Check existing tests.
7.  Avoid unnecessary rewrites.

## 62.3 Phase discipline

Work on one phase at a time.

Before moving to the next phase:

-   Implement.
-   Test.
-   Document.
-   Verify.
-   Report what changed.
-   Report remaining issues.
-   Confirm the phase's done criteria.

## 62.4 Do not invent APIs

If an external provider API is required:

1.  Check the official documentation.
2.  Confirm endpoint and authentication requirements.
3.  Confirm rate limits.
4.  Confirm historical-data availability.
5.  Confirm licensing/usage restrictions.
6.  Implement behind an abstraction.

Never invent endpoint names or response formats.

## 62.5 Data safety

Never:

-   overwrite raw market data
-   fabricate market data
-   fabricate backtest results
-   fabricate model metrics
-   fabricate API responses
-   use future candles as features
-   silently modify historical datasets

If data is unavailable, report the problem.

## 62.6 ML safety

Never claim:

``` text
The model guarantees profit.
```

Use:

``` text
historical performance
probability
experimental result
backtest result
out-of-sample result
```

## 62.7 Coding standards

Prefer:

-   clean architecture
-   meaningful names
-   small services
-   DTOs
-   validation
-   unit tests
-   integration tests
-   typed interfaces
-   configuration through environment variables
-   explicit error handling
-   documentation

Avoid:

-   unnecessary abstractions
-   premature microservices
-   duplicated logic
-   magic numbers
-   hard-coded secrets
-   hard-coded provider credentials
-   huge classes
-   undocumented ML transformations

## 62.8 Every feature must answer

Before implementation:

``` text
What problem does this solve?
What data does it require?
Can it introduce future leakage?
How is it tested?
How is it versioned?
How is it evaluated?
```

------------------------------------------------------------------------

# 63. AI Agent Task Format

For every implementation task, the agent should report:

``` text
PHASE:
TASK:

UNDERSTANDING:
...

FILES CHANGED:
...

IMPLEMENTATION:
...

TESTS:
...

VALIDATION:
...

RISKS:
...

DOCUMENTATION:
...

DONE CRITERIA:
...

NEXT TASK:
...
```

------------------------------------------------------------------------

# 64. Definition of Done

A phase is considered complete only when:

1.  Implementation exists.
2.  Tests exist.
3.  Tests pass.
4.  Documentation is updated.
5.  No known critical issue remains.
6.  The phase's acceptance criteria are satisfied.
7.  The output can be used by the next phase.

------------------------------------------------------------------------

# 65. Final End-to-End Workflow

The final system should operate like this:

``` text
                  MARKET DATA
                      |
          +-----------+-----------+
          |                       |
      Historical               Real-time
          |                       |
          v                       v
     PostgreSQL                WebSocket
          |                       |
          +-----------+-----------+
                      |
                      v
               FEATURE ENGINE
                      |
       +--------------+--------------+
       |              |              |
       v              v              v
   Indicators     Patterns       Structure
       |              |              |
       +--------------+--------------+
                      |
                      v
                Fibonacci
                      |
                      v
             VERSIONED FEATURES
                      |
                      v
              LABEL GENERATION
                      |
                      v
             TRAINING DATASET
                      |
                      v
               ML TRAINING
                      |
       +--------------+--------------+
       |              |              |
       v              v              v
   Logistic       Random Forest   XGBoost
       |              |              |
       +--------------+--------------+
                      |
                      v
                MODEL EVALUATION
                      |
                      v
               MODEL REGISTRY
                      |
                      v
              PREDICTION SERVICE
                      |
                      v
               SIGNAL ENGINE
                      |
             +--------+--------+
             |                 |
             v                 v
        BACKTESTING       REAL-TIME
             |                 |
             +--------+--------+
                      |
                      v
               PAPER TRADING
                      |
                      v
                DASHBOARD
```

------------------------------------------------------------------------

# 66. Future Research Roadmap

After Version 1 is stable, investigate:

1.  LSTM/GRU.
2.  Transformer-based time-series models.
3.  CNN/ViT chart-image classification.
4.  Multi-timeframe models.
5.  Multi-asset models.
6.  Market regime detection.
7.  News sentiment.
8.  Social sentiment.
9.  Funding rates.
10. Open interest.
11. Liquidation data.
12. Order-book features.
13. Ensemble models.
14. Reinforcement learning research.
15. Portfolio-level prediction.
16. Position-sizing optimization.
17. Automated feature selection.
18. Online/continual learning.
19. Model drift detection.
20. Advanced experiment tracking.

These are **future research items**, not Version 1 requirements.

------------------------------------------------------------------------

# 67. Recommended First 10 Implementation Tasks

Do not start with ML immediately.

Execute these tasks in order:

### Task 1

Create repository and project structure.

### Task 2

Set up PostgreSQL and Docker Compose.

### Task 3

Implement the `market_candle` schema.

### Task 4

Implement the market-data provider abstraction.

### Task 5

Implement historical candle ingestion.

### Task 6

Implement data-quality validation.

### Task 7

Collect and verify the initial BTCUSDT 15-minute dataset.

### Task 8

Implement the Python feature pipeline.

### Task 9

Implement the label-generation pipeline.

### Task 10

Generate and inspect the first versioned training dataset.

Only after these ten tasks are working should the first ML model be
trained.

------------------------------------------------------------------------

# 68. First Milestone

The first major milestone is:

> **A reproducible pipeline that converts historical market data into a
> leakage-free, versioned machine-learning dataset.**

Success looks like:

``` text
Market API
    ↓
Historical BTCUSDT 15m candles
    ↓
Validated PostgreSQL data
    ↓
Feature engineering
    ↓
Label generation
    ↓
Versioned dataset
    ↓
Dataset quality report
```

At this point, the project has a solid foundation.

Do not move to complex neural networks before this milestone is
reliable.

------------------------------------------------------------------------

# 69. Project Success Definition

The project is successful if it can demonstrate:

1.  Reliable market-data ingestion.
2.  Reproducible feature generation.
3.  Correct target generation.
4.  No known data leakage.
5.  Reproducible ML training.
6.  Proper chronological evaluation.
7.  Realistic backtesting.
8.  Real-time inference.
9.  Explainable predictions.
10. Paper-trading validation.
11. Production-quality software engineering.
12. Clear evidence showing both strengths and limitations of the model.

The goal is **not** to manufacture a high backtest number.

The goal is to build a scientifically and technically credible system
that can test whether market information and engineered features provide
measurable predictive value.

------------------------------------------------------------------------

# 70. Immediate Next Action

Start with:

**PHASE 0 → Project Definition**

Then proceed strictly in order.

The first coding milestone should be:

**PHASE 1 → Repository and Development Environment**

The first data milestone should be:

**PHASE 3 → Historical Market Data Ingestion**

The first ML milestone should be:

**PHASE 10--12 → Feature + Label + Dataset Generation**

The first serious evaluation milestone should be:

**PHASE 16--21 → Time-Series Validation + ML + Backtesting**

Do not skip directly to real-time trading or deep learning.
