package com.aitrading.controller;

import com.aitrading.dto.IndicatorFeatureDto;
import com.aitrading.dto.MarketStructureDto;
import com.aitrading.dto.PatternFeatureDto;
import com.aitrading.service.FeatureService;
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
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@WebMvcTest(FeatureController.class)
public class FeatureControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @MockBean
    private FeatureService featureService;

    @Test
    void testGetIndicators() throws Exception {
        IndicatorFeatureDto dto = new IndicatorFeatureDto(
            "BTC/USDT",
            "15m",
            Instant.parse("2026-01-01T12:00:00Z"),
            new BigDecimal("55.40"),
            new BigDecimal("50100.00"),
            new BigDecimal("49800.00"),
            new BigDecimal("48500.00"),
            new BigDecimal("12.50"),
            new BigDecimal("10.20"),
            new BigDecimal("250.00"),
            new BigDecimal("28.40"),
            Map.of()
        );

        when(featureService.getLatestIndicators("BTC/USDT", "15m")).thenReturn(Optional.of(dto));

        mockMvc.perform(get("/api/v1/features/indicators")
                .param("symbol", "BTC/USDT")
                .param("timeframe", "15m"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.rsi").value(55.40))
            .andExpect(jsonPath("$.ema200").value(48500.00));
    }

    @Test
    void testGetPatterns() throws Exception {
        PatternFeatureDto dto = new PatternFeatureDto(
            "BTC/USDT",
            "15m",
            Instant.parse("2026-01-01T12:00:00Z"),
            List.of("HAMMER", "BULLISH_ENGULFING"),
            Map.of("HAMMER", 0.85)
        );

        when(featureService.getLatestPatterns("BTC/USDT", "15m")).thenReturn(Optional.of(dto));

        mockMvc.perform(get("/api/v1/features/patterns")
                .param("symbol", "BTC/USDT")
                .param("timeframe", "15m"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.activePatterns[0]").value("HAMMER"));
    }

    @Test
    void testGetMarketStructure() throws Exception {
        MarketStructureDto dto = new MarketStructureDto(
            "BTC/USDT",
            "15m",
            Instant.parse("2026-01-01T12:00:00Z"),
            "BULLISH",
            new BigDecimal("50500.00"),
            new BigDecimal("49200.00"),
            true,
            false,
            "SUPPORT"
        );

        when(featureService.getLatestMarketStructure("BTC/USDT", "15m")).thenReturn(Optional.of(dto));

        mockMvc.perform(get("/api/v1/features/market-structure")
                .param("symbol", "BTC/USDT")
                .param("timeframe", "15m"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.trendDirection").value("BULLISH"))
            .andExpect(jsonPath("$.breakOfStructure").value(true));
    }
}
