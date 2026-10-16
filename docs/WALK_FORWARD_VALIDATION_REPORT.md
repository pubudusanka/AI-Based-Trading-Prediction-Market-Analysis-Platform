# Walk-Forward Validation Report: RandomForest

**Asset:** BTC/USDT (15m)  
**Validation Scheme:** 5-Fold Purged Walk-Forward (Expanding Window)  
**Safety Embargo (Purge Gap):** 20 candles  
**Generated At:** 2026-10-16T17:38:32.410144+00:00  

---

## 1. Aggregate Out-of-Sample Performance

- **Mean Balanced Accuracy:** 55.80% (± 4.93%)
- **Mean Macro F1:** 0.3081 (± 0.0995)
- **Mean Accuracy:** 52.02% (± 11.46%)
- **Directional Win Rate:** 52.02% (± 11.46%)
- **Total Out-of-Sample Trades:** 600

---

## 2. Per-Fold Out-of-Sample Leaderboard

| Fold | Train Window | Test Window | Test Samples | Balanced Acc | Macro F1 | Win Rate | Trades |
|---|---|---|---|---|---|---|---|
| 1 | `2026-01-01`..`2026-01-05` | `2026-01-06`..`2026-01-07` | 124 | 57.62% | 0.3535 | 53.23% | 124 |
| 2 | `2026-01-01`..`2026-01-07` | `2026-01-07`..`2026-01-08` | 124 | 59.52% | 0.3937 | 62.90% | 124 |
| 3 | `2026-01-01`..`2026-01-08` | `2026-01-09`..`2026-01-10` | 124 | 50.00% | 0.1595 | 31.45% | 124 |
| 4 | `2026-01-01`..`2026-01-10` | `2026-01-10`..`2026-01-11` | 124 | 50.00% | 0.2222 | 50.00% | 124 |
| 5 | `2026-01-01`..`2026-01-11` | `2026-01-12`..`2026-01-13` | 124 | 61.87% | 0.4114 | 62.50% | 104 |