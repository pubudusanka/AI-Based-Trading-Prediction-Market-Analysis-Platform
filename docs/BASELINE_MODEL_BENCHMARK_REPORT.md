# Baseline Model Benchmark Leaderboard: BTC/USDT (15m)

**Evaluation Split:** Validation  
**Total Evaluated Samples:** 232  
**Generated At:** 2026-10-16T17:28:28.849328+00:00  

---

## 1. Model Comparison Leaderboard

| Rank | Model Name | Balanced Acc | Macro F1 | ROC-AUC | PR-AUC | Log Loss | Win Rate | Trades |
|---|---|---|---|---|---|---|---|---|
| 1 | **RandomForest** | 51.62% | 0.2707 | N/A | 0.3106 | 1.3609 | 47.84% | 232 |
| 2 | **LogisticRegression** | 43.44% | 0.2396 | N/A | 0.3219 | 1.8049 | 40.52% | 232 |
| 3 | **XGBoost** | 48.80% | 0.2174 | N/A | 0.2768 | 1.7966 | 44.40% | 232 |
| 4 | **RuleBasedBaseline** | 0.00% | 0.0000 | N/A | 0.3333 | 1.8971 | 0.00% | 0 |

---

## 2. Detailed Per-Class Breakdown

| Model Name | Class | Precision | Recall | F1-Score | Support |
|---|---|---|---|---|---|
| RandomForest | **DOWN** | 46.15% | 91.43% | 0.6134 | - |
| RandomForest | **NEUTRAL** | 0.00% | 0.00% | 0.0000 | - |
| RandomForest | **UP** | 62.50% | 11.81% | 0.1987 | - |
| LogisticRegression | **DOWN** | 41.27% | 74.29% | 0.5306 | - |
| LogisticRegression | **NEUTRAL** | 0.00% | 0.00% | 0.0000 | - |
| LogisticRegression | **UP** | 37.21% | 12.60% | 0.1882 | - |
| XGBoost | **DOWN** | 44.64% | 95.24% | 0.6079 | - |
| XGBoost | **NEUTRAL** | 0.00% | 0.00% | 0.0000 | - |
| XGBoost | **UP** | 37.50% | 2.36% | 0.0444 | - |
| RuleBasedBaseline | **DOWN** | 0.00% | 0.00% | 0.0000 | - |
| RuleBasedBaseline | **NEUTRAL** | 0.00% | 0.00% | 0.0000 | - |
| RuleBasedBaseline | **UP** | 0.00% | 0.00% | 0.0000 | - |