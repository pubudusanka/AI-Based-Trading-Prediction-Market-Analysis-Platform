package com.aitrading.dto;

import java.math.BigDecimal;
import java.time.Instant;
import java.util.Map;

public record IndicatorFeatureDto(
    String symbol,
    String timeframe,
    Instant candleTime,
    BigDecimal rsi,
    BigDecimal ema20,
    BigDecimal ema50,
    BigDecimal ema200,
    BigDecimal macd,
    BigDecimal macdSignal,
    BigDecimal atr,
    BigDecimal adx,
    Map<String, Object> additionalIndicators
) {}
