package com.aitrading.controller;

import com.aitrading.dto.IndicatorFeatureDto;
import com.aitrading.dto.MarketStructureDto;
import com.aitrading.dto.PatternFeatureDto;
import com.aitrading.service.FeatureService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/v1/features")
@CrossOrigin(origins = "*")
public class FeatureController {

    private final FeatureService featureService;

    public FeatureController(FeatureService featureService) {
        this.featureService = featureService;
    }

    @GetMapping("/indicators")
    public ResponseEntity<IndicatorFeatureDto> getIndicators(
        @RequestParam(defaultValue = "BTC/USDT") String symbol,
        @RequestParam(defaultValue = "15m") String timeframe
    ) {
        return featureService.getLatestIndicators(symbol, timeframe)
            .map(ResponseEntity::ok)
            .orElseGet(() -> ResponseEntity.noContent().build());
    }

    @GetMapping("/patterns")
    public ResponseEntity<PatternFeatureDto> getPatterns(
        @RequestParam(defaultValue = "BTC/USDT") String symbol,
        @RequestParam(defaultValue = "15m") String timeframe
    ) {
        return featureService.getLatestPatterns(symbol, timeframe)
            .map(ResponseEntity::ok)
            .orElseGet(() -> ResponseEntity.noContent().build());
    }

    @GetMapping("/market-structure")
    public ResponseEntity<MarketStructureDto> getMarketStructure(
        @RequestParam(defaultValue = "BTC/USDT") String symbol,
        @RequestParam(defaultValue = "15m") String timeframe
    ) {
        return featureService.getLatestMarketStructure(symbol, timeframe)
            .map(ResponseEntity::ok)
            .orElseGet(() -> ResponseEntity.noContent().build());
    }
}
