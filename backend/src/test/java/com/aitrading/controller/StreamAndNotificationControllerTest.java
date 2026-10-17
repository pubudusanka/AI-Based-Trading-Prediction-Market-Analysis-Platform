package com.aitrading.controller;

import com.aitrading.service.MarketStreamService;
import com.aitrading.service.NotificationService;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;

import java.util.List;
import java.util.Map;

import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@WebMvcTest(StreamAndNotificationController.class)
class StreamAndNotificationControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @MockBean
    private MarketStreamService streamService;

    @MockBean
    private NotificationService notificationService;

    @Test
    @DisplayName("GET /api/v1/notifications/history returns notification list")
    void getNotificationHistory() throws Exception {
        when(notificationService.getRecentNotifications(10))
            .thenReturn(List.of(Map.of(
                "title", "TEST_ALERT",
                "message", "Test alert notification",
                "timestamp", "2026-01-01T00:00:00Z"
            )));

        mockMvc.perform(get("/api/v1/notifications/history")
                .param("limit", "10")
                .contentType(MediaType.APPLICATION_JSON))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$").isArray())
            .andExpect(jsonPath("$[0].title").value("TEST_ALERT"));
    }

    @Test
    @DisplayName("POST /api/v1/notifications/settings updates alert toggles")
    void updateNotificationSettings() throws Exception {
        when(notificationService.isNotificationsEnabled()).thenReturn(true);
        when(notificationService.getMinConfidenceThreshold()).thenReturn(0.65);

        mockMvc.perform(post("/api/v1/notifications/settings")
                .param("enabled", "true")
                .param("minConfidence", "0.65")
                .contentType(MediaType.APPLICATION_JSON))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.notificationsEnabled").value(true))
            .andExpect(jsonPath("$.minConfidenceThreshold").value(0.65));
    }
}
