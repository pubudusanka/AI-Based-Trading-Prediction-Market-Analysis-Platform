# Feature Catalog (v1.0.0)

**Document Version:** 1.0  
**Reference:** Implementation Plan Section 11 (Phase 6)  
**Guaranteed Invariant:** Zero future information leakage. All features at candle index $T$ use only data $\le T$.  

## Summary Table

| Feature Name | Group | Formula / Definition | Window | Inputs | Output Type | Missing Value Handling | Leakage Risk |
|---|---|---|---|---|---|---|---|
| `returns` | Price | `(C_t - C_{t-1}) / C_{t-1}` | 1 | close | `float` | NaN for first row | Zero: strictly backwards-looking (<= T) |
| `log_returns` | Price | `ln(C_t / C_{t-1})` | 1 | close | `float` | NaN for first row | Zero: strictly backwards-looking (<= T) |
| `percentage_change` | Price | `returns * 100` | 1 | close | `float` | NaN for first row | Zero: strictly backwards-looking (<= T) |
| `body_size` | Candle | `|C_t - O_t|` | 1 | open, close | `float` | Always valid | Zero: strictly backwards-looking (<= T) |
| `body_percentage` | Candle | `body_size / (H_t - L_t)` | 1 | open, high, low, close | `float` | 0.0 if H == L | Zero: strictly backwards-looking (<= T) |
| `upper_wick` | Candle | `H_t - max(O_t, C_t)` | 1 | open, high, close | `float` | Always valid | Zero: strictly backwards-looking (<= T) |
| `lower_wick` | Candle | `min(O_t, C_t) - L_t` | 1 | open, low, close | `float` | Always valid | Zero: strictly backwards-looking (<= T) |
| `candle_range` | Candle | `H_t - L_t` | 1 | high, low | `float` | Always valid | Zero: strictly backwards-looking (<= T) |
| `body_to_range_ratio` | Candle | `body_size / candle_range` | 1 | open, high, low, close | `float` | 0.0 if range == 0 | Zero: strictly backwards-looking (<= T) |
| `bullish_flag` | Candle | `1 if C_t > O_t else 0` | 1 | open, close | `int` | Binary indicator | Zero: strictly backwards-looking (<= T) |
| `bearish_flag` | Candle | `1 if C_t < O_t else 0` | 1 | open, close | `int` | Binary indicator | Zero: strictly backwards-looking (<= T) |
| `sma_20` | Moving Average | `SMA(close, 20)` | 20 | close | `float` | NaN for t < 20 | Zero: strictly backwards-looking (<= T) |
| `sma_50` | Moving Average | `SMA(close, 50)` | 50 | close | `float` | NaN for t < 50 | Zero: strictly backwards-looking (<= T) |
| `sma_200` | Moving Average | `SMA(close, 200)` | 200 | close | `float` | NaN for t < 200 | Zero: strictly backwards-looking (<= T) |
| `ema_9` | Moving Average | `EMA(close, 9)` | 9 | close | `float` | Standard exponential smoothing | Zero: strictly backwards-looking (<= T) |
| `ema_21` | Moving Average | `EMA(close, 21)` | 21 | close | `float` | Standard exponential smoothing | Zero: strictly backwards-looking (<= T) |
| `ema_50` | Moving Average | `EMA(close, 50)` | 50 | close | `float` | Standard exponential smoothing | Zero: strictly backwards-looking (<= T) |
| `ema_200` | Moving Average | `EMA(close, 200)` | 200 | close | `float` | Standard exponential smoothing | Zero: strictly backwards-looking (<= T) |
| `rsi_14` | Momentum | `RSI(close, 14) via Wilder smoothing` | 14 | close | `float` | NaN for t < 14 | Zero: strictly backwards-looking (<= T) |
| `macd` | Momentum | `EMA_12 - EMA_26` | 26 | close | `float` | NaN for t < 26 | Zero: strictly backwards-looking (<= T) |
| `macd_signal` | Momentum | `EMA_9(MACD)` | 34 | close | `float` | NaN for t < 34 | Zero: strictly backwards-looking (<= T) |
| `macd_hist` | Momentum | `MACD - MACD_signal` | 34 | close | `float` | NaN for t < 34 | Zero: strictly backwards-looking (<= T) |
| `stoch_k` | Momentum | `((C - L_14) / (H_14 - L_14)) * 100` | 14 | high, low, close | `float` | NaN for t < 14 | Zero: strictly backwards-looking (<= T) |
| `stoch_d` | Momentum | `SMA_3(stoch_k)` | 16 | high, low, close | `float` | NaN for t < 16 | Zero: strictly backwards-looking (<= T) |
| `roc_10` | Momentum | `((C_t - C_{t-10}) / C_{t-10}) * 100` | 10 | close | `float` | NaN for t < 10 | Zero: strictly backwards-looking (<= T) |
| `atr_14` | Volatility | `Wilder average of True Range` | 14 | high, low, close | `float` | NaN for t < 14 | Zero: strictly backwards-looking (<= T) |
| `bb_width_20` | Volatility | `(BB_upper - BB_lower) / BB_mid` | 20 | close | `float` | NaN for t < 20 | Zero: strictly backwards-looking (<= T) |
| `rolling_std_20` | Volatility | `Rolling 20-period standard deviation of returns` | 20 | close | `float` | NaN for t < 20 | Zero: strictly backwards-looking (<= T) |
| `adx_14` | Trend | `Average Directional Index (14 periods)` | 28 | high, low, close | `float` | NaN for t < 28 | Zero: strictly backwards-looking (<= T) |
| `ema_slope_21` | Trend | `(EMA_21_t - EMA_21_{t-5}) / EMA_21_{t-5}` | 26 | close | `float` | NaN for t < 26 | Zero: strictly backwards-looking (<= T) |
| `price_vs_ema_21` | Trend | `(C_t - EMA_21) / EMA_21` | 21 | close | `float` | Normalized distance | Zero: strictly backwards-looking (<= T) |
| `price_vs_ema_50` | Trend | `(C_t - EMA_50) / EMA_50` | 50 | close | `float` | Normalized distance | Zero: strictly backwards-looking (<= T) |
| `price_vs_ema_200` | Trend | `(C_t - EMA_200) / EMA_200` | 200 | close | `float` | Normalized distance | Zero: strictly backwards-looking (<= T) |
| `ma_cross_20_50` | Trend | `1 if SMA_20 > SMA_50 else 0` | 50 | close | `int` | State indicator | Zero: strictly backwards-looking (<= T) |
| `ma_cross_50_200` | Trend | `1 if SMA_50 > SMA_200 else 0` | 200 | close | `int` | Golden cross regime | Zero: strictly backwards-looking (<= T) |
| `volume_ma_20` | Volume | `SMA(volume, 20)` | 20 | volume | `float` | NaN for t < 20 | Zero: strictly backwards-looking (<= T) |
| `volume_ratio_20` | Volume | `volume / volume_ma_20` | 20 | volume | `float` | 1.0 default if 0 | Zero: strictly backwards-looking (<= T) |
| `volume_change` | Volume | `(V_t - V_{t-1}) / V_{t-1}` | 1 | volume | `float` | NaN for first row | Zero: strictly backwards-looking (<= T) |
| `obv` | Volume | `Cumulative On-Balance Volume` | 1 | close, volume | `float` | Continuous cumulative | Zero: strictly backwards-looking (<= T) |

