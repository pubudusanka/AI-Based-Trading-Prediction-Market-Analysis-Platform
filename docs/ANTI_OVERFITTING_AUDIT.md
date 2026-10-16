# Backtest Anti-Overfitting & Robustness Audit: RandomForest

**Asset:** BTC/USDT (15m)  
**Evaluated Holdout Samples:** 300  
**Generated At:** 2026-10-16T18:41:30.776464+00:00  

---

## 1. Deflated Sharpe Ratio (DSR) & Statistical Significance

> [!NOTE]
> **Methodology:** Marcos Lopez de Prado (2014). Adjusts observed Sharpe Ratio for selection bias under multiple testing, sample length, and return non-normality (skewness and kurtosis).

| Metric | Value | Reference Benchmark | Status |
|---|---|---|---|
| **Observed Annualized Sharpe** | 0.00 | > 1.00 desired | FAIL |
| **Expected Max Sharpe E[max SR]** | 0.00 | Based on 20 trials tested | Statistical Hurdle |
| **Deflated Sharpe Ratio (DSR)** | **0.0000** (0.0%) | $\ge 0.95$ (95% confidence) | **POTENTIAL OVERFIT** |
| **DSR p-value** | 1.0000 | $\le 0.05$ | NOT SIGNIFICANT |
| **Return Skewness** | +0.000 | 0.00 (Gaussian) | Left-skewed |
| **Return Excess Kurtosis** | +0.000 | 0.00 (Gaussian) | Thin-tailed |
| **Holdout Observations (T)** | 299 | > 500 desired | Sufficient |

---

## 2. Friction Stress Testing & Margin of Safety

Simulating execution degradation under surging network gas, exchange taker rate increases, and wide orderbook spreads.

| Scenario | Fee Rate | Slippage | Net Return | Profit Factor | Win Rate | Sharpe | Max Drawdown | Status |
|---|---|---|---|---|---|---|---|---|
| **Base Reality** | 0.10% | 0.05% | +0.00% | 0.00 | 0.0% | 0.00 | 0.00% | `UNPROFITABLE` |
| **Double Fees (0.20%)** | 0.20% | 0.05% | +0.00% | 0.00 | 0.0% | 0.00 | 0.00% | `UNPROFITABLE` |
| **Double Slippage (0.10%)** | 0.10% | 0.10% | +0.00% | 0.00 | 0.0% | 0.00 | 0.00% | `UNPROFITABLE` |
| **Extreme Frictions (2x Fee, 3x Slip)** | 0.20% | 0.15% | +0.00% | 0.00 | 0.0% | 0.00 | 0.00% | `UNPROFITABLE` |
| **High Slippage Stress (0.25%)** | 0.10% | 0.25% | +0.00% | 0.00 | 0.0% | 0.00 | 0.00% | `UNPROFITABLE` |

- **Break-Even Exchange Fee:** `0.05%` (Max tolerable fee before strategy becomes net negative).
- **Break-Even Execution Slippage:** `0.02%` (Max tolerable adverse slippage before failure).

---

## 3. Anti-Overfitting Governance Checklist

| Verification Item | Requirement | Measured Value | Compliance |
|---|---|---|---|
| **Feature Space Complexity** | $\le 50$ engineered features | 83 features | WARNING |
| **Hyperparameter Tuning Scope** | $\le 10$ parameters tuned | 8 parameters | COMPLIANT |
| **Lookahead Leakage Guard** | Strict chronological embargo | Zero Lookahead Invariant | **PASS** |
| **Holdout Integrity** | Test window strictly unexposed | 300 candles | **PASS** |
| **Deflated Sharpe Confidence** | DSR $\ge 0.95$ | 0.0000 | FAIL |

### Final Certification: **REJECTED - OVERFITTING DETECTED**
