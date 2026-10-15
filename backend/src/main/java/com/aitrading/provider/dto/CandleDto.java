package com.aitrading.provider.dto;

import java.math.BigDecimal;
import java.time.Instant;

public record CandleDto(
    String symbol,
    String exchange,
    String timeframe,
    Instant openTime,
    Instant closeTime,
    BigDecimal open,
    BigDecimal high,
    BigDecimal low,
    BigDecimal close,
    BigDecimal volume,
    BigDecimal quoteVolume,
    Integer tradeCount
) {
    public boolean isValid() {
        if (high.compareTo(open.max(close)) < 0) return false;
        if (low.compareTo(open.min(close)) > 0) return false;
        if (high.compareTo(low) < 0) return false;
        if (volume.compareTo(BigDecimal.ZERO) < 0) return false;
        return openTime.isBefore(closeTime);
    }
}
