# Market Data Provider Decision (Phase 2)

**Document Version:** 1.0  
**Status:** Approved  
**Reference Document:** `AI_Trading_Prediction_Platform_A-Z_Implementation_Plan.md` (Section 7)

---

## 1. Provider Evaluation Summary

To support continuous 15-minute historical and real-time data for `BTC/USDT`, several market data providers were evaluated against the criteria defined in the implementation plan:

| Provider | Data Coverage | Rate Limits | Authentication | WebSocket / Realtime | Cost | Fit for V1 |
|---|---|---|---|---|---|---|
| **Binance Public Spot API** | Complete historical Kline/OHLCV from 2017 to present | 1,200 weight/min (very high) | None required for public market data | Yes (`<symbol>@kline_<interval>`) | Free | **Primary Choice (Selected)** |
| **Coinbase Advanced API** | High quality, but historical candle limits per request are smaller (300 candles) | 10 req/sec | Optional/Required for high tiers | Yes | Free | Secondary / Fallback |
| **Kraken API** | Limited historical candle depth in single calls (720 candles) | Strict tier-based rate limits | None for public | Yes | Free | Alternative |
| **Twelve Data / Finnhub** | Cross-asset (Crypto + Stocks) | 8-30 calls/min on free tier (too restrictive for backfilling) | API Key required | Paid | Freemium | Reserved for future stock expansion |

---

## 2. Decision: Binance Spot Public Market Data API

### Rationale:
1. **High Historical Density:** Binance offers up to 1,000 candles per single HTTP call (`GET /api/v3/klines`), enabling rapid and complete backfilling of 1–2 years of 15m data (~35,000–70,000 candles) within minutes without hitting rate limits.
2. **Standardized OHLCV + Execution Metrics:** Each candle record includes exact millisecond open/close timestamps, open, high, low, close, base volume, quote volume, and trade count.
3. **No Financial Barrier / Immediate Reproducibility:** Anyone cloning the repository can ingest the raw dataset immediately without signing up for paid proprietary keys.
4. **Clean WebSocket Migration:** Provides instant live streaming via `wss://stream.binance.com:9443/ws/btcusdt@kline_15m` for Phase 10 / real-time monitoring.

---

## 3. Architecture & Interface Abstraction

To ensure zero vendor lock-in, data ingestion is implemented behind a strict interface contract:

```java
public interface MarketDataProvider {
    List<CandleDto> fetchHistoricalCandles(
        String symbol,
        String timeframe,
        Instant startTime,
        Instant endTime,
        int limit
    );
    
    String getProviderName();
}
```

If another provider or offline CSV source is introduced later, a new implementation of `MarketDataProvider` can be swapped via Spring dependency injection without touching downstream feature pipelines or persistence logic.
