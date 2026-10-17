package com.aitrading.service;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;

import java.io.IOException;
import java.util.List;
import java.util.Map;
import java.util.concurrent.CopyOnWriteArrayList;

@Service
public class MarketStreamService {

    private static final Logger log = LoggerFactory.getLogger(MarketStreamService.class);
    private static final Long EMITTER_TIMEOUT = 180_000L; // 3 minutes timeout before heartbeat renew

    private final List<SseEmitter> emitters = new CopyOnWriteArrayList<>();

    public SseEmitter subscribe(String symbol, String timeframe) {
        SseEmitter emitter = new SseEmitter(EMITTER_TIMEOUT);

        emitters.add(emitter);

        emitter.onCompletion(() -> {
            log.debug("SSE stream completed for {}:{}", symbol, timeframe);
            emitters.remove(emitter);
        });

        emitter.onTimeout(() -> {
            log.debug("SSE stream timed out for {}:{}", symbol, timeframe);
            emitter.complete();
            emitters.remove(emitter);
        });

        emitter.onError(e -> {
            log.debug("SSE stream error for {}:{}: {}", symbol, timeframe, e.getMessage());
            emitters.remove(emitter);
        });

        // Send initial connection handshake
        try {
            emitter.send(SseEmitter.event()
                .name("connected")
                .data(Map.of(
                    "status", "CONNECTED",
                    "symbol", symbol,
                    "timeframe", timeframe,
                    "message", "Subscribed to live market and signal stream"
                )));
        } catch (IOException e) {
            emitters.remove(emitter);
        }

        return emitter;
    }

    public void broadcastMarketUpdate(Map<String, Object> payload) {
        for (SseEmitter emitter : emitters) {
            try {
                emitter.send(SseEmitter.event()
                    .name("market-update")
                    .data(payload));
            } catch (Exception e) {
                emitters.remove(emitter);
            }
        }
    }

    public int getActiveSubscribersCount() {
        return emitters.size();
    }
}
