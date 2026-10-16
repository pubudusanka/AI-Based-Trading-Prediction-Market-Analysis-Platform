"""
Financial Performance & Risk Metrics Engine for Trading Backtests.
Reference: Section 25 (Phase 20) & Section 26 (Phase 21) of Implementation Plan.

Computes:
- Total Return & Annualized Return (CAGR)
- Win Rate, Loss Rate, Profit Factor, Expectancy
- Max Drawdown (percentage and duration in candles)
- Sharpe Ratio, Sortino Ratio, Calmar Ratio
- Market Exposure & Portfolio Turnover
- Max Consecutive Wins & Consecutive Losses
- Average Holding Period
- Friction breakdown (Trading Fees and Slippage)
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional
import numpy as np
import pandas as pd

from src.backtesting.trade import Trade


@dataclass
class BacktestMetrics:
    """Comprehensive performance and risk analytics."""
    initial_capital: float
    final_equity: float
    net_profit: float
    total_return_pct: float
    annualized_return_pct: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    breakeven_trades: int
    win_rate_pct: float
    loss_rate_pct: float
    profit_factor: float
    average_win: float
    average_loss: float
    win_loss_ratio: float
    expectancy_per_trade: float
    max_drawdown_pct: float
    max_drawdown_value: float
    max_drawdown_duration_candles: int
    sharpe_ratio: float
    sortino_ratio: float
    calmar_ratio: float
    market_exposure_pct: float
    portfolio_turnover: float
    max_consecutive_wins: int
    max_consecutive_losses: int
    average_holding_period_candles: float
    total_fees_paid: float
    total_slippage_cost: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class MetricsCalculator:
    """Calculates full statistical and portfolio metrics from equity curve and trades."""

    # 15m candles per year = 365.25 * 24 * 4 = 35,064
    CANDLES_PER_YEAR_15M = 35064.0
    RISK_FREE_RATE_ANNUAL = 0.04  # 4% annual risk-free benchmark

    @classmethod
    def compute(
        cls,
        trades: List[Trade],
        equity_series: pd.Series,
        initial_capital: float,
        timeframe: str = "15m",
        candles_per_year: Optional[float] = None,
    ) -> BacktestMetrics:
        """Computes comprehensive backtesting analytics."""
        cpy = candles_per_year or cls.CANDLES_PER_YEAR_15M

        final_equity = float(equity_series.iloc[-1]) if len(equity_series) > 0 else initial_capital
        net_profit = final_equity - initial_capital
        total_return_pct = (net_profit / initial_capital) * 100.0 if initial_capital > 0 else 0.0

        total_candles = len(equity_series)
        years = total_candles / cpy if cpy > 0 and total_candles > 0 else 1.0

        if years > 0 and final_equity > 0:
            annualized_return_pct = float(((final_equity / initial_capital) ** (1.0 / max(years, 0.01)) - 1.0) * 100.0)
        else:
            annualized_return_pct = 0.0

        total_trades = len(trades)
        if total_trades == 0:
            return BacktestMetrics(
                initial_capital=initial_capital,
                final_equity=final_equity,
                net_profit=net_profit,
                total_return_pct=total_return_pct,
                annualized_return_pct=annualized_return_pct,
                total_trades=0,
                winning_trades=0,
                losing_trades=0,
                breakeven_trades=0,
                win_rate_pct=0.0,
                loss_rate_pct=0.0,
                profit_factor=0.0,
                average_win=0.0,
                average_loss=0.0,
                win_loss_ratio=0.0,
                expectancy_per_trade=0.0,
                max_drawdown_pct=0.0,
                max_drawdown_value=0.0,
                max_drawdown_duration_candles=0,
                sharpe_ratio=0.0,
                sortino_ratio=0.0,
                calmar_ratio=0.0,
                market_exposure_pct=0.0,
                portfolio_turnover=0.0,
                max_consecutive_wins=0,
                max_consecutive_losses=0,
                average_holding_period_candles=0.0,
                total_fees_paid=0.0,
                total_slippage_cost=0.0,
            )

        winning_trades = [t for t in trades if t.net_pnl > 0]
        losing_trades = [t for t in trades if t.net_pnl < 0]
        breakeven_trades = [t for t in trades if t.net_pnl == 0]

        n_wins = len(winning_trades)
        n_losses = len(losing_trades)
        n_be = len(breakeven_trades)

        win_rate_pct = (n_wins / total_trades) * 100.0
        loss_rate_pct = (n_losses / total_trades) * 100.0

        gross_profit = sum(t.net_pnl for t in winning_trades)
        gross_loss = abs(sum(t.net_pnl for t in losing_trades))

        profit_factor = float(gross_profit / gross_loss) if gross_loss > 0 else (999.0 if gross_profit > 0 else 0.0)

        avg_win = float(gross_profit / n_wins) if n_wins > 0 else 0.0
        avg_loss = float(gross_loss / n_losses) if n_losses > 0 else 0.0
        win_loss_ratio = float(avg_win / avg_loss) if avg_loss > 0 else (999.0 if avg_win > 0 else 0.0)
        expectancy = float(net_profit / total_trades)

        # Drawdowns
        eq_arr = np.asarray(equity_series, dtype=np.float64)
        running_max = np.maximum.accumulate(eq_arr)
        drawdowns = (running_max - eq_arr) / np.where(running_max > 0, running_max, 1.0)
        max_drawdown_pct = float(np.max(drawdowns)) * 100.0
        max_drawdown_val = float(np.max(running_max - eq_arr))

        # Max drawdown duration
        max_dd_duration = 0
        curr_dd_duration = 0
        for eq, peak in zip(eq_arr, running_max):
            if eq < peak:
                curr_dd_duration += 1
                max_dd_duration = max(max_dd_duration, curr_dd_duration)
            else:
                curr_dd_duration = 0

        # Sharpe and Sortino (based on candle returns)
        candle_returns = np.asarray(equity_series.pct_change().dropna(), dtype=np.float64)
        c_std = float(np.std(candle_returns)) if len(candle_returns) > 1 else 0.0

        if len(candle_returns) > 1 and c_std > 1e-9:
            rf_per_candle = cls.RISK_FREE_RATE_ANNUAL / cpy
            excess_returns = np.asarray(candle_returns - rf_per_candle, dtype=np.float64)
            mean_excess = float(np.mean(excess_returns))
            std_returns = c_std

            sharpe_ratio = float((mean_excess / std_returns) * np.sqrt(cpy))

            downside_returns = np.asarray(candle_returns[candle_returns < 0], dtype=np.float64)
            d_std = float(np.std(downside_returns)) if len(downside_returns) > 0 else 0.0

            if len(downside_returns) > 0 and d_std > 1e-9:
                downside_sq = np.asarray(downside_returns ** 2, dtype=np.float64)
                downside_std = float(np.sqrt(np.mean(downside_sq)))
                sortino_ratio = float((mean_excess / downside_std) * np.sqrt(cpy))
            else:
                sortino_ratio = sharpe_ratio
        else:
            sharpe_ratio = 0.0
            sortino_ratio = 0.0

        calmar_ratio = float(annualized_return_pct / max_drawdown_pct) if max_drawdown_pct > 0 else 0.0

        # Exposure and holding periods
        total_holding_candles = sum(t.holding_candles for t in trades)
        market_exposure_pct = float(min(100.0, (total_holding_candles / max(1, total_candles)) * 100.0))
        avg_holding = float(total_holding_candles / total_trades)

        # Turnover = sum(trade position values) / initial_capital
        total_position_val = sum(t.position_value for t in trades)
        portfolio_turnover = float(total_position_val / initial_capital) if initial_capital > 0 else 0.0

        # Consecutive wins / losses
        max_consec_w = 0
        curr_consec_w = 0
        max_consec_l = 0
        curr_consec_l = 0

        for t in trades:
            if t.net_pnl > 0:
                curr_consec_w += 1
                max_consec_w = max(max_consec_w, curr_consec_w)
                curr_consec_l = 0
            elif t.net_pnl < 0:
                curr_consec_l += 1
                max_consec_l = max(max_consec_l, curr_consec_l)
                curr_consec_w = 0
            else:
                curr_consec_w = 0
                curr_consec_l = 0

        total_fees = float(sum(t.total_fees for t in trades))
        total_slip = float(sum(t.slippage_cost for t in trades))

        return BacktestMetrics(
            initial_capital=round(initial_capital, 2),
            final_equity=round(final_equity, 2),
            net_profit=round(net_profit, 2),
            total_return_pct=round(total_return_pct, 2),
            annualized_return_pct=round(annualized_return_pct, 2),
            total_trades=total_trades,
            winning_trades=n_wins,
            losing_trades=n_losses,
            breakeven_trades=n_be,
            win_rate_pct=round(win_rate_pct, 2),
            loss_rate_pct=round(loss_rate_pct, 2),
            profit_factor=round(profit_factor, 2),
            average_win=round(avg_win, 2),
            average_loss=round(avg_loss, 2),
            win_loss_ratio=round(win_loss_ratio, 2),
            expectancy_per_trade=round(expectancy, 2),
            max_drawdown_pct=round(max_drawdown_pct, 2),
            max_drawdown_value=round(max_drawdown_val, 2),
            max_drawdown_duration_candles=max_dd_duration,
            sharpe_ratio=round(sharpe_ratio, 2),
            sortino_ratio=round(sortino_ratio, 2),
            calmar_ratio=round(calmar_ratio, 2),
            market_exposure_pct=round(market_exposure_pct, 2),
            portfolio_turnover=round(portfolio_turnover, 2),
            max_consecutive_wins=max_consec_w,
            max_consecutive_losses=max_consec_l,
            average_holding_period_candles=round(avg_holding, 1),
            total_fees_paid=round(total_fees, 2),
            total_slippage_cost=round(total_slip, 2),
        )
