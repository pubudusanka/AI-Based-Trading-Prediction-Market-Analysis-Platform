package com.aitrading.service;

import com.aitrading.dto.TradingSignalDto;
import com.aitrading.model.MarketCandle;
import com.aitrading.model.TradingSignalRecord;
import com.aitrading.repository.MarketCandleRepository;
import com.aitrading.repository.MarketSymbolRepository;
import com.aitrading.repository.TradingSignalRepository;
import org.springframework.data.domain.PageRequest;
import org.springframework.stereotype.Service;

import java.math.BigDecimal;
import java.time.Instant;
import java.util.*;

@Service
public class SignalService {

    private final TradingSignalRepository signalRepository;
    private final MarketCandleRepository candleRepository;
    private final MarketSymbolRepository symbolRepository;
    private final MlServiceGateway mlServiceGateway;

    public SignalService(
        TradingSignalRepository signalRepository,
        MarketCandleRepository candleRepository,
        MarketSymbolRepository symbolRepository,
        MlServiceGateway mlServiceGateway
    ) {
        this.signalRepository = signalRepository;
        this.candleRepository = candleRepository;
        this.symbolRepository = symbolRepository;
        this.mlServiceGateway = mlServiceGateway;
    }

    public Optional<TradingSignalDto> getLatestSignal(String symbol, String timeframe) {
        return signalRepository.findTopBySymbolAndTimeframeOrderByCandleTimeDesc(symbol, timeframe)
            .map(this::mapToDto);
    }

    public List<TradingSignalDto> getSignalHistory(String symbol, String timeframe, int limit) {
        return signalRepository.findBySymbolAndTimeframeOrderByCandleTimeDesc(symbol, timeframe, PageRequest.of(0, Math.min(limit, 100)))
            .stream()
            .map(this::mapToDto)
            .toList();
    }

    public Optional<TradingSignalDto> generateSignalLive(String symbol, String timeframe) {
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

                Optional<Map<String, Object>> mlRespOpt = mlServiceGateway.requestSignal(requestPayload);
                if (mlRespOpt.isEmpty()) {
                    return Optional.empty();
                }

                Map<String, Object> resp = mlRespOpt.get();

                TradingSignalRecord record = new TradingSignalRecord();
                record.setSymbol(symbol);
                record.setTimeframe(timeframe);
                record.setCandleTime(Instant.parse((String) resp.get("timestamp")));
                record.setSignal((String) resp.get("signal"));
                record.setMlPrediction((String) resp.get("ml_prediction"));
                record.setProbabilityUp(BigDecimal.valueOf(((Number) resp.get("probability_up")).doubleValue()));
                record.setProbabilityDown(BigDecimal.valueOf(((Number) resp.get("probability_down")).doubleValue()));
                record.setProbabilityNeutral(BigDecimal.valueOf(((Number) resp.get("probability_neutral")).doubleValue()));
                record.setTechnicalScore(BigDecimal.valueOf(((Number) resp.get("technical_score")).doubleValue()));
                record.setRiskAcceptable((Boolean) resp.get("risk_acceptable"));
                record.setSuggestedEntry(BigDecimal.valueOf(((Number) resp.get("suggested_entry")).doubleValue()));
                record.setSuggestedTakeProfit(BigDecimal.valueOf(((Number) resp.get("suggested_take_profit")).doubleValue()));
                record.setSuggestedStopLoss(BigDecimal.valueOf(((Number) resp.get("suggested_stop_loss")).doubleValue()));
                record.setReasoning((String) resp.get("reasoning"));

                TradingSignalRecord saved = signalRepository.save(record);
                return Optional.of(mapToDto(saved));
            });
    }

    private TradingSignalDto mapToDto(TradingSignalRecord r) {
        return new TradingSignalDto(
            r.getId(),
            r.getSymbol(),
            r.getTimeframe(),
            r.getCandleTime(),
            r.getSignal(),
            r.getMlPrediction(),
            r.getProbabilityUp(),
            r.getProbabilityDown(),
            r.getTechnicalScore(),
            r.getRiskAcceptable(),
            r.getSuggestedEntry(),
            r.getSuggestedTakeProfit(),
            r.getSuggestedStopLoss(),
            r.getReasoning()
        );
    }
}
