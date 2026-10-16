package com.aitrading.dto;

import java.math.BigDecimal;
import java.time.Instant;

public record TradingSignalDto(
    Long id,
    String symbol,
    String timeframe,
    Instant candleTime,
    String signal, // BUY, SELL, HOLD, NO_SIGNAL
    String mlPrediction,
    BigDecimal probabilityUp,
    BigDecimal probabilityDown,
    BigDecimal technicalScore,
    Boolean riskAcceptable,
    BigDecimal suggestedEntry,
    BigDecimal suggestedTakeProfit,
    BigDecimal suggestedStopLoss,
    String reasoning
) {}
