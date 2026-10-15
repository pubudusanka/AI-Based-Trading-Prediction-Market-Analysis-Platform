package com.aitrading.provider;

import com.aitrading.provider.dto.CandleDto;
import java.time.Instant;
import java.util.List;

public interface MarketDataProvider {
    
    /**
     * Fetch historical candlestick (OHLCV) batches from provider.
     */
    List<CandleDto> fetchHistoricalCandles(
        String symbol,
        String timeframe,
        Instant startTime,
        Instant endTime,
        int limit
    );

    String getProviderName();
}
