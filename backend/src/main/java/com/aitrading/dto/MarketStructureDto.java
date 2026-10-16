package com.aitrading.dto;

import java.math.BigDecimal;
import java.time.Instant;

public record MarketStructureDto(
    String symbol,
    String timeframe,
    Instant candleTime,
    String trendDirection, // BULLISH, BEARISH, SIDEWAYS
    BigDecimal swingHigh,
    BigDecimal swingLow,
    boolean breakOfStructure,
    boolean changeOfCharacter,
    String supportResistanceLevel
) {}
