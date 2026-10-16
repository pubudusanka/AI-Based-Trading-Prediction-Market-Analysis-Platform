package com.aitrading.dto;

import java.time.Instant;
import java.util.List;
import java.util.Map;

public record PatternFeatureDto(
    String symbol,
    String timeframe,
    Instant candleTime,
    List<String> activePatterns,
    Map<String, Double> patternConfidence
) {}
