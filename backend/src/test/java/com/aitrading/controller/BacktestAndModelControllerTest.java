package com.aitrading.controller;

import com.aitrading.dto.BacktestResultDto;
import com.aitrading.dto.ModelVersionDto;
import com.aitrading.service.BacktestService;
import com.aitrading.service.ModelService;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.test.web.servlet.MockMvc;

import java.math.BigDecimal;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.Optional;

import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@WebMvcTest({BacktestController.class, ModelController.class})
public class BacktestAndModelControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @MockBean
    private BacktestService backtestService;

    @MockBean
    private ModelService modelService;

    @Test
    void testGetBacktestResults() throws Exception {
        BacktestResultDto dto = new BacktestResultDto(
            1L,
            "TRIPLE_BARRIER_V1",
            "BTC_15M_v1.0",
            "BTC/USDT",
            "15m",
            Instant.parse("2026-01-01T00:00:00Z"),
            Instant.parse("2026-02-01T00:00:00Z"),
            new BigDecimal("10000.00"),
            150,
            new BigDecimal("58.60"),
            new BigDecimal("1.85"),
            new BigDecimal("4.20"),
            new BigDecimal("2.10"),
            new BigDecimal("18.40"),
            List.of()
        );

        when(backtestService.getResults("BTC/USDT", 10)).thenReturn(List.of(dto));

        mockMvc.perform(get("/api/v1/backtests/results")
                .param("symbol", "BTC/USDT")
                .param("limit", "10"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$[0].strategyVersion").value("TRIPLE_BARRIER_V1"))
            .andExpect(jsonPath("$[0].sharpeRatio").value(2.10));
    }

    @Test
    void testListModels() throws Exception {
        Map<String, Object> modelMap = Map.of(
            "version", "BTC_15M_RF_v1.0",
            "modelType", "RANDOM_FOREST",
            "status", "PRODUCTION"
        );

        when(modelService.listModels("BTC/USDT", "15m")).thenReturn(List.of(modelMap));

        mockMvc.perform(get("/api/v1/models/list")
                .param("symbol", "BTC/USDT")
                .param("timeframe", "15m"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$[0].version").value("BTC_15M_RF_v1.0"));
    }

    @Test
    void testGetModelMetrics() throws Exception {
        Map<String, Object> metrics = Map.of(
            "version", "BTC_15M_RF_v1.0",
            "rocAuc", 0.68,
            "brierScore", 0.18
        );

        when(modelService.getModelMetrics("BTC_15M_RF_v1.0")).thenReturn(metrics);

        mockMvc.perform(get("/api/v1/models/BTC_15M_RF_v1.0/metrics"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.rocAuc").value(0.68));
    }
}
