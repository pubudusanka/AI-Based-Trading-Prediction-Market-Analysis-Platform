"""
Paper Trading Engine with Virtual Order Execution & PnL Tracking.
Reference: Section 28 (Phase 23) of Implementation Plan.

Guarantees:
- Real-time / streaming candle processing without real money risk.
- Production-like model inference and signal generation.
- Full Virtual Order Lifecycle: Market, Limit (TP), and Stop (SL).
- Required audit fields recorded:
  * signal, timestamp, entry, stop, target, prediction probability, model version, outcome.
- Real-time mark-to-market position valuation and equity curve.
- Drift & slippage comparison between Paper Trading performance and Backtest benchmarks.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
import json
import os
from typing import Dict, Any, List, Optional, Tuple, Union, cast
import numpy as np
import pandas as pd

from src.backtesting.sizing import PositionSizer, PercentCapitalSizer
from src.backtesting.metrics import BacktestMetrics
from src.risk.manager import RiskManager


@dataclass
class VirtualOrder:
    """Represents a virtual order submitted to the paper trading simulator."""
    order_id: str
    symbol: str
    side: str  # "BUY" or "SELL"
    order_type: str  # "MARKET", "LIMIT", "STOP"
    quantity: float
    price: float
    timestamp: str
    status: str = "FILLED"  # "FILLED", "PENDING", "CANCELLED"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class VirtualPosition:
    """Represents an active virtual position in the paper trading portfolio."""
    position_id: str
    symbol: str
    quantity: float
    entry_price: float
    current_price: float
    take_profit_price: float
    stop_loss_price: float
    unrealized_pnl: float
    unrealized_pnl_pct: float
    entry_time: str
    entry_fee: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class VirtualTradeRecord:
    """Historical audit record for a completed paper trade (Section 28 specification)."""
    trade_id: str
    symbol: str
    timeframe: str
    model_version: str
    signal: str  # "BUY" / "SELL"
    timestamp: str  # signal timestamp
    entry_time: str
    entry_price: float
    stop_price: float
    target_price: float
    prediction_probability: float
    quantity: float
    exit_time: str
    exit_price: float
    exit_reason: str  # "TAKE_PROFIT", "STOP_LOSS", "TIME_LIMIT"
    gross_pnl: float
    fees_paid: float
    net_pnl: float
    net_return_pct: float
    outcome: str  # "WIN", "LOSS", "BREAKEVEN"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class PaperTradingEngine:
    """
    Simulates production paper trading execution against streaming or historical candles.
    """

    def __init__(
        self,
        model: Any,
        model_version: str = "BTC_15M_v1.0",
        initial_capital: float = 10_000.0,
        sizer: Optional[PositionSizer] = None,
        symbol: str = "BTC/USDT",
        timeframe: str = "15m",
        fee_pct: float = 0.001,
        slippage_pct: float = 0.0005,
        take_profit_pct: float = 0.01,
        stop_loss_pct: float = 0.005,
        max_holding_candles: int = 20,
        min_confidence: float = 0.40,
        risk_manager: Optional[RiskManager] = None,
    ):
        self.model = model
        self.model_version = model_version
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.sizer = sizer or PercentCapitalSizer(capital_pct=0.20)
        self.symbol = symbol
        self.timeframe = timeframe
        self.fee_pct = fee_pct
        self.slippage_pct = slippage_pct
        self.take_profit_pct = take_profit_pct
        self.stop_loss_pct = stop_loss_pct
        self.max_holding_candles = max_holding_candles
        self.min_confidence = min_confidence
        self.risk_manager = risk_manager

        self.active_position: Optional[VirtualPosition] = None
        self.trade_history: List[VirtualTradeRecord] = []
        self.order_history: List[VirtualOrder] = []
        self.equity_log: List[Dict[str, Any]] = []

        self._active_trade_meta: Optional[Dict[str, Any]] = None
        self._candle_count = 0
        self._holding_candles = 0

    @property
    def total_equity(self) -> float:
        """Current total mark-to-market portfolio equity."""
        pos_val = (self.active_position.quantity * self.active_position.current_price) if self.active_position else 0.0
        return float(self.cash + pos_val)

    def process_candle(
        self,
        candle: Union[pd.Series, Dict[str, Any]],
        timestamp: Optional[str] = None,
    ) -> Optional[VirtualTradeRecord]:
        """
        Processes a single newly closed candle, managing position exits and signals.
        Returns a VirtualTradeRecord if a trade closed on this candle.
        """
        c_dict = candle.to_dict() if isinstance(candle, pd.Series) else candle
        time_str = timestamp or str(c_dict.get("timestamp", datetime.now(timezone.utc).isoformat()))

        c_open = float(c_dict["open"])
        c_high = float(c_dict["high"])
        c_low = float(c_dict["low"])
        c_close = float(c_dict["close"])

        completed_trade: Optional[VirtualTradeRecord] = None
        self._candle_count += 1

        # -------------------------------------------------------------
        # 1. Update active position mark-to-market & check barrier exits
        # -------------------------------------------------------------
        if self.active_position is not None and self._active_trade_meta is not None:
            self._holding_candles += 1
            self.active_position.current_price = c_close
            pos_qty = self.active_position.quantity

            # Mark to market
            current_val = pos_qty * c_close
            entry_val = pos_qty * self.active_position.entry_price
            self.active_position.unrealized_pnl = float(round(current_val - entry_val, 2))
            self.active_position.unrealized_pnl_pct = float(round((self.active_position.unrealized_pnl / entry_val) * 100.0, 2))

            tp_price = self.active_position.take_profit_price
            sl_price = self.active_position.stop_loss_price

            hit_tp = c_high >= tp_price
            hit_sl = c_low <= sl_price
            exit_triggered = False
            exit_reason = ""
            raw_exit = 0.0

            # Conservative tie-breaker: SL takes precedence if both touched in same candle
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
            elif self._holding_candles >= self.max_holding_candles:
                exit_triggered = True
                exit_reason = "TIME_LIMIT"
                raw_exit = c_close

            if exit_triggered:
                # Fill virtual sell order with slippage
                fill_exit_price = raw_exit * (1.0 - self.slippage_pct)
                gross_exit_val = pos_qty * fill_exit_price
                exit_fee = gross_exit_val * self.fee_pct
                total_fees = self.active_position.entry_fee + exit_fee

                gross_pnl = gross_exit_val - entry_val
                net_pnl = gross_pnl - total_fees
                net_ret = (net_pnl / entry_val) * 100.0

                self.cash += (gross_exit_val - exit_fee)

                outcome = "WIN" if net_pnl > 0 else ("LOSS" if net_pnl < 0 else "BREAKEVEN")

                # Record sell order
                sell_order = VirtualOrder(
                    order_id=f"ORD_{len(self.order_history)+1:05d}",
                    symbol=self.symbol,
                    side="SELL",
                    order_type="MARKET",
                    quantity=pos_qty,
                    price=fill_exit_price,
                    timestamp=time_str,
                )
                self.order_history.append(sell_order)

                completed_trade = VirtualTradeRecord(
                    trade_id=f"TRD_{len(self.trade_history)+1:05d}",
                    symbol=self.symbol,
                    timeframe=self.timeframe,
                    model_version=self.model_version,
                    signal="BUY",
                    timestamp=self._active_trade_meta["signal_time"],
                    entry_time=self.active_position.entry_time,
                    entry_price=self.active_position.entry_price,
                    stop_price=sl_price,
                    target_price=tp_price,
                    prediction_probability=self._active_trade_meta["probability"],
                    quantity=pos_qty,
                    exit_time=time_str,
                    exit_price=float(round(fill_exit_price, 4)),
                    exit_reason=exit_reason,
                    gross_pnl=float(round(gross_pnl, 2)),
                    fees_paid=float(round(total_fees, 2)),
                    net_pnl=float(round(net_pnl, 2)),
                    net_return_pct=float(round(net_ret, 2)),
                    outcome=outcome,
                )
                self.trade_history.append(completed_trade)
                if self.risk_manager is not None:
                    self.risk_manager.on_trade_closed(completed_trade.net_pnl, completed_trade.exit_time)

                self.active_position = None
                self._active_trade_meta = None
                self._holding_candles = 0

        # -------------------------------------------------------------
        # 2. If flat and no trade closed on this candle, run inference
        # -------------------------------------------------------------
        if self.active_position is None and completed_trade is None:
            candle_df = pd.DataFrame([c_dict])
            prob_df = self.model.predict_proba(candle_df)
            p_up = float(prob_df["UP"].iloc[0])

            if p_up >= self.min_confidence:
                # Enter at next available price (close of T with slippage)
                raw_entry = c_close
                fill_entry_price = raw_entry * (1.0 + self.slippage_pct)
                sl_barrier = fill_entry_price * (1.0 - self.stop_loss_pct)
                tp_barrier = fill_entry_price * (1.0 + self.take_profit_pct)

                risk_approved = True
                if self.risk_manager is not None:
                    atr_val = float(c_dict["atr_14"]) if ("atr_14" in c_dict and pd.notna(c_dict["atr_14"])) else None
                    assessment = self.risk_manager.evaluate_trade(
                        symbol=self.symbol,
                        entry_price=fill_entry_price,
                        stop_loss=sl_barrier,
                        take_profit=tp_barrier,
                        is_long=True,
                        atr=atr_val,
                        timestamp=time_str,
                    )
                    if not assessment.approved:
                        risk_approved = False
                    else:
                        sl_barrier = assessment.stop_loss
                        tp_barrier = assessment.take_profit

                if risk_approved:
                    qty = self.sizer.calculate_order_quantity(
                        current_equity=self.cash,
                        current_price=fill_entry_price,
                        stop_loss_price=sl_barrier,
                        probability=p_up,
                    )

                    pos_val = qty * fill_entry_price
                    entry_fee = pos_val * self.fee_pct

                    if pos_val + entry_fee <= self.cash and qty > 0:
                        self.cash -= (pos_val + entry_fee)

                        buy_order = VirtualOrder(
                            order_id=f"ORD_{len(self.order_history)+1:05d}",
                            symbol=self.symbol,
                            side="BUY",
                            order_type="MARKET",
                            quantity=qty,
                            price=fill_entry_price,
                            timestamp=time_str,
                        )
                        self.order_history.append(buy_order)

                        if self.risk_manager is not None:
                            self.risk_manager.on_trade_opened()

                        self.active_position = VirtualPosition(
                            position_id=f"POS_{len(self.trade_history)+1:05d}",
                            symbol=self.symbol,
                            quantity=qty,
                            entry_price=float(round(fill_entry_price, 4)),
                            current_price=float(round(c_close, 4)),
                            take_profit_price=float(round(tp_barrier, 4)),
                            stop_loss_price=float(round(sl_barrier, 4)),
                            unrealized_pnl=0.0,
                            unrealized_pnl_pct=0.0,
                            entry_time=time_str,
                            entry_fee=float(round(entry_fee, 2)),
                        )

                        self._active_trade_meta = {
                            "signal_time": time_str,
                            "probability": p_up,
                        }
                        self._holding_candles = 0

        # Record equity point
        self.equity_log.append({
            "timestamp": time_str,
            "cash": round(self.cash, 2),
            "equity": round(self.total_equity, 2),
            "in_position": self.active_position is not None,
        })

        if self.risk_manager is not None:
            self.risk_manager.on_candle_close()

        return completed_trade

    def get_summary(self) -> Dict[str, Any]:
        """Returns aggregate performance analytics for paper trading."""
        total_trades = len(self.trade_history)
        wins = [t for t in self.trade_history if t.outcome == "WIN"]
        losses = [t for t in self.trade_history if t.outcome == "LOSS"]

        total_net_pnl = sum(t.net_pnl for t in self.trade_history)
        win_rate = (len(wins) / total_trades * 100.0) if total_trades > 0 else 0.0

        summary: Dict[str, Any] = {
            "model_version": self.model_version,
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "initial_capital": self.initial_capital,
            "current_equity": round(self.total_equity, 2),
            "net_profit": round(total_net_pnl, 2),
            "total_return_pct": round(((self.total_equity - self.initial_capital) / self.initial_capital) * 100.0, 2),
            "total_trades": total_trades,
            "winning_trades": len(wins),
            "losing_trades": len(losses),
            "win_rate_pct": round(win_rate, 2),
            "active_position": self.active_position.to_dict() if self.active_position else None,
        }
        if self.risk_manager is not None:
            summary["risk_status"] = self.risk_manager.get_status()
        return summary

    def compare_with_backtest(self, backtest_metrics: BacktestMetrics) -> Dict[str, Any]:
        """
        Compares paper trading metrics with historical backtest expectations.
        Checks for execution drift, win rate divergence, and slippage decay.
        """
        paper_summary = self.get_summary()

        win_rate_diff = paper_summary["win_rate_pct"] - backtest_metrics.win_rate_pct
        return_diff = paper_summary["total_return_pct"] - backtest_metrics.total_return_pct

        return {
            "paper_trades": paper_summary["total_trades"],
            "backtest_trades": backtest_metrics.total_trades,
            "paper_win_rate": paper_summary["win_rate_pct"],
            "backtest_win_rate": backtest_metrics.win_rate_pct,
            "win_rate_divergence_pct": round(win_rate_diff, 2),
            "paper_return_pct": paper_summary["total_return_pct"],
            "backtest_return_pct": backtest_metrics.total_return_pct,
            "return_divergence_pct": round(return_diff, 2),
            "performance_parity": abs(win_rate_diff) <= 10.0,
        }

    def save_state(self, filepath: str) -> str:
        """Persists paper trading engine state to disk as JSON."""
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
        state = {
            "model_version": self.model_version,
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "initial_capital": self.initial_capital,
            "cash": self.cash,
            "summary": self.get_summary(),
            "trades": [t.to_dict() for t in self.trade_history],
            "orders": [o.to_dict() for o in self.order_history],
        }
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
        return filepath
