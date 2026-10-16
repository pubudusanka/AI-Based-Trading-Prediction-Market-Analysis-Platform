package com.aitrading.controller;

import com.aitrading.dto.TradingSignalDto;
import com.aitrading.service.SignalService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/v1/signals")
@CrossOrigin(origins = "*")
public class SignalController {

    private final SignalService signalService;

    public SignalController(SignalService signalService) {
        this.signalService = signalService;
    }

    @GetMapping("/latest")
    public ResponseEntity<TradingSignalDto> getLatest(
        @RequestParam(defaultValue = "BTC/USDT") String symbol,
        @RequestParam(defaultValue = "15m") String timeframe
    ) {
        return signalService.getLatestSignal(symbol, timeframe)
            .map(ResponseEntity::ok)
            .orElseGet(() -> ResponseEntity.noContent().build());
    }

    @GetMapping("/history")
    public ResponseEntity<List<TradingSignalDto>> getHistory(
        @RequestParam(defaultValue = "BTC/USDT") String symbol,
        @RequestParam(defaultValue = "15m") String timeframe,
        @RequestParam(defaultValue = "50") int limit
    ) {
        return ResponseEntity.ok(signalService.getSignalHistory(symbol, timeframe, limit));
    }

    @PostMapping("/generate")
    public ResponseEntity<TradingSignalDto> generateSignal(
        @RequestParam(defaultValue = "BTC/USDT") String symbol,
        @RequestParam(defaultValue = "15m") String timeframe
    ) {
        return signalService.generateSignalLive(symbol, timeframe)
            .map(ResponseEntity::ok)
            .orElseGet(() -> ResponseEntity.badRequest().build());
    }
}
