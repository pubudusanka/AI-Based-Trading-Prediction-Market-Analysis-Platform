# Project Scope & Definition (Phase 0)

**Project Name:** AI-Based Trading Prediction & Market Analysis Platform  
**Document Version:** 1.0  
**Status:** Approved / Active Baseline  
**Reference Document:** `AI_Trading_Prediction_Platform_A-Z_Implementation_Plan.md`

---

## 1. Project Objective & Core Question

The objective is to build a research-grade, production-style trading prediction and market analysis platform. 
The system does **not** claim to predict the market with certainty. Instead, it frames market forecasting as a strictly defined probabilistic classification problem:

> *"Given the market information available up to and including time $T$, what is the probability that price will hit a target profit threshold (+1.0%) before hitting a stop loss threshold (-0.5%) within the next 20 candles?"*

---

## 2. Initial Operational Scope (Version 1.0)

| Parameter | Specification | Details |
|---|---|---|
| **Primary Asset** | `BTC/USDT` | Spot market pair with high liquidity and continuous data |
| **Primary Timeframe** | `15-minute (15m)` | Balances signal timeliness with lower noise |
| **Historical Data Window** | 1 – 2 Years | Continuous 15m OHLCV candle series |
| **Prediction Horizon ($N$)** | 20 candles | Equivalent to 5 hours ahead in 15m intervals |
| **Target Profit Threshold** | `+1.0%` | Relative to the close price at candle $T$ |
| **Stop Loss Threshold** | `-0.5%` | Relative to the close price at candle $T$ |
| **Labeling Methodology** | Fixed Horizon Triple-Barrier | Evaluates upper target hit vs. lower stop hit vs. timeout |
| **Target Classes** | `UP` (Target first), `DOWN` (Stop first), `NEUTRAL` (Neither within $N$) | 3-class probabilistic classification |

---

## 3. Machine Learning Baseline & Architecture

1. **Baseline Models:**
   - Logistic Regression (interpretable baseline)
   - Random Forest (non-linear baseline)
   - **XGBoost Classifier (Primary V1 Model)**
2. **Evaluation Metrics:**
   - Multi-class Log Loss & Brier Score (probabilistic calibration)
   - Precision & Recall per class (especially precision on `UP` and `DOWN`)
   - Macro F1-score & ROC-AUC
   - Backtest Sharpe Ratio, Profit Factor, Maximum Drawdown (MDD), and Win Rate
3. **Data Integrity & Validation:**
   - Strict chronological walk-forward validation (No random K-Fold splits)
   - Zero look-ahead bias (features strictly calculated using data $\le T$)
   - Raw OHLCV records are immutable and stored untouched

---

## 4. Technical Stack

- **Backend:** Java 21 LTS, Spring Boot 3.x, Spring Data JPA, REST APIs, WebSocket
- **ML / Feature Pipeline:** Python 3.14+, Pandas, NumPy, Scikit-Learn, XGBoost, FastAPI
- **Database & Persistence:** PostgreSQL (timeseries-ready OHLCV + entities)
- **Cache & Pub/Sub:** Redis
- **Frontend Dashboard:** Next.js 14+ / React, TypeScript, Lightweight Charts / TradingView
- **Infrastructure:** Docker & Docker Compose

---

## 5. Explicit Non-Goals for Version 1.0

To prevent premature complexity and scope creep, the following are **out of scope** for V1:
- ❌ Automated live trading with real funds
- ❌ High-frequency trading (HFT) / sub-second tick execution
- ❌ Multi-asset portfolio balancing
- ❌ End-to-end deep learning or chart-image computer vision (reserved for V2+)
- ❌ Real-time sentiment analysis from social media/news (reserved for V2+)
- ❌ Complex microservices mesh (use clean modular monolithic services first)

---

## 6. Success Criteria

1. **Pipeline Integrity:** Automated ingestion of continuous 15m `BTC/USDT` data with zero missing intervals and verified schema.
2. **Leakage-Free Features:** Verified automated unit tests confirming no $T+k$ data leaks into features at time $T$.
3. **Predictive Performance:** The XGBoost model demonstrates positive information coefficient and statistically significant edge over random baseline on out-of-sample data.
4. **Execution Realism:** Backtesting results incorporate fees (0.075% - 0.1%), spread, and slippage.
5. **Interactive Visualization:** Next.js dashboard displaying live/historical candlesticks, technical indicators, probabilistic model outputs, and backtest equity curves.
