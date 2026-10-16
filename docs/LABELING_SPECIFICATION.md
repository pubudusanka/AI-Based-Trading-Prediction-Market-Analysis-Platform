# Target / Label Generation Specification (v1.0.0)

**Reference:** Section 16 (Phase 11) of Implementation Plan  
**Target Asset:** BTC/USDT (Binance Spot)  
**Timeframe:** 15m  

---

## 1. Mathematical Formulation

Given market information available at candle $T$, the machine learning task is formulated as a fixed-horizon triple-barrier classification problem:

$$\text{Entry Price} = C_T \quad (\text{Close at } T)$$

Over the forward prediction horizon:

$$\mathcal{H} = [T+1, T+N], \quad N = 20 \text{ candles } (5 \text{ hours})$$

Two spatial barrier prices are defined:
- **Upper Barrier (Take Profit):** $P_{\text{TP}} = C_T \times (1.0 + \tau_{\text{TP}})$, where $\tau_{\text{TP}} = +1.0\% = 0.010$
- **Lower Barrier (Stop Loss):** $P_{\text{SL}} = C_T \times (1.0 - \tau_{\text{SL}})$, where $\tau_{\text{SL}} = -0.5\% = 0.005$

---

## 2. Triple-Barrier Classification Logic

For each future step $t \in [T+1, T+N]$:
1. $t_{\text{TP}} = \min \{ t \mid H_t \ge P_{\text{TP}} \}$
2. $t_{\text{SL}} = \min \{ t \mid L_t \le P_{\text{SL}} \}$

The ground-truth label $Y_T$ is assigned as:

$$
Y_T = \begin{cases}
+1 \text{ ("UP")}, & \text{if } t_{\text{TP}} \text{ is finite and } (t_{\text{SL}} \text{ is None or } t_{\text{TP}} < t_{\text{SL}}) \\
-1 \text{ ("DOWN")}, & \text{if } t_{\text{SL}} \text{ is finite and } (t_{\text{TP}} \text{ is None or } t_{\text{SL}} < t_{\text{TP}}) \\
0 \text{ ("NEUTRAL")}, & \text{if both } t_{\text{TP}} \text{ and } t_{\text{SL}} \text{ are None (neither hit within } N \text{ candles)}
\end{cases}
$$

---

## 3. Intra-Candle Ambiguity Resolution

### The Edge Case
If both $H_t \ge P_{\text{TP}}$ and $L_t \le P_{\text{SL}}$ occur within the **exact same candle** $t$, standard OHLC data cannot unambiguously determine whether high or low was visited first.

### Conservative Policy (`conservative_stop`)
In live execution, risk management prioritizes capital preservation:
- A trader cannot guarantee that take-profit was touched before stop-loss in a volatile bar.
- Therefore, the platform applies a **conservative worst-case policy**:
  $$\text{If } t_{\text{TP}} = t_{\text{SL}} = t \implies Y_T = -1 \text{ ("DOWN / STOPPED OUT")}$$
- This prevents overly optimistic backtesting or inflated win rates.

---

## 4. Auxiliary Targets & Excursion Metrics

In addition to the primary 3-class triple barrier label, the engine computes:

| Target Name | Type | Definition | Purpose |
|---|---|---|---|
| `target_triple_barrier` | `int` | $+1$ (`UP`), $-1$ (`DOWN`), $0$ (`NEUTRAL`) | Primary ML classification label |
| `target_label_name` | `str` | `"UP"`, `"DOWN"`, `"NEUTRAL"`, `"UNLABELLED"` | Human-readable tag |
| `target_binary` | `int` | $1$ if $C_{T+20} > C_T$ else $0$ | Binary directional baseline |
| `future_return_5` | `float` | $(C_{T+5} - C_T) / C_T$ | 1.25-hour forward return |
| `future_return_10` | `float` | $(C_{T+10} - C_T) / C_T$ | 2.5-hour forward return |
| `future_return_20` | `float` | $(C_{T+20} - C_T) / C_T$ | 5.0-hour forward return |
| `max_future_return` | `float` | $(\max_{t \in [T+1, T+N]} H_t - C_T) / C_T$ | Maximum Favorable Excursion (MFE) |
| `min_future_return` | `float` | $(\min_{t \in [T+1, T+N]} L_t - C_T) / C_T$ | Maximum Adverse Excursion (MAE) |
| `candles_to_target` | `float` | Index offset to TP breach ($1 \dots 20$) | Speed of profit attainment |
| `candles_to_stop` | `float` | Index offset to SL breach ($1 \dots 20$) | Speed of stop trigger |
| `is_target_valid` | `bool` | True if full $N$-bar future window exists | Prevents lookahead/incomplete horizon bias |

---

## 5. Incomplete Horizon Boundary Rules

For the most recent $N$ candles in any dataset (the "tail" $T_{\text{end}} - N + 1 \dots T_{\text{end}}$):
- The full 20-candle future window has not yet occurred.
- Labeling these candles with truncated horizons would introduce **severe survivorship and incomplete-horizon leakage**.
- **Rule:** All tail candles strictly set `is_target_valid = False`, `target_label_name = "UNLABELLED"`, and `target_triple_barrier = NaN`.
