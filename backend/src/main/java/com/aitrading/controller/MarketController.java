package com.aitrading.controller;

import com.aitrading.dto.MarketStatusDto;
import com.aitrading.model.MarketCandle;
import com.aitrading.model.MarketSymbol;
import com.aitrading.service.MarketService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/v1/market")
@CrossOrigin(origins = "*")
public class MarketController {

    private final MarketService marketService;

    public MarketController(MarketService marketService) {
        this.marketService = marketService;
    }

    @GetMapping("/candles")
    public ResponseEntity<List<MarketCandle>> getCandles(
        @RequestParam(defaultValue = "BTC/USDT") String symbol,
        @RequestParam(defaultValue = "15m") String timeframe,
        @RequestParam(defaultValue = "100") int limit
    ) {
        return ResponseEntity.ok(marketService.getLatestCandles(symbol, timeframe, limit));
    }

    @GetMapping("/symbols")
    public ResponseEntity<List<MarketSymbol>> getSymbols() {
        return ResponseEntity.ok(marketService.getAllSymbols());
    }

    @GetMapping("/data-status")
    public ResponseEntity<MarketStatusDto> getDataStatus(
        @RequestParam(defaultValue = "BTC/USDT") String symbol,
        @RequestParam(defaultValue = "15m") String timeframe
    ) {
        return ResponseEntity.ok(marketService.getMarketDataStatus(symbol, timeframe));
    }
}
