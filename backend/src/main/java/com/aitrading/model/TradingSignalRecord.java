package com.aitrading.model;

import jakarta.persistence.*;
import java.math.BigDecimal;
import java.time.Instant;

@Entity
@Table(name = "trading_signal", indexes = {
    @Index(name = "idx_signal_lookup", columnList = "symbol, timeframe, candle_time DESC")
})
public class TradingSignalRecord {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false, length = 32)
    private String symbol;

    @Column(nullable = false, length = 10)
    private String timeframe;

    @Column(name = "candle_time", nullable = false)
    private Instant candleTime;

    @Column(nullable = false, length = 20)
    private String signal; // BUY, SELL, HOLD, NO_SIGNAL

    @Column(name = "ml_prediction", length = 20)
    private String mlPrediction;

    @Column(name = "probability_up", precision = 6, scale = 5)
    private BigDecimal probabilityUp;

    @Column(name = "probability_down", precision = 6, scale = 5)
    private BigDecimal probabilityDown;

    @Column(name = "probability_neutral", precision = 6, scale = 5)
    private BigDecimal probabilityNeutral;

    @Column(name = "technical_score", precision = 6, scale = 2)
    private BigDecimal technicalScore;

    @Column(name = "risk_acceptable")
    private Boolean riskAcceptable;

    @Column(name = "suggested_entry", precision = 20, scale = 8)
    private BigDecimal suggestedEntry;

    @Column(name = "suggested_take_profit", precision = 20, scale = 8)
    private BigDecimal suggestedTakeProfit;

    @Column(name = "suggested_stop_loss", precision = 20, scale = 8)
    private BigDecimal suggestedStopLoss;

    @Column(columnDefinition = "TEXT")
    private String reasoning;

    @Column(name = "created_at", updatable = false)
    private Instant createdAt = Instant.now();

    public TradingSignalRecord() {}

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }

    public String getSymbol() { return symbol; }
    public void setSymbol(String symbol) { this.symbol = symbol; }

    public String getTimeframe() { return timeframe; }
    public void setTimeframe(String timeframe) { this.timeframe = timeframe; }

    public Instant getCandleTime() { return candleTime; }
    public void setCandleTime(Instant candleTime) { this.candleTime = candleTime; }

    public String getSignal() { return signal; }
    public void setSignal(String signal) { this.signal = signal; }

    public String getMlPrediction() { return mlPrediction; }
    public void setMlPrediction(String mlPrediction) { this.mlPrediction = mlPrediction; }

    public BigDecimal getProbabilityUp() { return probabilityUp; }
    public void setProbabilityUp(BigDecimal probabilityUp) { this.probabilityUp = probabilityUp; }

    public BigDecimal getProbabilityDown() { return probabilityDown; }
    public void setProbabilityDown(BigDecimal probabilityDown) { this.probabilityDown = probabilityDown; }

    public BigDecimal getProbabilityNeutral() { return probabilityNeutral; }
    public void setProbabilityNeutral(BigDecimal probabilityNeutral) { this.probabilityNeutral = probabilityNeutral; }

    public BigDecimal getTechnicalScore() { return technicalScore; }
    public void setTechnicalScore(BigDecimal technicalScore) { this.technicalScore = technicalScore; }

    public Boolean getRiskAcceptable() { return riskAcceptable; }
    public void setRiskAcceptable(Boolean riskAcceptable) { this.riskAcceptable = riskAcceptable; }

    public BigDecimal getSuggestedEntry() { return suggestedEntry; }
    public void setSuggestedEntry(BigDecimal suggestedEntry) { this.suggestedEntry = suggestedEntry; }

    public BigDecimal getSuggestedTakeProfit() { return suggestedTakeProfit; }
    public void setSuggestedTakeProfit(BigDecimal suggestedTakeProfit) { this.suggestedTakeProfit = suggestedTakeProfit; }

    public BigDecimal getSuggestedStopLoss() { return suggestedStopLoss; }
    public void setSuggestedStopLoss(BigDecimal suggestedStopLoss) { this.suggestedStopLoss = suggestedStopLoss; }

    public String getReasoning() { return reasoning; }
    public void setReasoning(String reasoning) { this.reasoning = reasoning; }

    public Instant getCreatedAt() { return createdAt; }
    public void setCreatedAt(Instant createdAt) { this.createdAt = createdAt; }
}
