"""
Event-Driven Realistic Backtesting Engine.
Reference: Section 25 (Phase 20) & Section 26 (Phase 21) of Implementation Plan.

Guarantees:
- Zero Lookahead: Signals generated at candle T close execute at candle T+1 Open.
- Realistic Execution Frictions:
  * Percentage Slippage on Market Entries and Barrier Exits.
  * Exchange Transaction Fees (Maker/Taker) accounted on every order.
- Conservative Intra-Candle Barrier Resolution:
  * If both TP and SL are touched within the same candle, SL executes first.
- Strict Position Sizing:
  * Supports FixedQuantity, PercentCapital, RiskBased, and HalfKelly sizers.
- Complete Metric Breakdown:
  * Sharpe, Sortino, Calmar, Max Drawdown, Win Rate, Profit Factor, Exposure, Turnover.
- Auditable Trade Log & Equity Curve.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
import os
from typing import Dict, Any, List, Optional, Tuple, Union, cast
import numpy as np
import pandas as pd

from src.backtesting.trade import Trade
from src.backtesting.sizing import PositionSizer, PercentCapitalSizer
from src.backtesting.metrics import BacktestMetrics, MetricsCalculator


@dataclass
class BacktestResult:
    """Complete results from a backtest execution."""
    symbol: str
    timeframe: str
    model_name: str
    metrics: BacktestMetrics
    trades: List[Trade]
    equity_curve: pd.DataFrame
    config: Dict[str, Any]
    generated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def trades_to_dataframe(self) -> pd.DataFrame:
        """Converts list of trades to a structured pandas DataFrame."""
        if not self.trades:
            return pd.DataFrame()
        return pd.DataFrame([t.to_dict() for t in self.trades])

    def to_markdown(self) -> str:
        """Renders comprehensive Markdown report for backtest documentation."""
        m = self.metrics
        c = self.config

        md = [
            f"# Backtest Performance Report: {self.model_name}",
            "",
            f"**Asset:** {self.symbol} ({self.timeframe})  ",
            f"**Initial Capital:** ${m.initial_capital:,.2f}  ",
            f"**Final Equity:** ${m.final_equity:,.2f} (**{m.total_return_pct:+.2f}%**)  ",
            f"**Annualized Return (CAGR):** {m.annualized_return_pct:+.2f}%  ",
            f"**Generated At:** {self.generated_at}  ",
            "",
            "---",
            "",
            "## 1. Execution & Friction Assumptions",
            "",
            "| Parameter | Configuration | Notes |",
            "|---|---|---|",
            f"| **Execution Timing** | Candle `T+1` Open | Signal generated on close of `T` |",
            f"| **Exchange Trading Fee** | {c.get('fee_pct', 0.001)*100:.2f}% | Deducted on both entry and exit |",
            f"| **Execution Slippage** | {c.get('slippage_pct', 0.0005)*100:.2f}% | Applied adversely on entry & exits |",
            f"| **Take Profit Target** | +{c.get('take_profit_pct', 0.01)*100:.1f}% | Upper triple-barrier |",
            f"| **Stop Loss Target** | -{c.get('stop_loss_pct', 0.005)*100:.1f}% | Lower triple-barrier |",
            f"| **Horizon Limit** | {c.get('max_holding_candles', 20)} candles | Time-exit barrier |",
            f"| **Same-Candle Tie-Breaker** | Conservative (SL first) | Avoids optimistic execution bias |",
            "",
            "---",
            "",
            "## 2. Key Performance Indicators",
            "",
            "| Return & Risk Metric | Value | Trade Activity Metric | Value |",
            "|---|---|---|---|",
            f"| **Total Net Profit** | ${m.net_profit:+,.2f} | **Total Completed Trades** | {m.total_trades} |",
            f"| **Profit Factor** | {m.profit_factor:.2f} | **Win Rate** | {m.win_rate_pct:.1f}% ({m.winning_trades} wins) |",
            f"| **Sharpe Ratio** | {m.sharpe_ratio:.2f} | **Loss Rate** | {m.loss_rate_pct:.1f}% ({m.losing_trades} losses) |",
            f"| **Sortino Ratio** | {m.sortino_ratio:.2f} | **Win / Loss Ratio** | {m.win_loss_ratio:.2f} |",
            f"| **Calmar Ratio** | {m.calmar_ratio:.2f} | **Average Win** | ${m.average_win:.2f} |",
            f"| **Maximum Drawdown** | **{m.max_drawdown_pct:.2f}%** (${m.max_drawdown_value:,.2f}) | **Average Loss** | ${m.average_loss:.2f} |",
            f"| **Max DD Duration** | {m.max_drawdown_duration_candles} candles | **Expectancy per Trade** | ${m.expectancy_per_trade:+.2f} |",
            f"| **Market Exposure** | {m.market_exposure_pct:.1f}% | **Avg Holding Period** | {m.average_holding_period_candles} candles |",
            f"| **Portfolio Turnover** | {m.portfolio_turnover:.1f}x | **Max Consec. Wins / Losses** | {m.max_consecutive_wins} / {m.max_consecutive_losses} |",
            f"| **Total Fees Paid** | ${m.total_fees_paid:,.2f} | **Total Slippage Cost** | ${m.total_slippage_cost:,.2f} |",
            "",
            "---",
            "",
            "## 3. Recent Trade Execution Log",
            "",
            "| ID | Signal Time | Entry Price | Exit Time | Exit Price | Reason | Net P&L | Return |",
            "|---|---|---|---|---|---|---|---|",
        ]

        # Include up to 15 most recent trades
        display_trades = self.trades[-15:] if len(self.trades) > 15 else self.trades
        for t in display_trades:
            sign = "+" if t.net_pnl > 0 else ""
            md.append(
                f"| {t.trade_id} | {t.signal_time} | ${t.entry_price:,.2f} | "
                f"{t.exit_time} | ${t.exit_price:,.2f} | `{t.exit_reason}` | "
                f"{sign}${t.net_pnl:.2f} | {t.net_return_pct:+.2f}% |"
            )

        return "\n".join(md)

    def save_report(self, filepath: str) -> str:
        """Persists markdown report to disk."""
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(self.to_markdown() + "\n")
        return filepath


class BacktestEngine:
    """
    Simulates historical trading execution with zero lookahead bias and realistic frictions.
    """

    def __init__(
        self,
        initial_capital: float = 10_000.0,
        sizer: Optional[PositionSizer] = None,
        fee_pct: float = 0.001,             # 0.10% Binance Spot standard taker fee
        slippage_pct: float = 0.0005,       # 0.05% slippage on market orders
        take_profit_pct: float = 0.01,      # +1.0%
        stop_loss_pct: float = 0.005,       # -0.5%
        max_holding_candles: int = 20,      # 5 hours (20 x 15m)
        min_confidence: float = 0.45,       # minimum UP probability required to enter
    ):
        self.initial_capital = initial_capital
        self.sizer = sizer or PercentCapitalSizer(capital_pct=0.20)
        self.fee_pct = fee_pct
        self.slippage_pct = slippage_pct
        self.take_profit_pct = take_profit_pct
        self.stop_loss_pct = stop_loss_pct
        self.max_holding_candles = max_holding_candles
        self.min_confidence = min_confidence

    def run(
        self,
        df: pd.DataFrame,
        model: Any,
        symbol: str = "BTC/USDT",
        timeframe: str = "15m",
    ) -> BacktestResult:
        """
        Runs candle-by-candle event-driven backtest simulation across DataFrame.
        """
        required_cols = {"open", "high", "low", "close"}
        missing = required_cols - set(df.columns)
        if missing:
            raise ValueError(f"DataFrame missing required OHLC columns: {missing}")

        n_candles = len(df)
        if n_candles < 2:
            raise ValueError(f"DataFrame must contain at least 2 candles for backtesting, got {n_candles}")

        model_name = getattr(model, "name", type(model).__name__)

        # Precompute model prediction probabilities
        prob_df = model.predict_proba(df)

        cash = self.initial_capital
        position_qty = 0.0
        active_trade: Optional[Dict[str, Any]] = None
        completed_trades: List[Trade] = []
        trade_id_counter = 1

        timestamps = [str(t) for t in df.index]
        opens = np.asarray(df["open"], dtype=np.float64)
        highs = np.asarray(df["high"], dtype=np.float64)
        lows = np.asarray(df["low"], dtype=np.float64)
        closes = np.asarray(df["close"], dtype=np.float64)
        up_probs = np.asarray(prob_df["UP"], dtype=np.float64)

        equity_curve_records: List[Dict[str, Any]] = []

        # Scheduled order from candle T to execute at candle T+1 open
        pending_entry: Optional[Dict[str, Any]] = None

        for i in range(n_candles):
            current_time = timestamps[i]
            c_open = opens[i]
            c_high = highs[i]
            c_low = lows[i]
            c_close = closes[i]

            # -------------------------------------------------------------
            # 1. Execute any pending market order from previous candle at OPEN of current candle
            # -------------------------------------------------------------
            if pending_entry is not None and active_trade is None:
                # Apply slippage (adverse execution: buy higher)
                raw_entry = c_open
                entry_price = raw_entry * (1.0 + self.slippage_pct)
                signal_prob = pending_entry["probability"]

                # Calculate position size
                sl_barrier = entry_price * (1.0 - self.stop_loss_pct)
                order_qty = self.sizer.calculate_order_quantity(
                    current_equity=cash,
                    current_price=entry_price,
                    stop_loss_price=sl_barrier,
                    probability=signal_prob,
                )

                position_value = order_qty * entry_price
                entry_fee = position_value * self.fee_pct

                if position_value + entry_fee <= cash and order_qty > 0:
                    cash -= (position_value + entry_fee)
                    position_qty = order_qty

                    active_trade = {
                        "trade_id": trade_id_counter,
                        "signal_time": pending_entry["signal_time"],
                        "entry_time": current_time,
                        "entry_index": i,
                        "raw_entry_price": raw_entry,
                        "entry_price": entry_price,
                        "quantity": order_qty,
                        "position_value": position_value,
                        "entry_fee": entry_fee,
                        "tp_price": entry_price * (1.0 + self.take_profit_pct),
                        "sl_price": entry_price * (1.0 - self.stop_loss_pct),
                    }
                    trade_id_counter += 1

                pending_entry = None

            # -------------------------------------------------------------
            # 2. Check Intra-Candle Barriers for active position
            # -------------------------------------------------------------
            if active_trade is not None:
                tp_price = active_trade["tp_price"]
                sl_price = active_trade["sl_price"]
                holding_duration = i - active_trade["entry_index"]

                hit_tp = c_high >= tp_price
                hit_sl = c_low <= sl_price
                exit_triggered = False
                exit_reason = ""
                raw_exit = 0.0

                # Conservative tie-breaker: if both hit in same candle, SL executes first!
                if hit_tp and hit_sl:
                    exit_triggered = True
                    exit_reason = "STOP_LOSS"
                    raw_exit = sl_price
                elif hit_sl:
                    exit_triggered = True
                    exit_reason = "STOP_LOSS"
                    raw_exit = sl_price
                elif hit_tp:
                    exit_triggered = True
                    exit_reason = "TAKE_PROFIT"
                    raw_exit = tp_price
                elif holding_duration >= self.max_holding_candles:
                    # Time limit horizon reached -> exit at candle Close
                    exit_triggered = True
                    exit_reason = "TIME_LIMIT"
                    raw_exit = c_close
                elif i == n_candles - 1:
                    # Final candle of backtest dataset -> close at final Close
                    exit_triggered = True
                    exit_reason = "END_OF_DATA"
                    raw_exit = c_close

                if exit_triggered:
                    # Apply slippage on exit (adverse execution: sell lower)
                    exit_price = raw_exit * (1.0 - self.slippage_pct)
                    gross_exit_val = position_qty * exit_price
                    exit_fee = gross_exit_val * self.fee_pct
                    total_fees = active_trade["entry_fee"] + exit_fee

                    gross_pnl = gross_exit_val - active_trade["position_value"]
                    net_pnl = gross_pnl - total_fees
                    gross_ret = (gross_pnl / active_trade["position_value"]) * 100.0
                    net_ret = (net_pnl / active_trade["position_value"]) * 100.0

                    slippage_cost = (
                        (active_trade["entry_price"] - active_trade["raw_entry_price"]) * position_qty
                        + (raw_exit - exit_price) * position_qty
                    )

                    cash += (gross_exit_val - exit_fee)

                    completed_trades.append(
                        Trade(
                            trade_id=active_trade["trade_id"],
                            symbol=symbol,
                            timeframe=timeframe,
                            side="LONG",
                            signal_time=active_trade["signal_time"],
                            entry_time=active_trade["entry_time"],
                            entry_price=float(round(active_trade["entry_price"], 4)),
                            raw_entry_price=float(round(active_trade["raw_entry_price"], 4)),
                            exit_time=current_time,
                            exit_price=float(round(exit_price, 4)),
                            raw_exit_price=float(round(raw_exit, 4)),
                            quantity=float(round(position_qty, 6)),
                            position_value=float(round(active_trade["position_value"], 2)),
                            exit_reason=exit_reason,
                            gross_pnl=float(round(gross_pnl, 2)),
                            gross_return_pct=float(round(gross_ret, 2)),
                            entry_fee=float(round(active_trade["entry_fee"], 2)),
                            exit_fee=float(round(exit_fee, 2)),
                            total_fees=float(round(total_fees, 2)),
                            slippage_cost=float(round(slippage_cost, 2)),
                            net_pnl=float(round(net_pnl, 2)),
                            net_return_pct=float(round(net_ret, 2)),
                            holding_candles=max(1, holding_duration),
                            is_winner=bool(net_pnl > 0),
                        )
                    )

                    position_qty = 0.0
                    active_trade = None

            # -------------------------------------------------------------
            # 3. Model generates signal at CLOSE of candle T (for T+1 entry)
            # -------------------------------------------------------------
            if active_trade is None and pending_entry is None and i < n_candles - 1:
                p_up = up_probs[i]
                if p_up >= self.min_confidence:
                    pending_entry = {
                        "signal_time": current_time,
                        "probability": p_up,
                    }

            # -------------------------------------------------------------
            # 4. Mark-to-market Equity Tracking
            # -------------------------------------------------------------
            current_pos_val = position_qty * c_close
            current_equity = cash + current_pos_val
            equity_curve_records.append({
                "timestamp": current_time,
                "cash": round(cash, 2),
                "position_value": round(current_pos_val, 2),
                "equity": round(current_equity, 2),
            })

        # Calculate metrics
        equity_df = pd.DataFrame(equity_curve_records).set_index("timestamp")
        equity_series = pd.Series(cast(Any, equity_df["equity"]))

        metrics = MetricsCalculator.compute(
            trades=completed_trades,
            equity_series=equity_series,
            initial_capital=self.initial_capital,
            timeframe=timeframe,
        )

        config_dict = {
            "fee_pct": self.fee_pct,
            "slippage_pct": self.slippage_pct,
            "take_profit_pct": self.take_profit_pct,
            "stop_loss_pct": self.stop_loss_pct,
            "max_holding_candles": self.max_holding_candles,
            "min_confidence": self.min_confidence,
            "sizer": type(self.sizer).__name__,
        }

        return BacktestResult(
            symbol=symbol,
            timeframe=timeframe,
            model_name=model_name,
            metrics=metrics,
            trades=completed_trades,
            equity_curve=equity_df,
            config=config_dict,
        )
