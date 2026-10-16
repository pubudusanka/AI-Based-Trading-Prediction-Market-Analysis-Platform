# Backtest Performance Report: RandomForest

**Asset:** BTC/USDT (15m)  
**Initial Capital:** $10,000.00  
**Final Equity:** $9,540.61 (**-4.59%**)  
**Annualized Return (CAGR):** -98.38%  
**Generated At:** 2026-10-16T18:26:17.043344+00:00  

---

## 1. Execution & Friction Assumptions

| Parameter | Configuration | Notes |
|---|---|---|
| **Execution Timing** | Candle `T+1` Open | Signal generated on close of `T` |
| **Exchange Trading Fee** | 0.10% | Deducted on both entry and exit |
| **Execution Slippage** | 0.05% | Applied adversely on entry & exits |
| **Take Profit Target** | +1.0% | Upper triple-barrier |
| **Stop Loss Target** | -0.5% | Lower triple-barrier |
| **Horizon Limit** | 20 candles | Time-exit barrier |
| **Same-Candle Tie-Breaker** | Conservative (SL first) | Avoids optimistic execution bias |

---

## 2. Key Performance Indicators

| Return & Risk Metric | Value | Trade Activity Metric | Value |
|---|---|---|---|
| **Total Net Profit** | $-459.39 | **Total Completed Trades** | 87 |
| **Profit Factor** | 0.55 | **Win Rate** | 35.6% (31 wins) |
| **Sharpe Ratio** | -24.62 | **Loss Rate** | 64.4% (56 losses) |
| **Sortino Ratio** | -12.55 | **Win / Loss Ratio** | 1.00 |
| **Calmar Ratio** | -20.62 | **Average Win** | $18.19 |
| **Maximum Drawdown** | **4.77%** ($477.21) | **Average Loss** | $18.28 |
| **Max DD Duration** | 399 candles | **Expectancy per Trade** | $-5.28 |
| **Market Exposure** | 23.0% | **Avg Holding Period** | 1.1 candles |
| **Portfolio Turnover** | 21.2x | **Max Consec. Wins / Losses** | 5 / 8 |
| **Total Fees Paid** | $423.95 | **Total Slippage Cost** | $211.90 |

---

## 3. Recent Trade Execution Log

| ID | Signal Time | Entry Price | Exit Time | Exit Price | Reason | Net P&L | Return |
|---|---|---|---|---|---|---|---|
| 73 | 2026-01-12 23:30:00+00:00 | $98,057.41 | 2026-01-12 23:45:00+00:00 | $97,518.34 | `STOP_LOSS` | $-18.17 | -0.75% |
| 74 | 2026-01-12 23:45:00+00:00 | $96,619.38 | 2026-01-13 00:00:00+00:00 | $96,088.22 | `STOP_LOSS` | $-18.14 | -0.75% |
| 75 | 2026-01-13 00:00:00+00:00 | $96,217.06 | 2026-01-13 00:15:00+00:00 | $95,688.10 | `STOP_LOSS` | $-18.11 | -0.75% |
| 76 | 2026-01-13 00:15:00+00:00 | $95,358.65 | 2026-01-13 00:30:00+00:00 | $96,264.08 | `TAKE_PROFIT` | +$18.06 | +0.75% |
| 77 | 2026-01-13 00:30:00+00:00 | $96,489.97 | 2026-01-13 01:00:00+00:00 | $95,959.52 | `STOP_LOSS` | $-18.11 | -0.75% |
| 78 | 2026-01-13 01:15:00+00:00 | $98,332.82 | 2026-01-13 02:00:00+00:00 | $97,792.23 | `STOP_LOSS` | $-18.07 | -0.75% |
| 79 | 2026-01-13 04:30:00+00:00 | $102,255.60 | 2026-01-13 04:45:00+00:00 | $101,693.45 | `STOP_LOSS` | $-18.04 | -0.75% |
| 80 | 2026-01-13 05:00:00+00:00 | $102,593.37 | 2026-01-13 05:30:00+00:00 | $102,029.36 | `STOP_LOSS` | $-18.00 | -0.75% |
| 81 | 2026-01-13 06:00:00+00:00 | $100,729.83 | 2026-01-13 06:30:00+00:00 | $100,176.07 | `STOP_LOSS` | $-17.97 | -0.75% |
| 82 | 2026-01-13 06:30:00+00:00 | $100,026.33 | 2026-01-13 06:45:00+00:00 | $99,476.44 | `STOP_LOSS` | $-17.94 | -0.75% |
| 83 | 2026-01-13 06:45:00+00:00 | $99,286.37 | 2026-01-13 07:00:00+00:00 | $98,740.55 | `STOP_LOSS` | $-17.90 | -0.75% |
| 84 | 2026-01-13 07:15:00+00:00 | $100,445.13 | 2026-01-13 07:30:00+00:00 | $101,398.86 | `TAKE_PROFIT` | +$17.85 | +0.75% |
| 85 | 2026-01-13 09:45:00+00:00 | $98,270.70 | 2026-01-13 10:00:00+00:00 | $97,730.45 | `STOP_LOSS` | $-17.90 | -0.75% |
| 86 | 2026-01-13 10:00:00+00:00 | $97,887.25 | 2026-01-13 10:15:00+00:00 | $97,349.11 | `STOP_LOSS` | $-17.87 | -0.75% |
| 87 | 2026-01-13 10:30:00+00:00 | $97,076.94 | 2026-01-13 11:15:00+00:00 | $97,998.68 | `TAKE_PROFIT` | +$17.82 | +0.75% |