## Market Structure Features (Phase 8)

| Feature Name | Group | Formula / Definition | Lookback / Confirmation | Inputs | Output Type | Leakage Prevention Invariant |
|---|---|---|---|---|---|---|
| `is_swing_high` | Structure | 1 if peak confirmed at candle $t$ (which occurred at $t - K$) | $K$ confirmation bars | high | `int` | Confirmed strictly at $t \ge t_{\text{peak}} + K$ |
| `is_swing_low` | Structure | 1 if trough confirmed at candle $t$ (which occurred at $t - K$) | $K$ confirmation bars | low | `int` | Confirmed strictly at $t \ge t_{\text{trough}} + K$ |
| `active_swing_high_price` | Structure | Price level of most recent confirmed swing high | Dynamic | high | `float` | Level known at or before current candle $t$ |
| `active_swing_low_price` | Structure | Price level of most recent confirmed swing low | Dynamic | low | `float` | Level known at or before current candle $t$ |
| `is_higher_high` | Structure | 1 if newly confirmed swing high > prior confirmed swing high | $2 \times \text{swings}$ | high | `int` | Evaluated strictly on confirmed peaks |
| `is_lower_high` | Structure | 1 if newly confirmed swing high < prior confirmed swing high | $2 \times \text{swings}$ | high | `int` | Evaluated strictly on confirmed peaks |
| `is_higher_low` | Structure | 1 if newly confirmed swing low > prior confirmed swing low | $2 \times \text{swings}$ | low | `int` | Evaluated strictly on confirmed troughs |
| `is_lower_low` | Structure | 1 if newly confirmed swing low < prior confirmed swing low | $2 \times \text{swings}$ | low | `int` | Evaluated strictly on confirmed troughs |
| `trend_direction` | Structure | +1 for Uptrend (HH/HL), -1 for Downtrend (LH/LL), 0 Sideways | Dynamic | high, low | `int` | State changes only when swing confirmed |
| `support_price` | Support/Res | Current active support level (most recent confirmed swing low) | Dynamic | low | `float` | Only confirmed levels used |
| `resistance_price` | Support/Res | Current active resistance level (most recent confirmed swing high) | Dynamic | high | `float` | Only confirmed levels used |
| `dist_to_support` | Support/Res | `(close - support_price) / close` | Dynamic | close, low | `float` | Normalized distance |
| `dist_to_resistance` | Support/Res | `(resistance_price - close) / close` | Dynamic | close, high | `float` | Normalized distance |
| `is_breakout_high` | Breakout | 1 if candle close > previous candle's active resistance | 1 | close, high | `int` | Compared against prior candle's resistance |
| `is_breakout_low` | Breakout | 1 if candle close < previous candle's active support | 1 | close, low | `int` | Compared against prior candle's support |
| `is_break_of_structure` | Structure | +1 for Bullish BOS, -1 for Bearish BOS, 0 otherwise | 1 | close, high, low | `int` | Causal break of structure detection |
| `is_retest_support` | Retest | 1 if price pulls back to broken resistance ($\pm 0.3\%$) and holds | $\le 10$ bars | close, low | `int` | Post-breakout causal tracking |
| `is_retest_resistance` | Retest | 1 if price rallies to broken support ($\pm 0.3\%$) and rejects | $\le 10$ bars | close, high | `int` | Post-breakdown causal tracking |

