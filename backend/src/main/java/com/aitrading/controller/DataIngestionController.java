package com.aitrading.controller;

import com.aitrading.model.DataIngestionRun;
import com.aitrading.model.MarketCandle;
import com.aitrading.model.MarketSymbol;
import com.aitrading.repository.DataIngestionRunRepository;
import com.aitrading.repository.MarketCandleRepository;
import com.aitrading.repository.MarketSymbolRepository;
import com.aitrading.service.DataIngestionService;
import org.springframework.data.domain.PageRequest;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.time.Instant;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/v1")
@CrossOrigin(origins = "*")
public class DataIngestionController {

    private final DataIngestionService ingestionService;
    private final MarketCandleRepository candleRepository;
    private final MarketSymbolRepository symbolRepository;
    private final DataIngestionRunRepository runRepository;

    public DataIngestionController(
        DataIngestionService ingestionService,
        MarketCandleRepository candleRepository,
        MarketSymbolRepository symbolRepository,
        DataIngestionRunRepository runRepository
    ) {
        this.ingestionService = ingestionService;
        this.candleRepository = candleRepository;
        this.symbolRepository = symbolRepository;
        this.runRepository = runRepository;
    }

    @PostMapping("/ingestion/backfill")
    public ResponseEntity<DataIngestionRun> triggerBackfill(
        @RequestParam(defaultValue = "BTC/USDT") String symbol,
        @RequestParam(defaultValue = "15m") String timeframe,
        @RequestParam(required = false) Long startTimeMs,
        @RequestParam(required = false) Long endTimeMs
    ) {
        Instant start = startTimeMs != null ? Instant.ofEpochMilli(startTimeMs) : null;
        Instant end = endTimeMs != null ? Instant.ofEpochMilli(endTimeMs) : null;

        DataIngestionRun run = ingestionService.backfillCandles(symbol, timeframe, start, end);
        return ResponseEntity.ok(run);
    }

    @GetMapping("/ingestion/runs")
    public ResponseEntity<List<DataIngestionRun>> getRuns(
        @RequestParam(defaultValue = "BTC/USDT") String symbol,
        @RequestParam(defaultValue = "10") int limit
    ) {
        return ResponseEntity.ok(
            runRepository.findBySymbolOrderByStartedAtDesc(symbol, PageRequest.of(0, limit))
        );
    }

    @GetMapping("/market/candles")
    public ResponseEntity<?> getLatestCandles(
        @RequestParam(defaultValue = "BTC/USDT") String symbol,
        @RequestParam(defaultValue = "15m") String timeframe,
        @RequestParam(defaultValue = "100") int limit
    ) {
        return symbolRepository.findBySymbol(symbol)
            .map(sym -> {
                List<MarketCandle> candles = candleRepository.findLatestCandles(
                    sym.getId(),
                    timeframe,
                    PageRequest.of(0, Math.min(limit, 1000))
                );
                return ResponseEntity.ok(candles);
            })
            .orElseGet(() -> ResponseEntity.ok(List.of()));
    }

    @GetMapping("/market/health")
    public ResponseEntity<Map<String, Object>> health() {
        return ResponseEntity.ok(Map.of(
            "status", "UP",
            "service", "ai-trading-backend",
            "provider", "BINANCE"
        ));
    }
}
