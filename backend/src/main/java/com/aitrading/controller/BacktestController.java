package com.aitrading.controller;

import com.aitrading.dto.BacktestResultDto;
import com.aitrading.service.BacktestService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.math.BigDecimal;
import java.time.Instant;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/v1/backtests")
@CrossOrigin(origins = "*")
public class BacktestController {

    private final BacktestService backtestService;

    public BacktestController(BacktestService backtestService) {
        this.backtestService = backtestService;
    }

    @PostMapping("/run")
    public ResponseEntity<BacktestResultDto> runBacktest(
        @RequestParam(defaultValue = "TRIPLE_BARRIER_V1") String strategyVersion,
        @RequestParam(defaultValue = "BTC_15M_v1.0") String modelVersion,
        @RequestParam(defaultValue = "BTC/USDT") String symbol,
        @RequestParam(defaultValue = "15m") String timeframe,
        @RequestParam(required = false) Long startTimeMs,
        @RequestParam(required = false) Long endTimeMs,
        @RequestParam(defaultValue = "10000.0") BigDecimal initialCapital
    ) {
        Instant start = startTimeMs != null ? Instant.ofEpochMilli(startTimeMs) : null;
        Instant end = endTimeMs != null ? Instant.ofEpochMilli(endTimeMs) : null;

        BacktestResultDto result = backtestService.createBacktestRun(
            strategyVersion,
            modelVersion,
            symbol,
            timeframe,
            start,
            end,
            initialCapital
        );
        return ResponseEntity.ok(result);
    }

    @GetMapping("/results")
    public ResponseEntity<List<BacktestResultDto>> getResults(
        @RequestParam(defaultValue = "BTC/USDT") String symbol,
        @RequestParam(defaultValue = "10") int limit
    ) {
        return ResponseEntity.ok(backtestService.getResults(symbol, limit));
    }

    @GetMapping("/{id}")
    public ResponseEntity<BacktestResultDto> getById(@PathVariable Long id) {
        return backtestService.getBacktestById(id)
            .map(ResponseEntity::ok)
            .orElseGet(() -> ResponseEntity.notFound().build());
    }

    @GetMapping("/{id}/trades")
    public ResponseEntity<List<Map<String, Object>>> getTrades(@PathVariable Long id) {
        return ResponseEntity.ok(backtestService.getBacktestTrades(id));
    }
}
