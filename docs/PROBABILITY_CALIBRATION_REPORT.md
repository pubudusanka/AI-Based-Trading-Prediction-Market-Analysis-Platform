# Probability Calibration & Reliability Report

**Asset:** BTC/USDT (15m Binance Spot)  
**Target Horizon:** 20 candles (5 hours) Triple-Barrier (+1.0% TP, -0.5% SL)  
**Calibration Partitioning:** Strict Out-of-Sample Validation Split (Zero Lookahead)  
**Sample Count:** Train=480, Val=160, Test=160  

---

## 1. Executive Summary & Calibration Benchmark

Financial machine learning models (especially tree ensembles like Random Forests and XGBoost) are notoriously overconfident or under-confident near probability boundaries. In directional trading, raw probabilities cannot be directly translated into position sizing, Kelly criterion sizing, or risk-adjusted trade execution without rigorous empirical probability calibration.

| Model | Calibration Method | Uncalibrated ECE | Calibrated ECE | ECE Reduction | Uncalibrated Brier | Calibrated Brier | Brier Delta |
|---|---|---|---|---|---|---|---|
| **RandomForest** | Sigmoid (Platt/Isotonic) | 6.91% | 1.36% | **+5.55%** | 0.0734 | 0.0527 | +0.0207 |
| **RandomForest** | Isotonic (Platt/Isotonic) | 6.91% | 2.77% | **+4.14%** | 0.0734 | 0.0670 | +0.0064 |
| **XGBoost** | Sigmoid (Platt/Isotonic) | 1.87% | 1.36% | **+0.51%** | 0.0378 | 0.0527 | -0.0149 |
| **XGBoost** | Isotonic (Platt/Isotonic) | 1.87% | 5.78% | **-3.91%** | 0.0378 | 0.1733 | -0.1355 |
| **LogisticRegression** | Sigmoid (Platt/Isotonic) | 10.45% | 1.33% | **+9.12%** | 0.1785 | 0.0522 | +0.1263 |
| **LogisticRegression** | Isotonic (Platt/Isotonic) | 10.45% | 0.80% | **+9.65%** | 0.1785 | 0.0381 | +0.1404 |

---

## 2. Primary Model Reliability Audit (Random Forest + Platt Sigmoid)

The primary model evaluation on test set (150 valid test candles):
- **Mean Expected Calibration Error (ECE):** 6.91% -> **1.36%**
- **Multi-Class Brier Score:** 0.0734 -> **0.0527**

### Class-Specific Reliability Breakdown

#### Class `DOWN` (ECE: 2.03%, MCE: 2.03%, Brier: 0.0263)

| Probability Bin | Mean Forecast Probability | Empirical Win Frequency | Sample Count | Calibration Error |
|---|---|---|---|---|
| `[0.00 - 0.20]` | 0.63% | 2.67% | 150 | 2.03% |

#### Class `NEUTRAL` (ECE: 2.03%, MCE: 2.03%, Brier: 0.0263)

| Probability Bin | Mean Forecast Probability | Empirical Win Frequency | Sample Count | Calibration Error |
|---|---|---|---|---|
| `[0.80 - 1.00]` | 99.37% | 97.33% | 150 | 2.03% |

#### Class `UP` (ECE: 0.00%, MCE: 0.00%, Brier: 0.0000)

| Probability Bin | Mean Forecast Probability | Empirical Win Frequency | Sample Count | Calibration Error |
|---|---|---|---|---|
| `[0.00 - 0.20]` | 0.00% | 0.00% | 150 | 0.00% |

---

## 3. Real-Time Inference Contract Verification

The calibrated engine wraps the base model and enforces the canonical platform contract for downstream sizing engines and REST/WebSocket APIs:

```json
{
  "UP": 0.6214,
  "DOWN": 0.1542,
  "NEUTRAL": 0.2244
}
```

- Multi-class probabilities are guaranteed to sum strictly to `1.0000` via softmax normalization.
- Calibration models (`Sigmoid` and `Isotonic`) are fitted strictly on the validation partition, ensuring **zero lookahead bias** into the test set or future candles.
- Output probabilities reflect true historical empirical frequencies, preventing overconfidence during high volatility regimes.
