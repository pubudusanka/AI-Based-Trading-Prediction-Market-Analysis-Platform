# Exploratory Data Analysis Report: BTC/USDT (15m)

**Generated At:** 2026-10-16 16:53:25 UTC  
**Total Samples:** 1,500  
**Valid Target Samples:** 1,480  
**Target Imbalance Ratio:** 210.00 : 1  

---

## 1. Target Class Distribution

| Class | Count | Percentage | Description |
|---|---|---|---|
| **UP** | 636 | 42.97% | Profit target reached (+1.0%) before stop |
| **DOWN** | 840 | 56.76% | Stop loss triggered (-0.5%) before target |
| **NEUTRAL** | 4 | 0.27% | Neither barrier touched within 20 candles |

> [!WARNING]
> Significant class imbalance detected (210.00:1). Models must be evaluated with Balanced Accuracy, Macro F1, and PR-AUC, not raw accuracy.

---

## 2. Missing Value & Data Quality Audit

| Feature | Missing Count | Missing Pct | Recommended Action |
|---|---|---|---|
| `returns` | 1 | 0.07% | Forward-fill / Drop warm-up rows |
| `log_returns` | 1 | 0.07% | Forward-fill / Drop warm-up rows |
| `percentage_change` | 1 | 0.07% | Forward-fill / Drop warm-up rows |
| `sma_20` | 19 | 1.27% | Forward-fill / Drop warm-up rows |
| `sma_50` | 49 | 3.27% | Forward-fill / Drop warm-up rows |
| `sma_200` | 199 | 13.27% | Forward-fill / Drop warm-up rows |
| `rsi_14` | 1 | 0.07% | Forward-fill / Drop warm-up rows |
| `stoch_k` | 13 | 0.87% | Forward-fill / Drop warm-up rows |
| `stoch_d` | 15 | 1.00% | Forward-fill / Drop warm-up rows |
| `roc_10` | 10 | 0.67% | Forward-fill / Drop warm-up rows |
| `bb_width_20` | 19 | 1.27% | Forward-fill / Drop warm-up rows |
| `rolling_std_20` | 20 | 1.33% | Forward-fill / Drop warm-up rows |
| `ema_slope_21` | 5 | 0.33% | Forward-fill / Drop warm-up rows |
| `volume_ma_20` | 19 | 1.27% | Forward-fill / Drop warm-up rows |
| `volume_ratio_20` | 19 | 1.27% | Forward-fill / Drop warm-up rows |

---

## 3. Top Feature Candidates (ANOVA F-Score Ranking)

Features ranked by statistical separation across the 3 target classes:

| Rank | Feature | F-Statistic | p-value | Correlation with Direction |
|---|---|---|---|---|
| 1 | `dist_to_support` | 7.07 | 8.78e-04 | +0.0684 |
| 2 | `rsi_14` | 5.86 | 2.93e-03 | +0.0646 |
| 3 | `price_vs_ema_21` | 5.44 | 4.42e-03 | +0.0642 |
| 4 | `stoch_k` | 5.43 | 4.45e-03 | +0.0741 |
| 5 | `obv` | 5.27 | 5.26e-03 | +0.0719 |
| 6 | `fib_swing_range` | 5.24 | 5.38e-03 | +0.0711 |
| 7 | `active_swing_high_price` | 5.21 | 5.54e-03 | +0.0741 |
| 8 | `resistance_price` | 5.21 | 5.54e-03 | +0.0741 |
| 9 | `stoch_d` | 5.04 | 6.56e-03 | +0.0782 |
| 10 | `fib_level_1000` | 4.92 | 7.45e-03 | +0.0749 |
| 11 | `fib_level_786` | 4.88 | 7.71e-03 | +0.0745 |
| 12 | `fib_level_618` | 4.85 | 7.94e-03 | +0.0742 |
| 13 | `fib_level_500` | 4.83 | 8.12e-03 | +0.0739 |
| 14 | `fib_level_382` | 4.81 | 8.31e-03 | +0.0737 |
| 15 | `fib_level_236` | 4.78 | 8.56e-03 | +0.0733 |

---

## 4. Multicollinearity & High Correlation Pairs (|r| >= 0.85)

The following feature pairs exhibit strong collinearity. Consider PCA or L1 regularization during feature selection:

| Feature 1 | Feature 2 | Pearson r |
|---|---|---|
| `returns` | `percentage_change` | +1.0000 |
| `body_percentage` | `body_to_range_ratio` | +1.0000 |
| `bullish_flag` | `bearish_flag` | -1.0000 |
| `active_swing_high_price` | `resistance_price` | +1.0000 |
| `active_swing_low_price` | `support_price` | +1.0000 |
| `returns` | `log_returns` | +1.0000 |
| `log_returns` | `percentage_change` | +1.0000 |
| `fib_level_382` | `fib_level_500` | +0.9999 |
| `fib_level_500` | `fib_level_618` | +0.9999 |
| `sma_20` | `ema_21` | +0.9999 |
| `fib_level_236` | `fib_level_382` | +0.9999 |
| `fib_level_618` | `fib_level_786` | +0.9999 |

---

## 5. Performance by Market Regime (Conditional Distribution)

Target distribution partitioned by structural trend direction:

| Market Regime (`trend_direction`) | Total Samples | % UP | % DOWN | % NEUTRAL |
|---|---|---|---|---|
| **Uptrend (+1)** | 860 | 44.30% | 55.47% | 0.23% |
| **Downtrend (-1)** | 609 | 40.89% | 58.78% | 0.33% |
| **Sideways (0)** | 11 | 54.55% | 45.45% | 0.00% |