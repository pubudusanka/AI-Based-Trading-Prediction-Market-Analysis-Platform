"""
Historical and Real-time Market Data Ingestion Client.
Reference: Section 7 & 8 of Implementation Plan.
Target Asset: BTC/USDT, 15m.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any, Tuple
import logging
import time
import requests
import pandas as pd

logger = logging.getLogger("ingestion.collector")


@dataclass(frozen=True)
class Candle:
    symbol: str
    exchange: str
    timeframe: str
    open_time: datetime
    close_time: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    quote_volume: float
    trade_count: int

    def validate(self) -> Tuple[bool, Optional[str]]:
        """
        Validates OHLC invariants and data consistency according to Phase 3 rules:
        - high >= max(open, close)
        - low <= min(open, close)
        - high >= low
        - volume >= 0
        - open_time < close_time
        """
        if self.high < max(self.open, self.close):
            return False, f"Invariant violated: high ({self.high}) < max(open, close) ({max(self.open, self.close)})"
        if self.low > min(self.open, self.close):
            return False, f"Invariant violated: low ({self.low}) > min(open, close) ({min(self.open, self.close)})"
        if self.high < self.low:
            return False, f"Invariant violated: high ({self.high}) < low ({self.low})"
        if self.volume < 0:
            return False, f"Invariant violated: volume ({self.volume}) < 0"
        if self.open_time >= self.close_time:
            return False, f"Timestamp error: open_time ({self.open_time}) >= close_time ({self.close_time})"
        return True, None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "exchange": self.exchange,
            "timeframe": self.timeframe,
            "open_time": self.open_time.isoformat(),
            "close_time": self.close_time.isoformat(),
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.close,
            "volume": self.volume,
            "quote_volume": self.quote_volume,
            "trade_count": self.trade_count,
        }


class BinanceMarketDataClient:
    """
    Public REST client for Binance Spot Market Data with automated pagination,
    exponential backoff, and data invariant validation.
    """

    BASE_URL = "https://api.binance.com"
    KLINES_ENDPOINT = "/api/v3/klines"
    MAX_LIMIT = 1000

    def __init__(self, base_url: Optional[str] = None, session: Optional[requests.Session] = None):
        self.base_url = base_url or self.BASE_URL
        self.session = session or requests.Session()
        self.session.headers.update({
            "User-Agent": "AI-Trading-Prediction-Platform/1.0"
        })

    def fetch_klines(
        self,
        symbol: str = "BTCUSDT",
        interval: str = "15m",
        start_time_ms: Optional[int] = None,
        end_time_ms: Optional[int] = None,
        limit: int = 1000,
        max_retries: int = 3,
        retry_delay_sec: float = 1.0
    ) -> List[Candle]:
        """
        Fetch a single batch of klines from Binance API.
        """
        url = f"{self.base_url}{self.KLINES_ENDPOINT}"
        params: Dict[str, Any] = {
            "symbol": symbol.replace("/", ""),
            "interval": interval,
            "limit": min(limit, self.MAX_LIMIT)
        }
        if start_time_ms is not None:
            params["startTime"] = start_time_ms
        if end_time_ms is not None:
            params["endTime"] = end_time_ms

        for attempt in range(1, max_retries + 1):
            try:
                response = self.session.get(url, params=params, timeout=10)
                if response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", 10))
                    logger.warning("Rate limit 429 encountered. Backing off for %ds", retry_after)
                    time.sleep(retry_after)
                    continue

                response.raise_for_status()
                raw_data = response.json()
                candles: List[Candle] = []

                for k in raw_data:
                    # Binance Kline schema:
                    # [0: open_time, 1: open, 2: high, 3: low, 4: close, 5: volume, 6: close_time, 7: quote_vol, 8: trade_count, ...]
                    open_dt = datetime.fromtimestamp(k[0] / 1000.0, tz=timezone.utc)
                    close_dt = datetime.fromtimestamp(k[6] / 1000.0, tz=timezone.utc)

                    candle = Candle(
                        symbol=symbol,
                        exchange="BINANCE",
                        timeframe=interval,
                        open_time=open_dt,
                        close_time=close_dt,
                        open=float(k[1]),
                        high=float(k[2]),
                        low=float(k[3]),
                        close=float(k[4]),
                        volume=float(k[5]),
                        quote_volume=float(k[7]),
                        trade_count=int(k[8])
                    )

                    valid, err = candle.validate()
                    if not valid:
                        logger.error("Invalid candle rejected: %s", err)
                        continue

                    candles.append(candle)

                return candles

            except (requests.RequestException, ValueError) as ex:
                logger.warning("Request attempt %d failed: %s", attempt, ex)
                if attempt == max_retries:
                    raise
                time.sleep(retry_delay_sec * (2 ** (attempt - 1)))

        return []

    def backfill_range(
        self,
        symbol: str = "BTCUSDT",
        interval: str = "15m",
        start_dt: datetime = None,
        end_dt: datetime = None,
        batch_delay_sec: float = 0.2
    ) -> List[Candle]:
        """
        Paginates backwards or forwards to retrieve all continuous candles between start_dt and end_dt.
        Ensures strict deduplication by open_time.
        """
        start_ms = int(start_dt.timestamp() * 1000) if start_dt else None
        end_ms = int(end_dt.timestamp() * 1000) if end_dt else int(time.time() * 1000)

        all_candles: Dict[int, Candle] = {}
        current_start = start_ms

        while True:
            batch = self.fetch_klines(
                symbol=symbol,
                interval=interval,
                start_time_ms=current_start,
                end_time_ms=end_ms,
                limit=self.MAX_LIMIT
            )

            if not batch:
                break

            for candle in batch:
                open_ts = int(candle.open_time.timestamp())
                all_candles[open_ts] = candle

            last_open_ms = int(batch[-1].open_time.timestamp() * 1000)
            logger.info("Fetched batch of %d candles. Current progress: %s", len(batch), batch[-1].open_time)

            if len(batch) < self.MAX_LIMIT or (end_ms and last_open_ms >= end_ms):
                break

            # Next page starts 1ms after last received open time to avoid duplicates
            current_start = last_open_ms + 1
            time.sleep(batch_delay_sec)

        sorted_candles = [all_candles[k] for k in sorted(all_candles.keys())]
        logger.info("Total continuous valid candles collected: %d", len(sorted_candles))
        return sorted_candles

    @staticmethod
    def to_dataframe(candles: List[Candle]) -> pd.DataFrame:
        """Converts candle list to standardized pandas DataFrame indexed by open_time."""
        if not candles:
            return pd.DataFrame()
        records = [c.to_dict() for c in candles]
        df = pd.DataFrame(records)
        df["open_time"] = pd.to_datetime(df["open_time"])
        df["close_time"] = pd.to_datetime(df["close_time"])
        df.set_index("open_time", inplace=True)
        df.sort_index(inplace=True)
        return df
