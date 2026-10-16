package com.aitrading.service;

import com.aitrading.dto.MarketStatusDto;
import com.aitrading.model.MarketCandle;
import com.aitrading.model.MarketSymbol;
import com.aitrading.repository.MarketCandleRepository;
import com.aitrading.repository.MarketSymbolRepository;
import org.springframework.data.domain.PageRequest;
import org.springframework.stereotype.Service;

import java.time.Duration;
import java.time.Instant;
import java.util.List;
import java.util.Optional;

@Service
public class MarketService {

    private final MarketCandleRepository candleRepository;
    private final MarketSymbolRepository symbolRepository;

    public MarketService(
        MarketCandleRepository candleRepository,
        MarketSymbolRepository symbolRepository
    ) {
        this.candleRepository = candleRepository;
        this.symbolRepository = symbolRepository;
    }

    public List<MarketCandle> getLatestCandles(String symbolStr, String timeframe, int limit) {
        return symbolRepository.findBySymbol(symbolStr)
            .map(sym -> candleRepository.findLatestCandles(sym.getId(), timeframe, PageRequest.of(0, Math.min(limit, 2000))))
            .orElseGet(List::of);
    }

    public List<MarketSymbol> getAllSymbols() {
        return symbolRepository.findAll();
    }

    public MarketStatusDto getMarketDataStatus(String symbolStr, String timeframe) {
        Optional<MarketSymbol> symOpt = symbolRepository.findBySymbol(symbolStr);
        if (symOpt.isEmpty()) {
            return new MarketStatusDto(
                symbolStr,
                timeframe,
                "UNKNOWN",
                null,
                0L,
                false,
                "Symbol " + symbolStr + " not found in local database"
            );
        }

        MarketSymbol sym = symOpt.get();
        Optional<Instant> maxTimeOpt = candleRepository.findMaxOpenTime(sym.getId(), timeframe);
        long count = candleRepository.count();

        Instant latestTime = maxTimeOpt.orElse(null);
        boolean isFresh = false;
        String message = "No candle data available";

        if (latestTime != null) {
            Duration age = Duration.between(latestTime, Instant.now());
            // For 15m timeframe, fresh if age is within 3 hours
            isFresh = age.toMinutes() <= 180;
            message = isFresh ? "Data pipeline active and up to date" : "Data delayed. Last candle: " + latestTime;
        }

        return new MarketStatusDto(
            sym.getSymbol(),
            timeframe,
            sym.getExchange(),
            latestTime,
            count,
            isFresh,
            message
        );
    }
}
