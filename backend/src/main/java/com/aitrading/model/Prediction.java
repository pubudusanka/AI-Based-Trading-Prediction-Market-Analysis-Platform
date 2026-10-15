package com.aitrading.model;

import jakarta.persistence.*;
import java.math.BigDecimal;
import java.time.Instant;

@Entity
@Table(name = "prediction", indexes = {
    @Index(name = "idx_prediction_time", columnList = "symbol, timeframe, candle_time DESC")
})
public class Prediction {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false, length = 32)
    private String symbol;

    @Column(nullable = false, length = 10)
    private String timeframe;

    @Column(name = "candle_time", nullable = false)
    private Instant candleTime;

    @Column(name = "model_version", nullable = false, length = 50)
    private String modelVersion;

    @Column(name = "feature_version", nullable = false, length = 50)
    private String featureVersion;

    @Column(name = "probability_up", nullable = false, precision = 6, scale = 5)
    private BigDecimal probabilityUp;

    @Column(name = "probability_down", nullable = false, precision = 6, scale = 5)
    private BigDecimal probabilityDown;

    @Column(name = "probability_neutral", nullable = false, precision = 6, scale = 5)
    private BigDecimal probabilityNeutral;

    @Column(name = "predicted_class", nullable = false, length = 10)
    private String predictedClass;

    @Column(name = "created_at", updatable = false)
    private Instant createdAt = Instant.now();

    public Prediction() {}

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }

    public String getSymbol() { return symbol; }
    public void setSymbol(String symbol) { this.symbol = symbol; }

    public String getTimeframe() { return timeframe; }
    public void setTimeframe(String timeframe) { this.timeframe = timeframe; }

    public Instant getCandleTime() { return candleTime; }
    public void setCandleTime(Instant candleTime) { this.candleTime = candleTime; }

    public String getModelVersion() { return modelVersion; }
    public void setModelVersion(String modelVersion) { this.modelVersion = modelVersion; }

    public String getFeatureVersion() { return featureVersion; }
    public void setFeatureVersion(String featureVersion) { this.featureVersion = featureVersion; }

    public BigDecimal getProbabilityUp() { return probabilityUp; }
    public void setProbabilityUp(BigDecimal probabilityUp) { this.probabilityUp = probabilityUp; }

    public BigDecimal getProbabilityDown() { return probabilityDown; }
    public void setProbabilityDown(BigDecimal probabilityDown) { this.probabilityDown = probabilityDown; }

    public BigDecimal getProbabilityNeutral() { return probabilityNeutral; }
    public void setProbabilityNeutral(BigDecimal probabilityNeutral) { this.probabilityNeutral = probabilityNeutral; }

    public String getPredictedClass() { return predictedClass; }
    public void setPredictedClass(String predictedClass) { this.predictedClass = predictedClass; }

    public Instant getCreatedAt() { return createdAt; }
}
