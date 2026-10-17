package com.aitrading.controller;

import com.aitrading.service.MarketStreamService;
import com.aitrading.service.NotificationService;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/v1")
@CrossOrigin(origins = "*")
public class StreamAndNotificationController {

    private final MarketStreamService streamService;
    private final NotificationService notificationService;

    public StreamAndNotificationController(
        MarketStreamService streamService,
        NotificationService notificationService
    ) {
        this.streamService = streamService;
        this.notificationService = notificationService;
    }

    @GetMapping(value = "/stream/market", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
    public SseEmitter streamMarket(
        @RequestParam(defaultValue = "BTC/USDT") String symbol,
        @RequestParam(defaultValue = "15m") String timeframe
    ) {
        return streamService.subscribe(symbol, timeframe);
    }

    @GetMapping("/notifications/history")
    public ResponseEntity<List<Map<String, Object>>> getNotificationHistory(
        @RequestParam(defaultValue = "20") int limit
    ) {
        return ResponseEntity.ok(notificationService.getRecentNotifications(limit));
    }

    @PostMapping("/notifications/settings")
    public ResponseEntity<Map<String, Object>> updateNotificationSettings(
        @RequestParam(required = false) Boolean enabled,
        @RequestParam(required = false) Double minConfidence
    ) {
        if (enabled != null) {
            notificationService.setNotificationsEnabled(enabled);
        }
        if (minConfidence != null) {
            notificationService.setMinConfidenceThreshold(minConfidence);
        }

        return ResponseEntity.ok(Map.of(
            "notificationsEnabled", notificationService.isNotificationsEnabled(),
            "minConfidenceThreshold", notificationService.getMinConfidenceThreshold()
        ));
    }
}
