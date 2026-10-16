package com.aitrading.dto;

import java.time.Instant;

public record MarketStatusDto(
    String symbol,
    String timeframe,
    String provider,
    Instant latestCandleTime,
    Long totalCandles,
    boolean isFresh,
    String statusMessage
) {}
