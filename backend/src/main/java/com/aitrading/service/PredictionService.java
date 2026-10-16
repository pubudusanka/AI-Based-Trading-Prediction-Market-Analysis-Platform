package com.aitrading.service;

import com.aitrading.dto.PredictionDto;
import com.aitrading.model.MarketCandle;
import com.aitrading.model.Prediction;
import com.aitrading.repository.MarketCandleRepository;
import com.aitrading.repository.MarketSymbolRepository;
import com.aitrading.repository.PredictionRepository;
import org.springframework.data.domain.PageRequest;
import org.springframework.stereotype.Service;

import java.math.BigDecimal;
import java.time.Instant;
import java.util.*;

@Service
public class PredictionService {

    private final PredictionRepository predictionRepository;
    private final MarketCandleRepository candleRepository;
    private final MarketSymbolRepository symbolRepository;
    private final MlServiceGateway mlServiceGateway;

    public PredictionService(
        PredictionRepository predictionRepository,
        MarketCandleRepository candleRepository,
        MarketSymbolRepository symbolRepository,
        MlServiceGateway mlServiceGateway
    ) {
        this.predictionRepository = predictionRepository;
        this.candleRepository = candleRepository;
        this.symbolRepository = symbolRepository;
        this.mlServiceGateway = mlServiceGateway;
    }

    public Optional<PredictionDto> getLatestPrediction(String symbol, String timeframe) {
        return predictionRepository.findTopBySymbolAndTimeframeOrderByCandleTimeDesc(symbol, timeframe)
            .map(this::mapToDto);
    }

    public List<PredictionDto> getPredictionHistory(String symbol, String timeframe, int limit) {
        return predictionRepository.findBySymbolAndTimeframeOrderByCandleTimeDesc(symbol, timeframe, PageRequest.of(0, Math.min(limit, 100)))
            .stream()
            .map(this::mapToDto)
            .toList();
    }

    public Optional<PredictionDto> getPredictionById(Long id) {
        if (id == null) {
            return Optional.empty();
        }
        return predictionRepository.findById(id).map(this::mapToDto);
    }

    @SuppressWarnings("unchecked")
    public Optional<PredictionDto> predictLive(String symbol, String timeframe) {
        return symbolRepository.findBySymbol(symbol)
            .flatMap(sym -> {
                List<MarketCandle> candles = candleRepository.findLatestCandles(sym.getId(), timeframe, PageRequest.of(0, 40));
                if (candles.size() < 30) {
                    return Optional.empty();
                }

                List<MarketCandle> chronCandles = new ArrayList<>(candles);
                Collections.reverse(chronCandles);

                List<Map<String, Object>> candleList = new ArrayList<>();
                for (MarketCandle c : chronCandles) {
                    Map<String, Object> map = new HashMap<>();
                    map.put("open_time", c.getOpenTime().toString());
                    map.put("open", c.getOpen().doubleValue());
                    map.put("high", c.getHigh().doubleValue());
                    map.put("low", c.getLow().doubleValue());
                    map.put("close", c.getClose().doubleValue());
                    map.put("volume", c.getVolume().doubleValue());
                    candleList.add(map);
                }

                Map<String, Object> requestPayload = Map.of(
                    "symbol", symbol,
                    "timeframe", timeframe,
                    "candles", candleList
                );

                Optional<Map<String, Object>> mlRespOpt = mlServiceGateway.requestPrediction(requestPayload);
                if (mlRespOpt.isEmpty()) {
                    return Optional.empty();
                }

                Map<String, Object> resp = mlRespOpt.get();

                // Persist prediction to database
                Prediction entity = new Prediction();
                entity.setSymbol(symbol);
                entity.setTimeframe(timeframe);
                entity.setCandleTime(Instant.parse((String) resp.get("candleTime")));
                entity.setModelVersion((String) resp.get("modelVersion"));
                entity.setFeatureVersion("V1");
                entity.setProbabilityUp(BigDecimal.valueOf(((Number) resp.get("probabilityUp")).doubleValue()));
                entity.setProbabilityDown(BigDecimal.valueOf(((Number) resp.get("probabilityDown")).doubleValue()));
                entity.setProbabilityNeutral(BigDecimal.valueOf(((Number) resp.get("probabilityNeutral")).doubleValue()));
                entity.setPredictedClass((String) resp.get("prediction"));

                Prediction saved = predictionRepository.save(entity);

                List<Map<String, Object>> factors = resp.containsKey("topFactors")
                    ? (List<Map<String, Object>>) resp.get("topFactors")
                    : List.of();

                return Optional.of(new PredictionDto(
                    saved.getId(),
                    saved.getSymbol(),
                    saved.getTimeframe(),
                    saved.getCandleTime(),
                    saved.getModelVersion(),
                    saved.getPredictedClass(),
                    saved.getProbabilityUp(),
                    saved.getProbabilityDown(),
                    saved.getProbabilityNeutral(),
                    factors,
                    (String) resp.getOrDefault("disclaimer", "AI Prediction; not financial advice")
                ));
            });
    }

    private PredictionDto mapToDto(Prediction p) {
        return new PredictionDto(
            p.getId(),
            p.getSymbol(),
            p.getTimeframe(),
            p.getCandleTime(),
            p.getModelVersion(),
            p.getPredictedClass(),
            p.getProbabilityUp(),
            p.getProbabilityDown(),
            p.getProbabilityNeutral(),
            List.of(),
            "AI Prediction; not financial advice"
        );
    }
}
