"""
Trade Record Data Structure for Backtesting & Execution Audits.
Reference: Section 25 (Phase 20) & Section 26 (Phase 21) of Implementation Plan.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Dict, Any


@dataclass
class Trade:
    """Represents a completed trade lifecycle in the backtesting engine."""
    trade_id: int
    symbol: str
    timeframe: str
    side: str  # "LONG" or "SHORT"
    signal_time: str
    entry_time: str
    entry_price: float
    raw_entry_price: float
    exit_time: str
    exit_price: float
    raw_exit_price: float
    quantity: float
    position_value: float
    exit_reason: str  # "TAKE_PROFIT", "STOP_LOSS", "TIME_LIMIT", "SIGNAL_REVERSAL", "END_OF_DATA"
    gross_pnl: float
    gross_return_pct: float
    entry_fee: float
    exit_fee: float
    total_fees: float
    slippage_cost: float
    net_pnl: float
    net_return_pct: float
    holding_candles: int
    is_winner: bool

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
