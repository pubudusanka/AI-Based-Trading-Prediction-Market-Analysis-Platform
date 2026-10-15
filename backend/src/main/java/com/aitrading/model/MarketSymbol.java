package com.aitrading.model;

import jakarta.persistence.*;
import java.time.Instant;

@Entity
@Table(name = "market_symbol", uniqueConstraints = {
    @UniqueConstraint(name = "uq_symbol_exchange", columnNames = {"symbol", "exchange"})
})
public class MarketSymbol {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Integer id;

    @Column(nullable = false, length = 32)
    private String symbol;

    @Column(nullable = false, length = 32)
    private String exchange = "BINANCE";

    @Column(name = "asset_type", nullable = false, length = 32)
    private String assetType = "CRYPTO";

    @Column(name = "base_asset", nullable = false, length = 16)
    private String baseAsset;

    @Column(name = "quote_asset", nullable = false, length = 16)
    private String quoteAsset;

    @Column(nullable = false)
    private Boolean active = true;

    @Column(name = "created_at", updatable = false)
    private Instant createdAt = Instant.now();

    public MarketSymbol() {}

    public MarketSymbol(String symbol, String exchange, String baseAsset, String quoteAsset) {
        this.symbol = symbol;
        this.exchange = exchange;
        this.baseAsset = baseAsset;
        this.quoteAsset = quoteAsset;
    }

    public Integer getId() { return id; }
    public void setId(Integer id) { this.id = id; }

    public String getSymbol() { return symbol; }
    public void setSymbol(String symbol) { this.symbol = symbol; }

    public String getExchange() { return exchange; }
    public void setExchange(String exchange) { this.exchange = exchange; }

    public String getAssetType() { return assetType; }
    public void setAssetType(String assetType) { this.assetType = assetType; }

    public String getBaseAsset() { return baseAsset; }
    public void setBaseAsset(String baseAsset) { this.baseAsset = baseAsset; }

    public String getQuoteAsset() { return quoteAsset; }
    public void setQuoteAsset(String quoteAsset) { this.quoteAsset = quoteAsset; }

    public Boolean getActive() { return active; }
    public void setActive(Boolean active) { this.active = active; }

    public Instant getCreatedAt() { return createdAt; }
}
