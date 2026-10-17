package com.aitrading.service;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

import java.time.Instant;
import java.util.*;
import java.util.concurrent.CopyOnWriteArrayList;

@Service
public class NotificationService {

    private static final Logger log = LoggerFactory.getLogger(NotificationService.class);

    private final List<Map<String, Object>> notificationHistory = new CopyOnWriteArrayList<>();
    private boolean notificationsEnabled = true;
    private double minConfidenceThreshold = 0.55;

    public void setNotificationsEnabled(boolean enabled) {
        this.notificationsEnabled = enabled;
    }

    public boolean isNotificationsEnabled() {
        return notificationsEnabled;
    }

    public void setMinConfidenceThreshold(double threshold) {
        this.minConfidenceThreshold = threshold;
    }

    public double getMinConfidenceThreshold() {
        return minConfidenceThreshold;
    }

    public Optional<Map<String, Object>> dispatchSignalAlert(
        String symbol,
        String timeframe,
        String signal,
        double probUp,
        double technicalScore,
        String modelVersion
    ) {
        if (!notificationsEnabled) {
            log.debug("Notifications are disabled; skipping alert for {}", symbol);
            return Optional.empty();
        }

        if (probUp < minConfidenceThreshold && !"SELL".equalsIgnoreCase(signal)) {
            log.debug("Probability {} below notification threshold {}; skipping alert", probUp, minConfidenceThreshold);
            return Optional.empty();
        }

        // Section 36 formatted notification text
        String formattedMessage = String.format(
            "%s %s\n\nNew %s signal\n\nUP probability: %.0f%%\nTechnical score: %.0f\nModel: %s",
            symbol.replace("/", ""),
            timeframe,
            signal,
            probUp * 100,
            technicalScore,
            modelVersion
        );

        Map<String, Object> notification = Map.of(
            "id", UUID.randomUUID().toString(),
            "timestamp", Instant.now().toString(),
            "symbol", symbol,
            "timeframe", timeframe,
            "signal", signal,
            "probabilityUp", probUp,
            "technicalScore", technicalScore,
            "modelVersion", modelVersion,
            "formattedMessage", formattedMessage
        );

        notificationHistory.add(0, notification);
        if (notificationHistory.size() > 50) {
            notificationHistory.remove(notificationHistory.size() - 1);
        }

        log.info("DISPATCHED TRADING ALERT:\n{}", formattedMessage);
        return Optional.of(notification);
    }

    public List<Map<String, Object>> getRecentNotifications(int limit) {
        return notificationHistory.stream().limit(Math.min(limit, 50)).toList();
    }
}
