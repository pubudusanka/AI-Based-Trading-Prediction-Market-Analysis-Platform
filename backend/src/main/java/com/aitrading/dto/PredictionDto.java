package com.aitrading.dto;

import java.math.BigDecimal;
import java.time.Instant;
import java.util.List;
import java.util.Map;

public record PredictionDto(
    Long id,
    String symbol,
    String timeframe,
    Instant candleTime,
    String modelVersion,
    String predictedClass,
    BigDecimal probabilityUp,
    BigDecimal probabilityDown,
    BigDecimal probabilityNeutral,
    List<Map<String, Object>> topFactors,
    String disclaimer
) {}
