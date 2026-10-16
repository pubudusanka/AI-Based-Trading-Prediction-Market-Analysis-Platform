package com.aitrading.service;

import com.aitrading.dto.IndicatorFeatureDto;
import com.aitrading.dto.MarketStructureDto;
import com.aitrading.dto.PatternFeatureDto;
import com.aitrading.model.FeatureSnapshot;
import com.aitrading.model.MarketCandle;
import com.aitrading.repository.FeatureSnapshotRepository;
import com.aitrading.repository.MarketCandleRepository;
import com.aitrading.repository.MarketSymbolRepository;
import org.springframework.data.domain.PageRequest;
import org.springframework.stereotype.Service;

import java.math.BigDecimal;
import java.util.*;

@Service
public class FeatureService {

    private final FeatureSnapshotRepository featureSnapshotRepository;
    private final MarketCandleRepository candleRepository;
    private final MarketSymbolRepository symbolRepository;

    public FeatureService(
        FeatureSnapshotRepository featureSnapshotRepository,
        MarketCandleRepository candleRepository,
        MarketSymbolRepository symbolRepository
    ) {
        this.featureSnapshotRepository = featureSnapshotRepository;
        this.candleRepository = candleRepository;
        this.symbolRepository = symbolRepository;
    }

    public Optional<IndicatorFeatureDto> getLatestIndicators(String symbolStr, String timeframe) {
        Optional<MarketCandle> latestCandle = getLatestCandle(symbolStr, timeframe);
        if (latestCandle.isEmpty()) {
            return Optional.empty();
        }

        MarketCandle candle = latestCandle.get();
        // Check if feature snapshot exists for this candle
        Optional<FeatureSnapshot> snapOpt = featureSnapshotRepository.findByCandleAndFeatureVersion(candle, "V1");
        if (snapOpt.isPresent()) {
            FeatureSnapshot snap = snapOpt.get();
            return Optional.of(new IndicatorFeatureDto(
                symbolStr,
                timeframe,
                candle.getOpenTime(),
                snap.getRsi(),
                snap.getEma20(),
                snap.getEma50(),
                snap.getEma200(),
                snap.getMacd(),
                snap.getMacdSignal(),
                snap.getAtr(),
                snap.getAdx(),
                Map.of("featureVersion", snap.getFeatureVersion())
            ));
        }

        // Return fallback derived directly from candle price levels if no snapshot persisted yet
        BigDecimal close = candle.getClose();
        return Optional.of(new IndicatorFeatureDto(
            symbolStr,
            timeframe,
            candle.getOpenTime(),
            new BigDecimal("50.0"), // Neutral RSI
            close,
            close,
            close,
            BigDecimal.ZERO,
            BigDecimal.ZERO,
            candle.getHigh().subtract(candle.getLow()),
            new BigDecimal("20.0"),
            Map.of("status", "live_candle_estimate")
        ));
    }

    public Optional<PatternFeatureDto> getLatestPatterns(String symbolStr, String timeframe) {
        Optional<MarketCandle> latestCandle = getLatestCandle(symbolStr, timeframe);
        if (latestCandle.isEmpty()) {
            return Optional.empty();
        }

        MarketCandle candle = latestCandle.get();
        List<String> patterns = new ArrayList<>();
        Map<String, Double> conf = new HashMap<>();

        BigDecimal body = candle.getClose().subtract(candle.getOpen()).abs();
        BigDecimal range = candle.getHigh().subtract(candle.getLow());

        // Basic heuristic detection for live visualization when DB snapshot is pending
        if (range.compareTo(BigDecimal.ZERO) > 0) {
            double ratio = body.doubleValue() / range.doubleValue();
            if (ratio < 0.1) {
                patterns.add("DOJI");
                conf.put("DOJI", 0.85);
            } else if (candle.getClose().compareTo(candle.getOpen()) > 0) {
                patterns.add("BULLISH_CANDLE");
                conf.put("BULLISH_CANDLE", 0.75);
            } else {
                patterns.add("BEARISH_CANDLE");
                conf.put("BEARISH_CANDLE", 0.75);
            }
        }

        return Optional.of(new PatternFeatureDto(
            symbolStr,
            timeframe,
            candle.getOpenTime(),
            patterns,
            conf
        ));
    }

    public Optional<MarketStructureDto> getLatestMarketStructure(String symbolStr, String timeframe) {
        Optional<MarketCandle> latestCandle = getLatestCandle(symbolStr, timeframe);
        if (latestCandle.isEmpty()) {
            return Optional.empty();
        }

        MarketCandle candle = latestCandle.get();
        return Optional.of(new MarketStructureDto(
            symbolStr,
            timeframe,
            candle.getOpenTime(),
            "BULLISH",
            candle.getHigh(),
            candle.getLow(),
            false,
            false,
            "SUPPORT"
        ));
    }

    private Optional<MarketCandle> getLatestCandle(String symbolStr, String timeframe) {
        return symbolRepository.findBySymbol(symbolStr)
            .flatMap(sym -> {
                List<MarketCandle> candles = candleRepository.findLatestCandles(sym.getId(), timeframe, PageRequest.of(0, 1));
                return candles.isEmpty() ? Optional.empty() : Optional.of(candles.get(0));
            });
    }
}
