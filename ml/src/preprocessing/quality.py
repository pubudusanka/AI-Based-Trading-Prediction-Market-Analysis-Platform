"""
Historical Data Quality Pipeline.
Reference: Section 10 (Phase 5) of Implementation Plan.
Performs rigorous audit of OHLCV timeseries data prior to feature engineering.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Tuple, Optional
import json
import logging
import pandas as pd
import numpy as np

logger = logging.getLogger("preprocessing.quality")


@dataclass
class TimestampGap:
    expected_time: datetime
    actual_next_time: datetime
    gap_duration_minutes: float
    missing_candle_count: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "expected_time": self.expected_time.isoformat(),
            "actual_next_time": self.actual_next_time.isoformat(),
            "gap_duration_minutes": round(self.gap_duration_minutes, 2),
            "missing_candle_count": self.missing_candle_count,
        }


@dataclass
class DataQualityReport:
    symbol: str
    timeframe: str
    total_candles: int
    expected_candles: int
    missing_candles: int
    duplicate_candles: int
    invalid_ohlc_candles: int
    zero_or_negative_price_candles: int
    abnormal_volume_candles: int
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    coverage_percentage: float = 0.0
    gaps: List[TimestampGap] = field(default_factory=list)
    is_clean: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "total_candles": self.total_candles,
            "expected_candles": self.expected_candles,
            "missing_candles": self.missing_candles,
            "duplicate_candles": self.duplicate_candles,
            "invalid_ohlc_candles": self.invalid_ohlc_candles,
            "zero_or_negative_price_candles": self.zero_or_negative_price_candles,
            "abnormal_volume_candles": self.abnormal_volume_candles,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "coverage_percentage": round(self.coverage_percentage, 4),
            "gap_count": len(self.gaps),
            "gaps": [g.to_dict() for g in self.gaps[:20]],  # cap sample gaps
            "is_clean": self.is_clean,
        }

    def generate_markdown(self) -> str:
        status_badge = "✅ CLEAN" if self.is_clean else "⚠️ ISSUES DETECTED"
        md = [
            f"# Data Quality Report: {self.symbol} ({self.timeframe})",
            "",
            f"**Status:** {status_badge}  ",
            f"**Evaluation Date:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}  ",
            f"**Date Range:** {self.start_date} to {self.end_date}  ",
            "",
            "## Summary Metrics",
            "",
            "| Metric | Value |",
            "|---|---|",
            f"| **Total Candles Received** | {self.total_candles:,} |",
            f"| **Expected Theoretical Candles** | {self.expected_candles:,} |",
            f"| **Missing Candles** | {self.missing_candles:,} |",
            f"| **Duplicate Candles** | {self.duplicate_candles:,} |",
            f"| **Invalid OHLC Candles** | {self.invalid_ohlc_candles:,} |",
            f"| **Zero / Negative Prices** | {self.zero_or_negative_price_candles:,} |",
            f"| **Abnormal Volume Spikes** | {self.abnormal_volume_candles:,} |",
            f"| **Data Coverage** | **{self.coverage_percentage:.2f}%** |",
            "",
        ]

        if self.gaps:
            md.append("## Detected Timestamp Gaps (Sample)")
            md.append("| Expected Time | Resume Time | Gap Minutes | Missing Candles |")
            md.append("|---|---|---|---|")
            for g in self.gaps[:10]:
                md.append(f"| {g.expected_time} | {g.actual_next_time} | {g.gap_duration_minutes:.1f}m | {g.missing_candle_count} |")
            if len(self.gaps) > 10:
                md.append(f"\n*...and {len(self.gaps) - 10} additional gap intervals.*")
        else:
            md.append("## Timestamp Gaps\nNo missing timestamp gaps detected. Continuous timeseries verified.")

        return "\n".join(md)


class DataQualityAuditor:
    """
    Automated auditor to verify OHLCV integrity according to Phase 5.
    """

    TIMEFRAME_MAP = {
        "1m": timedelta(minutes=1),
        "5m": timedelta(minutes=5),
        "15m": timedelta(minutes=15),
        "30m": timedelta(minutes=30),
        "1h": timedelta(hours=1),
        "4h": timedelta(hours=4),
        "1d": timedelta(days=1),
    }

    def __init__(self, volume_outlier_std: float = 8.0):
        self.volume_outlier_std = volume_outlier_std

    def audit(
        self,
        df: pd.DataFrame,
        symbol: str = "BTC/USDT",
        timeframe: str = "15m"
    ) -> DataQualityReport:
        if df.empty:
            return DataQualityReport(
                symbol=symbol,
                timeframe=timeframe,
                total_candles=0,
                expected_candles=0,
                missing_candles=0,
                duplicate_candles=0,
                invalid_ohlc_candles=0,
                zero_or_negative_price_candles=0,
                abnormal_volume_candles=0,
                is_clean=False
            )

        data = df.copy()

        # 1. Normalize index to UTC DatetimeIndex
        if not isinstance(data.index, pd.DatetimeIndex):
            if "open_time" in data.columns:
                data["open_time"] = pd.to_datetime(data["open_time"], utc=True)
                data.set_index("open_time", inplace=True)
            else:
                raise ValueError("DataFrame must have a DatetimeIndex or 'open_time' column")
        elif data.index.tz is None:
            data.index = data.index.tz_localize("UTC")
        else:
            data.index = data.index.tz_convert("UTC")

        # 2. Check duplicates
        duplicate_count = int(data.index.duplicated().sum())
        if duplicate_count > 0:
            data = data[~data.index.duplicated(keep="first")]

        data.sort_index(inplace=True)

        def _to_dt(val: Any) -> datetime:
            dt = pd.Timestamp(str(val)).to_pydatetime()
            if isinstance(dt, datetime):
                return dt
            raise ValueError(f"Invalid timestamp value: {val}")

        start_date: datetime = _to_dt(data.index[0])
        end_date: datetime = _to_dt(data.index[-1])
        total_candles = len(data)

        # 3. Timeframe continuous interval checking
        interval_delta = self.TIMEFRAME_MAP.get(timeframe.lower(), timedelta(minutes=15))
        total_duration = end_date - start_date
        expected_candles = int(total_duration / interval_delta) + 1 if total_duration.total_seconds() >= 0 else 1

        # Find timestamp gaps
        time_series = pd.Series(pd.to_datetime(data.index), index=data.index)
        time_diffs = time_series.diff()
        expected_sec = interval_delta.total_seconds()
        gap_mask = time_diffs > (interval_delta + timedelta(seconds=1))

        gaps: List[TimestampGap] = []
        missing_candles_count = 0

        filtered_diffs = pd.Series(time_diffs[gap_mask])
        for gap_time, diff in filtered_diffs.items():
            gap_seconds = pd.Timedelta(diff).total_seconds()
            missing_in_gap = int(gap_seconds // expected_sec) - 1
            if missing_in_gap > 0:
                expected_prev = pd.Timestamp(str(gap_time)) - pd.Timedelta(diff) + interval_delta
                missing_candles_count += missing_in_gap
                gaps.append(TimestampGap(
                    expected_time=_to_dt(expected_prev),
                    actual_next_time=_to_dt(gap_time),
                    gap_duration_minutes=gap_seconds / 60.0,
                    missing_candle_count=missing_in_gap
                ))

        # 4. Check OHLC validity
        # high >= max(open, close), low <= min(open, close), high >= low
        o = pd.Series(data["open"], dtype=float)
        h = pd.Series(data["high"], dtype=float)
        l = pd.Series(data["low"], dtype=float)
        c = pd.Series(data["close"], dtype=float)

        max_oc = o.where(o >= c, c)
        min_oc = o.where(o <= c, c)

        invalid_high = h < max_oc
        invalid_low = l > min_oc
        invalid_hl = h < l
        invalid_ohlc_mask = invalid_high | invalid_low | invalid_hl
        invalid_ohlc_count = int(invalid_ohlc_mask.sum())

        # 5. Non-positive prices (<= 0)
        zero_neg_mask = (data["open"] <= 0) | (data["high"] <= 0) | (data["low"] <= 0) | (data["close"] <= 0)
        zero_or_negative_price_count = int(zero_neg_mask.sum())

        # 6. Volume checks (volume < 0 or extreme outlier > 8 std)
        negative_vol = data["volume"] < 0
        vol_mean = data["volume"].mean()
        vol_std = data["volume"].std()
        outlier_vol = data["volume"] > (vol_mean + self.volume_outlier_std * vol_std) if vol_std > 0 else pd.Series(False, index=data.index)
        abnormal_volume_count = int((negative_vol | outlier_vol).sum())

        coverage = (total_candles / expected_candles * 100.0) if expected_candles > 0 else 100.0
        coverage = min(coverage, 100.0)

        is_clean = bool(
            missing_candles_count == 0
            and duplicate_count == 0
            and invalid_ohlc_count == 0
            and zero_or_negative_price_count == 0
            and (negative_vol.sum() == 0)
        )

        return DataQualityReport(
            symbol=symbol,
            timeframe=timeframe,
            total_candles=total_candles,
            expected_candles=expected_candles,
            missing_candles=missing_candles_count,
            duplicate_candles=duplicate_count,
            invalid_ohlc_candles=invalid_ohlc_count,
            zero_or_negative_price_candles=zero_or_negative_price_count,
            abnormal_volume_candles=abnormal_volume_count,
            start_date=start_date,
            end_date=end_date,
            coverage_percentage=coverage,
            gaps=gaps,
            is_clean=is_clean
        )
