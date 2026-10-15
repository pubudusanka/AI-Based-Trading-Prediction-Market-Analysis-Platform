package com.aitrading.model;

import jakarta.persistence.*;
import java.math.BigDecimal;
import java.time.Instant;

@Entity
@Table(name = "feature_snapshot", uniqueConstraints = {
    @UniqueConstraint(name = "uq_feature_candle_version", columnNames = {"candle_id", "feature_version"})
}, indexes = {
    @Index(name = "idx_feature_snapshot_version", columnList = "feature_version, candle_id")
})
public class FeatureSnapshot {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "candle_id", nullable = false)
    private MarketCandle candle;

    @Column(name = "feature_version", nullable = false, length = 50)
    private String featureVersion;

    @Column(precision = 10, scale = 4)
    private BigDecimal rsi;

    @Column(name = "ema_20", precision = 20, scale = 8)
    private BigDecimal ema20;

    @Column(name = "ema_50", precision = 20, scale = 8)
    private BigDecimal ema50;

    @Column(name = "ema_200", precision = 20, scale = 8)
    private BigDecimal ema200;

    @Column(precision = 12, scale = 6)
    private BigDecimal macd;

    @Column(name = "macd_signal", precision = 12, scale = 6)
    private BigDecimal macdSignal;

    @Column(precision = 12, scale = 6)
    private BigDecimal atr;

    @Column(precision = 10, scale = 4)
    private BigDecimal adx;

    @Column(columnDefinition = "TEXT")
    private String features; // JSON string representation

    @Column(name = "created_at", updatable = false)
    private Instant createdAt = Instant.now();

    public FeatureSnapshot() {}

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }

    public MarketCandle getCandle() { return candle; }
    public void setCandle(MarketCandle candle) { this.candle = candle; }

    public String getFeatureVersion() { return featureVersion; }
    public void setFeatureVersion(String featureVersion) { this.featureVersion = featureVersion; }

    public BigDecimal getRsi() { return rsi; }
    public void setRsi(BigDecimal rsi) { this.rsi = rsi; }

    public BigDecimal getEma20() { return ema20; }
    public void setEma20(BigDecimal ema20) { this.ema20 = ema20; }

    public BigDecimal getEma50() { return ema50; }
    public void setEma50(BigDecimal ema50) { this.ema50 = ema50; }

    public BigDecimal getEma200() { return ema200; }
    public void setEma200(BigDecimal ema200) { this.ema200 = ema200; }

    public BigDecimal getMacd() { return macd; }
    public void setMacd(BigDecimal macd) { this.macd = macd; }

    public BigDecimal getMacdSignal() { return macdSignal; }
    public void setMacdSignal(BigDecimal macdSignal) { this.macdSignal = macdSignal; }

    public BigDecimal getAtr() { return atr; }
    public void setAtr(BigDecimal atr) { this.atr = atr; }

    public BigDecimal getAdx() { return adx; }
    public void setAdx(BigDecimal adx) { this.adx = adx; }

    public String getFeatures() { return features; }
    public void setFeatures(String features) { this.features = features; }

    public Instant getCreatedAt() { return createdAt; }
}