## Fibonacci Retracement Features (Phase 9)

| Feature Name | Group | Formula / Definition | Lookback / Anchor | Inputs | Output Type | Leakage Prevention Invariant |
|---|---|---|---|---|---|---|
| `fib_level_236` | Fibonacci | Retracement level at $0.236$ ratio | Active confirmed swings | high, low | `float` | Dynamically anchored to past swings |
| `fib_level_382` | Fibonacci | Retracement level at $0.382$ ratio | Active confirmed swings | high, low | `float` | Dynamically anchored to past swings |
| `fib_level_500` | Fibonacci | Midpoint equilibrium level at $0.500$ ratio | Active confirmed swings | high, low | `float` | Dynamically anchored to past swings |
| `fib_level_618` | Fibonacci | Golden pocket level at $0.618$ ratio | Active confirmed swings | high, low | `float` | Dynamically anchored to past swings |
| `fib_level_786` | Fibonacci | Deep retracement level at $0.786$ ratio | Active confirmed swings | high, low | `float` | Dynamically anchored to past swings |
| `fib_level_1000` | Fibonacci | Full retracement boundary (1.000) | Active confirmed swings | high, low | `float` | Dynamically anchored to past swings |
| `distance_to_236` | Fibonacci | `(close - fib_level_236) / close` | 1 | close, fib_level_236 | `float` | Signed normalized distance |
| `distance_to_382` | Fibonacci | `(close - fib_level_382) / close` | 1 | close, fib_level_382 | `float` | Signed normalized distance |
| `distance_to_500` | Fibonacci | `(close - fib_level_500) / close` | 1 | close, fib_level_500 | `float` | Signed normalized distance |
| `distance_to_618` | Fibonacci | `(close - fib_level_618) / close` | 1 | close, fib_level_618 | `float` | Signed normalized distance |
| `distance_to_786` | Fibonacci | `(close - fib_level_786) / close` | 1 | close, fib_level_786 | `float` | Signed normalized distance |
| `near_618` | Fibonacci | 1 if `|distance_to_618| <= 0.003` (0.3%) else 0 | 1 | close, fib_level_618 | `int` | Binary golden zone proximity flag |
| `near_382` | Fibonacci | 1 if `|distance_to_382| <= 0.003` (0.3%) else 0 | 1 | close, fib_level_382 | `int` | Binary shallow retracement proximity flag |
| `fib_swing_range` | Fibonacci | `active_swing_high_price - active_swing_low_price` | Dynamic | high, low | `float` | Active structural swing span |
| `fib_impulse_direction`| Fibonacci | +1 for Low->High impulse, -1 for High->Low impulse | Dynamic | swing timestamps | `int` | Direction of originating move |
