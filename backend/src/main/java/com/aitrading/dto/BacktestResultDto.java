package com.aitrading.dto;

import java.math.BigDecimal;
import java.time.Instant;
import java.util.List;
import java.util.Map;

public record BacktestResultDto(
    Long id,
    String strategyVersion,
    String modelVersion,
    String symbol,
    String timeframe,
    Instant startTime,
    Instant endTime,
    BigDecimal initialCapital,
    Integer totalTrades,
    BigDecimal winRate,
    BigDecimal profitFactor,
    BigDecimal maxDrawdown,
    BigDecimal sharpeRatio,
    BigDecimal totalReturn,
    List<Map<String, Object>> trades
) {}
