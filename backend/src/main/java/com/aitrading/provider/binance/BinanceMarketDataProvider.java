package com.aitrading.provider.binance;

import com.aitrading.provider.MarketDataProvider;
import com.aitrading.provider.dto.CandleDto;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClient;

import java.math.BigDecimal;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;

@Component
public class BinanceMarketDataProvider implements MarketDataProvider {

    private static final Logger log = LoggerFactory.getLogger(BinanceMarketDataProvider.class);
    private static final String PROVIDER_NAME = "BINANCE";

    private final RestClient restClient;

    public BinanceMarketDataProvider(
        @Value("${trading.binance.base-url:https://api.binance.com}") String baseUrl
    ) {
        String effectiveUrl = (baseUrl != null && !baseUrl.isBlank()) ? baseUrl : "https://api.binance.com";
        this.restClient = RestClient.builder()
            .baseUrl(effectiveUrl)
            .defaultHeader("User-Agent", "AI-Trading-Prediction-Platform/1.0")
            .build();
    }

    @Override
    public String getProviderName() {
        return PROVIDER_NAME;
    }

    @Override
    public List<CandleDto> fetchHistoricalCandles(
        String symbol,
        String timeframe,
        Instant startTime,
        Instant endTime,
        int limit
    ) {
        String formattedSymbol = symbol.replace("/", "").replace("-", "").toUpperCase();
        int safeLimit = Math.min(Math.max(limit, 1), 1000);

        log.debug("Fetching klines from Binance for {} ({}): start={}, end={}, limit={}",
            formattedSymbol, timeframe, startTime, endTime, safeLimit);

        try {
            var response = restClient.get()
                .uri(uriBuilder -> {
                    var builder = uriBuilder.path("/api/v3/klines")
                        .queryParam("symbol", formattedSymbol)
                        .queryParam("interval", timeframe)
                        .queryParam("limit", safeLimit);
                    if (startTime != null) {
                        builder.queryParam("startTime", startTime.toEpochMilli());
                    }
                    if (endTime != null) {
                        builder.queryParam("endTime", endTime.toEpochMilli());
                    }
                    return builder.build();
                })
                .retrieve()
                .body(new ParameterizedTypeReference<List<List<Object>>>() {});

            if (response == null || response.isEmpty()) {
                return List.of();
            }

            List<CandleDto> candles = new ArrayList<>(response.size());
            for (List<Object> k : response) {
                // k[0]: openTime (Long)
                // k[1]: open (String)
                // k[2]: high (String)
                // k[3]: low (String)
                // k[4]: close (String)
                // k[5]: volume (String)
                // k[6]: closeTime (Long)
                // k[7]: quoteAssetVolume (String)
                // k[8]: numberOfTrades (Integer/Long)
                Instant openTime = Instant.ofEpochMilli(((Number) k.get(0)).longValue());
                Instant closeTime = Instant.ofEpochMilli(((Number) k.get(6)).longValue());
                BigDecimal open = new BigDecimal(k.get(1).toString());
                BigDecimal high = new BigDecimal(k.get(2).toString());
                BigDecimal low = new BigDecimal(k.get(3).toString());
                BigDecimal close = new BigDecimal(k.get(4).toString());
                BigDecimal volume = new BigDecimal(k.get(5).toString());
                BigDecimal quoteVolume = new BigDecimal(k.get(7).toString());
                Integer tradeCount = ((Number) k.get(8)).intValue();

                CandleDto candle = new CandleDto(
                    symbol,
                    PROVIDER_NAME,
                    timeframe,
                    openTime,
                    closeTime,
                    open,
                    high,
                    low,
                    close,
                    volume,
                    quoteVolume,
                    tradeCount
                );

                if (candle.isValid()) {
                    candles.add(candle);
                } else {
                    log.warn("Dropped invalid candle for {}: openTime={}", symbol, openTime);
                }
            }

            return candles;

        } catch (Exception ex) {
            log.error("Failed to fetch klines from Binance: {}", ex.getMessage(), ex);
            throw new RuntimeException("Binance klines fetch failed: " + ex.getMessage(), ex);
        }
    }
}
