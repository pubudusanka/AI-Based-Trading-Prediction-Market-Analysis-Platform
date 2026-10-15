package com.aitrading.model;

import jakarta.persistence.*;
import java.math.BigDecimal;
import java.time.Instant;

@Entity
@Table(name = "prediction_outcome", indexes = {
    @Index(name = "idx_outcome_prediction", columnList = "prediction_id")
})
public class PredictionOutcome {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "prediction_id", nullable = false)
    private Prediction prediction;

    @Column(name = "future_return", precision = 10, scale = 6)
    private BigDecimal futureReturn;

    @Column(name = "maximum_favorable_excursion", precision = 10, scale = 6)
    private BigDecimal maximumFavorableExcursion;

    @Column(name = "maximum_adverse_excursion", precision = 10, scale = 6)
    private BigDecimal maximumAdverseExcursion;

    @Column(name = "actual_class", length = 10)
    private String actualClass;

    @Column(name = "target_hit")
    private Boolean targetHit;

    @Column(name = "stop_hit")
    private Boolean stopHit;

    @Column(name = "evaluated_at")
    private Instant evaluatedAt = Instant.now();

    public PredictionOutcome() {}

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }

    public Prediction getPrediction() { return prediction; }
    public void setPrediction(Prediction prediction) { this.prediction = prediction; }

    public BigDecimal getFutureReturn() { return futureReturn; }
    public void setFutureReturn(BigDecimal futureReturn) { this.futureReturn = futureReturn; }

    public BigDecimal getMaximumFavorableExcursion() { return maximumFavorableExcursion; }
    public void setMaximumFavorableExcursion(BigDecimal maximumFavorableExcursion) { this.maximumFavorableExcursion = maximumFavorableExcursion; }

    public BigDecimal getMaximumAdverseExcursion() { return maximumAdverseExcursion; }
    public void setMaximumAdverseExcursion(BigDecimal maximumAdverseExcursion) { this.maximumAdverseExcursion = maximumAdverseExcursion; }

    public String getActualClass() { return actualClass; }
    public void setActualClass(String actualClass) { this.actualClass = actualClass; }

    public Boolean getTargetHit() { return targetHit; }
    public void setTargetHit(Boolean targetHit) { this.targetHit = targetHit; }

    public Boolean getStopHit() { return stopHit; }
    public void setStopHit(Boolean stopHit) { this.stopHit = stopHit; }

    public Instant getEvaluatedAt() { return evaluatedAt; }
    public void setEvaluatedAt(Instant evaluatedAt) { this.evaluatedAt = evaluatedAt; }
}
