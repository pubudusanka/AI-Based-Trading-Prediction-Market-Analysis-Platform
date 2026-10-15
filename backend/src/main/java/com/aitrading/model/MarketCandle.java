package com.aitrading.model;

import jakarta.persistence.*;
import java.math.BigDecimal;
import java.time.Instant;

@Entity
@Table(name = "market_candle", uniqueConstraints = {
    @UniqueConstraint(name = "uq_candle_symbol_tf_open", columnNames = {"symbol_id", "timeframe", "open_time"})
}, indexes = {
    @Index(name = "idx_candle_lookup", columnList = "symbol_id, timeframe, open_time DESC")
})
public class MarketCandle {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "symbol_id", nullable = false)
    private MarketSymbol symbol;

    @Column(nullable = false, length = 10)
    private String timeframe;

    @Column(name = "open_time", nullable = false)
    private Instant openTime;

    @Column(name = "close_time", nullable = false)
    private Instant closeTime;

    @Column(nullable = false, precision = 20, scale = 8)
    private BigDecimal open;

    @Column(nullable = false, precision = 20, scale = 8)
    private BigDecimal high;

    @Column(nullable = false, precision = 20, scale = 8)
    private BigDecimal low;

    @Column(nullable = false, precision = 20, scale = 8)
    private BigDecimal close;

    @Column(nullable = false, precision = 28, scale = 8)
    private BigDecimal volume;

    @Column(name = "quote_volume", nullable = false, precision = 28, scale = 8)
    private BigDecimal quoteVolume;

    @Column(name = "trade_count", nullable = false)
    private Integer tradeCount = 0;

    @Column(name = "created_at", updatable = false)
    private Instant createdAt = Instant.now();

    public MarketCandle() {}

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }

    public MarketSymbol getSymbol() { return symbol; }
    public void setSymbol(MarketSymbol symbol) { this.symbol = symbol; }

    public String getTimeframe() { return timeframe; }
    public void setTimeframe(String timeframe) { this.timeframe = timeframe; }

    public Instant getOpenTime() { return openTime; }
    public void setOpenTime(Instant openTime) { this.openTime = openTime; }

    public Instant getCloseTime() { return closeTime; }
    public void setCloseTime(Instant closeTime) { this.closeTime = closeTime; }

    public BigDecimal getOpen() { return open; }
    public void setOpen(BigDecimal open) { this.open = open; }

    public BigDecimal getHigh() { return high; }
    public void setHigh(BigDecimal high) { this.high = high; }

    public BigDecimal getLow() { return low; }
    public void setLow(BigDecimal low) { this.low = low; }

    public BigDecimal getClose() { return close; }
    public void setClose(BigDecimal close) { this.close = close; }

    public BigDecimal getVolume() { return volume; }
    public void setVolume(BigDecimal volume) { this.volume = volume; }

    public BigDecimal getQuoteVolume() { return quoteVolume; }
    public void setQuoteVolume(BigDecimal quoteVolume) { this.quoteVolume = quoteVolume; }

    public Integer getTradeCount() { return tradeCount; }
    public void setTradeCount(Integer tradeCount) { this.tradeCount = tradeCount; }

    public Instant getCreatedAt() { return createdAt; }
}
