package com.aitrading.controller;

import com.aitrading.dto.PredictionDto;
import com.aitrading.service.PredictionService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/v1/predictions")
@CrossOrigin(origins = "*")
public class PredictionController {

    private final PredictionService predictionService;

    public PredictionController(PredictionService predictionService) {
        this.predictionService = predictionService;
    }

    @GetMapping("/latest")
    public ResponseEntity<PredictionDto> getLatest(
        @RequestParam(defaultValue = "BTC/USDT") String symbol,
        @RequestParam(defaultValue = "15m") String timeframe
    ) {
        return predictionService.getLatestPrediction(symbol, timeframe)
            .map(ResponseEntity::ok)
            .orElseGet(() -> ResponseEntity.noContent().build());
    }

    @GetMapping("/history")
    public ResponseEntity<List<PredictionDto>> getHistory(
        @RequestParam(defaultValue = "BTC/USDT") String symbol,
        @RequestParam(defaultValue = "15m") String timeframe,
        @RequestParam(defaultValue = "50") int limit
    ) {
        return ResponseEntity.ok(predictionService.getPredictionHistory(symbol, timeframe, limit));
    }

    @GetMapping("/{id}")
    public ResponseEntity<PredictionDto> getById(@PathVariable Long id) {
        return predictionService.getPredictionById(id)
            .map(ResponseEntity::ok)
            .orElseGet(() -> ResponseEntity.notFound().build());
    }

    @PostMapping("/predict")
    public ResponseEntity<PredictionDto> predictLive(
        @RequestParam(defaultValue = "BTC/USDT") String symbol,
        @RequestParam(defaultValue = "15m") String timeframe
    ) {
        return predictionService.predictLive(symbol, timeframe)
            .map(ResponseEntity::ok)
            .orElseGet(() -> ResponseEntity.badRequest().build());
    }
}
