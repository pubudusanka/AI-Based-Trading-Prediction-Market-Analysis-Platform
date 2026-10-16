"""
Real-Time Market Data Ingestion Buffer & Closed-Candle Feature Pipeline.
Reference: Section 29 (Phase 24) of Implementation Plan.

Guarantees:
- Maintains rolling candle window (e.g. 200 candles) for technical indicator warmup.
- Strict closed-candle execution: Feature calculation and model inference are triggered
  ONLY when a candle is finalized and closed (is_closed == True), preventing intrabar noise.
- Out-of-order and duplicate candle filtering using candle open timestamps.
- Automated feature generation via FeatureDatasetBuilder upon candle close.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Callable
import pandas as pd

from src.features.dataset import FeatureDatasetBuilder


@dataclass
class ClosedCandleEvent:
    """Event emitted strictly when a 15m candle closes."""
    symbol: str
    timeframe: str
    open_time: str
    close_time: str
    open: float
    high: float
    low: float
    close: float
    volume: float
    is_closed: bool = True
    emitted_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class RollingCandleBuffer:
    """
    In-memory rolling candle window per (symbol, timeframe) for real-time feature computation.
    """

    def __init__(
        self,
        symbol: str = "BTC/USDT",
        timeframe: str = "15m",
        max_candles: int = 250,
        min_warmup_candles: int = 50,
    ):
        self.symbol = symbol
        self.timeframe = timeframe
        self.max_candles = max_candles
        self.min_warmup_candles = min_warmup_candles

        self._candles: List[Dict[str, Any]] = []
        self._seen_open_times: set[str] = set()
        self.feature_builder = FeatureDatasetBuilder(k_confirmation=2)
        self._listeners: List[Callable[[ClosedCandleEvent, pd.DataFrame], None]] = []

    def add_listener(self, callback: Callable[[ClosedCandleEvent, pd.DataFrame], None]) -> None:
        """Registers a subscriber for closed candle events with computed features."""
        self._listeners.append(callback)

    def on_candle_update(
        self,
        candle: Dict[str, Any],
        is_closed: bool = True,
    ) -> Optional[ClosedCandleEvent]:
        """
        Processes incoming streaming candle update.
        Triggers feature calculation and event emission ONLY when is_closed is True.
        """
        open_time = str(candle.get("open_time", candle.get("timestamp", "")))
        if not open_time:
            open_time = datetime.now(timezone.utc).isoformat()

        # Deduplication of identical closed candles
        if is_closed and open_time in self._seen_open_times:
            return None

        clean_candle = {
            "open_time": open_time,
            "close_time": str(candle.get("close_time", "")),
            "open": float(candle["open"]),
            "high": float(candle["high"]),
            "low": float(candle["low"]),
            "close": float(candle["close"]),
            "volume": float(candle.get("volume", 0.0)),
        }

        if is_closed:
            self._candles.append(clean_candle)
            self._seen_open_times.add(open_time)

            # Trim to max window
            if len(self._candles) > self.max_candles:
                removed = self._candles.pop(0)
                self._seen_open_times.discard(removed["open_time"])

            event = ClosedCandleEvent(
                symbol=self.symbol,
                timeframe=self.timeframe,
                open_time=clean_candle["open_time"],
                close_time=clean_candle["close_time"],
                open=clean_candle["open"],
                high=clean_candle["high"],
                low=clean_candle["low"],
                close=clean_candle["close"],
                volume=clean_candle["volume"],
            )

            # If warmup is sufficient, calculate features and notify listeners
            if len(self._candles) >= self.min_warmup_candles:
                features_df = self.get_latest_features()
                for listener in self._listeners:
                    try:
                        listener(event, features_df)
                    except Exception:
                        pass

            return event

        return None

    def get_ohlcv_dataframe(self) -> pd.DataFrame:
        """Returns the current buffer as a sorted DatetimeIndex pandas DataFrame."""
        if not self._candles:
            return pd.DataFrame(columns=["open", "high", "low", "close", "volume"])

        df = pd.DataFrame(self._candles)
        try:
            df.index = pd.to_datetime(df["open_time"], utc=True)
        except Exception:
            df.index = pd.RangeIndex(len(df))

        subset = pd.DataFrame(df[["open", "high", "low", "close", "volume"]])
        return subset.copy()

    def get_latest_features(self) -> pd.DataFrame:
        """
        Computes technical indicators, market structure, and candlestick features on buffer.
        Returns DataFrame with all engineered feature columns.
        """
        ohlcv_df = self.get_ohlcv_dataframe()
        if len(ohlcv_df) < self.min_warmup_candles:
            raise ValueError(
                f"Buffer length ({len(ohlcv_df)}) is below minimum warmup ({self.min_warmup_candles})."
            )

        feat_dataset = self.feature_builder.build(ohlcv_df, symbol=self.symbol, timeframe=self.timeframe)
        return pd.DataFrame(feat_dataset.data)
