# Feature Importance & Model Explainability Report: RandomForest

**Asset:** BTC/USDT (15m)  
**Evaluated Test Samples:** 150  
**Generated At:** 2026-10-16T17:57:55.382701+00:00  

> [!IMPORTANT]
> **Causality Notice:** DISCLAIMER: Feature importance and attribution values quantify empirical statistical associations within the model's fitted decision landscape. They do NOT establish or prove economic or financial causation in market mechanics.

---

## 1. Native Model Feature Importance (MDI / Gini / GBDT Gain)

| Rank | Feature | Importance Score | Relative Share |
|---|---|---|---|
| 1 | `macd_hist` | 0.0661 | 6.61% |
| 2 | `percentage_change` | 0.0565 | 5.65% |
| 3 | `ema_slope_21` | 0.0518 | 5.18% |
| 4 | `adx_14` | 0.0509 | 5.09% |
| 5 | `returns` | 0.0470 | 4.70% |
| 6 | `stoch_d` | 0.0463 | 4.63% |
| 7 | `log_returns` | 0.0434 | 4.34% |
| 8 | `stoch_k` | 0.0427 | 4.27% |
| 9 | `price_vs_ema_21` | 0.0424 | 4.24% |
| 10 | `macd` | 0.0395 | 3.95% |
| 11 | `price_vs_ema_200` | 0.0351 | 3.51% |
| 12 | `ema_200` | 0.0311 | 3.11% |
| 13 | `resistance_price` | 0.0302 | 3.02% |
| 14 | `roc_10` | 0.0271 | 2.71% |
| 15 | `sma_50` | 0.0250 | 2.50% |

---

## 2. Out-of-Sample Permutation Feature Importance

Permutation importance quantifies the drop in Balanced Accuracy when a feature column is shuffled out-of-sample.

| Rank | Feature | Mean Accuracy Drop (Δ) | Std Dev (±) |
|---|---|---|---|
| 1 | `returns` | +0.0000 | ±0.0000 |
| 2 | `log_returns` | +0.0000 | ±0.0000 |
| 3 | `percentage_change` | +0.0000 | ±0.0000 |
| 4 | `body_size` | +0.0000 | ±0.0000 |
| 5 | `body_percentage` | +0.0000 | ±0.0000 |
| 6 | `upper_wick` | +0.0000 | ±0.0000 |
| 7 | `lower_wick` | +0.0000 | ±0.0000 |
| 8 | `candle_range` | +0.0000 | ±0.0000 |
| 9 | `body_to_range_ratio` | +0.0000 | ±0.0000 |
| 10 | `bullish_flag` | +0.0000 | ±0.0000 |
| 11 | `bearish_flag` | +0.0000 | ±0.0000 |
| 12 | `sma_20` | +0.0000 | ±0.0000 |
| 13 | `sma_50` | +0.0000 | ±0.0000 |
| 14 | `sma_200` | +0.0000 | ±0.0000 |
| 15 | `ema_9` | +0.0000 | ±0.0000 |

---

## 3. Global SHAP Feature Importance (Mean |SHAP Value|)

| Rank | Feature | Mean |SHAP| Attribution | Relative Contribution |
|---|---|---|---|
| 1 | `adx_14` | 0.0411 | 7.96% |
| 2 | `percentage_change` | 0.0320 | 6.18% |
| 3 | `macd_hist` | 0.0307 | 5.94% |
| 4 | `ema_slope_21` | 0.0285 | 5.51% |
| 5 | `returns` | 0.0264 | 5.11% |
| 6 | `log_returns` | 0.0263 | 5.09% |
| 7 | `stoch_d` | 0.0259 | 5.02% |
| 8 | `price_vs_ema_200` | 0.0179 | 3.47% |
| 9 | `macd_signal` | 0.0171 | 3.30% |
| 10 | `macd` | 0.0169 | 3.28% |
| 11 | `ema_50` | 0.0167 | 3.23% |
| 12 | `stoch_k` | 0.0163 | 3.15% |
| 13 | `obv` | 0.0161 | 3.12% |
| 14 | `ema_200` | 0.0154 | 2.98% |
| 15 | `price_vs_ema_21` | 0.0143 | 2.76% |

---

## 4. Single-Prediction Real-Time Attribution Example

```text
Prediction: NEUTRAL 87.2%

Important factors:
1. Macd Hist (+0.05) [NEUTRAL]
2. Ema Slope 21 (+0.05) [NEUTRAL]
3. Stoch D (+0.04) [NEUTRAL]
4. Percentage Change (+0.03) [NEUTRAL]
5. Macd (+0.03) [NEUTRAL]
```

### JSON Payload Contract (REST API / WebSocket):
```json
{
  "symbol": "BTC/USDT",
  "timeframe": "15m",
  "prediction": "NEUTRAL",
  "probability": 0.8718,
  "probabilities": {
    "DOWN": 0.1282,
    "NEUTRAL": 0.8718,
    "UP": 0.0
  },
  "top_factors": [
    {
      "rank": 1,
      "feature": "macd_hist",
      "value": 2.8434,
      "attribution": 0.052,
      "impact": "NEUTRAL"
    },
    {
      "rank": 2,
      "feature": "ema_slope_21",
      "value": 0.0009,
      "attribution": 0.0456,
      "impact": "NEUTRAL"
    },
    {
      "rank": 3,
      "feature": "stoch_d",
      "value": 67.8687,
      "attribution": 0.037,
      "impact": "NEUTRAL"
    },
    {
      "rank": 4,
      "feature": "percentage_change",
      "value": -0.0037,
      "attribution": 0.0335,
      "impact": "NEUTRAL"
    },
    {
      "rank": 5,
      "feature": "macd",
      "value": 64.052,
      "attribution": 0.0281,
      "impact": "NEUTRAL"
    }
  ],
  "disclaimer": "DISCLAIMER: Feature importance and attribution values quantify empirical statistical associations within the model's fitted decision landscape. They do NOT establish or prove economic or financial causation in market mechanics.",
  "timestamp": "2026-10-16T17:57:55.382568+00:00"
}
```
