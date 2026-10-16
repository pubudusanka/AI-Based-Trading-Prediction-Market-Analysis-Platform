# Risk Management Policy & Safeguards (Phase 27)

**Document Version:** 1.0  
**Scope:** V1 `BTC/USDT` Spot (15m Timeframe)  
**Implementation Reference:** Section 32 of Implementation Plan (`ml/src/risk/manager.py`)

---

## 1. Executive Summary

The Risk Management Module operates as an independent, non-negotiable safeguard layer positioned between signal generation, model inference, and order execution. Even if a machine learning model or rule-based strategy emits an aggressive BUY signal with high confidence, the trade **cannot execute** unless all institutional capital preservation constraints defined below are fully satisfied.

---

## 2. Core Safeguards and Mathematical Constraints

| Safeguard | Configuration Default | Trigger Condition | Consequence / Action |
| :--- | :--- | :--- | :--- |
| **Max Position Notional** | `25%` of equity | $Q \times P_{\text{entry}} > \text{Capital} \times 0.25$ | Order size $Q$ clamped to maximum allowable notional |
| **Fixed Fractional Risk** | `1%` of equity | Per-trade risk budget | $Q = \frac{\text{Capital} \times 0.01}{\|P_{\text{entry}} - P_{\text{stop}}\|}$ |
| **Risk / Reward Gating** | Minimum `1.5 : 1` | $\frac{\|P_{\text{target}} - P_{\text{entry}}\|}{\|P_{\text{entry}} - P_{\text{stop}}\|} < 1.5$ | **Trade Rejected**; avoids low-expectancy asymmetric payoff setups |
| **Volatility Noise Filter** | $0.5 \times \text{ATR}_{14}$ | $\|P_{\text{entry}} - P_{\text{stop}}\| < 0.5 \times \text{ATR}_{14}$ | **Trade Rejected**; avoids unrealistic tight stops prone to spread/noise whipsaws |
| **Max Daily Loss Limit** | `3%` of initial capital | $\text{Daily Realized Loss} \ge 3\%$ | **Daily Circuit Breaker Triggered**; all trading halted until 00:00 UTC day rollover |
| **Consecutive Loss Cooldown**| `2` straight losses | Consecutive loss count $= 2$ | **Cooldown Engaged**; trading paused for `4` consecutive 15m candles |
| **Portfolio Max Drawdown** | `10%` from peak | $\frac{\text{Peak Equity} - \text{Current Equity}}{\text{Peak Equity}} \ge 0.10$ | **Portfolio Kill Switch**; permanently halts automated execution until manual operator reset |
| **Max Open Positions** | `1` (V1 crypto spot) | $\text{Open Positions} \ge 1$ | **Trade Rejected**; prevents overlapping capital lockup |

---

## 3. Integration Architecture

```
[Candle Event / Streaming Bar]
             │
             ▼
    [PredictionService] (ML Probabilities: UP/DOWN/NEUTRAL)
             │
             ▼
      [SignalEngine]    (Technical Confluence Score: 0-100)
             │
             ▼ (Proposed Signal: Entry, Stop, Target, Confidence)
     ┌────────────────────────┐
     │      RiskManager       │
     │  - Daily Loss Check    │
     │  - Drawdown Check      │
     │  - Cooldown Check      │
     │  - R:R Gating          │
     │  - Dynamic ATR Sizing  │
     └───────────┬────────────┘
                 │
       ┌─────────┴─────────┐
       ▼                   ▼
  [Approved]          [Rejected]
  Sized & Sent to     Logged with Rejection Reason;
  Paper/Live Engine   Flat State Preserved
```

---

## 4. Verification & Audit Results

- **Unit Test Suite:** `ml/tests/test_risk_management.py` (7 tests covering sizing, R:R rejection, ATR noise filtering, daily circuit breaker, consecutive loss cooldown, max drawdown kill switch, and paper trading integration).
- **Regression Suite:** 116 tests passing across all 18 test suites in `ml/tests`.
- **Type Checking:** `pyright ml` passed with 0 errors, 0 warnings.
