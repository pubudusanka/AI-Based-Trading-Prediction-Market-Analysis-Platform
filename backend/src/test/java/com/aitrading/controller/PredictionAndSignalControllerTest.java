package com.aitrading.controller;

import com.aitrading.dto.PredictionDto;
import com.aitrading.dto.TradingSignalDto;
import com.aitrading.service.PredictionService;
import com.aitrading.service.SignalService;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.test.web.servlet.MockMvc;

import java.math.BigDecimal;
import java.time.Instant;
import java.util.List;
import java.util.Optional;

import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@WebMvcTest({PredictionController.class, SignalController.class})
public class PredictionAndSignalControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @MockBean
    private PredictionService predictionService;

    @MockBean
    private SignalService signalService;

    @Test
    void testGetLatestPrediction() throws Exception {
        PredictionDto predDto = new PredictionDto(
            1L,
            "BTC/USDT",
            "15m",
            Instant.parse("2026-01-01T12:00:00Z"),
            "BTC_15M_RF_v1.0",
            "UP",
            new BigDecimal("0.72000"),
            new BigDecimal("0.18000"),
            new BigDecimal("0.10000"),
            List.of(),
            "AI Prediction; not financial advice"
        );

        when(predictionService.getLatestPrediction("BTC/USDT", "15m")).thenReturn(Optional.of(predDto));

        mockMvc.perform(get("/api/v1/predictions/latest")
                .param("symbol", "BTC/USDT")
                .param("timeframe", "15m"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.predictedClass").value("UP"))
            .andExpect(jsonPath("$.probabilityUp").value(0.72));
    }

    @Test
    void testGetLatestSignal() throws Exception {
        TradingSignalDto sigDto = new TradingSignalDto(
            1L,
            "BTC/USDT",
            "15m",
            Instant.parse("2026-01-01T12:00:00Z"),
            "BUY",
            "UP",
            new BigDecimal("0.72"),
            new BigDecimal("0.18"),
            new BigDecimal("78.50"),
            true,
            new BigDecimal("50000.00"),
            new BigDecimal("50500.00"),
            new BigDecimal("49750.00"),
            "Confluence verified"
        );

        when(signalService.getLatestSignal("BTC/USDT", "15m")).thenReturn(Optional.of(sigDto));

        mockMvc.perform(get("/api/v1/signals/latest")
                .param("symbol", "BTC/USDT")
                .param("timeframe", "15m"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.signal").value("BUY"))
            .andExpect(jsonPath("$.technicalScore").value(78.50))
            .andExpect(jsonPath("$.riskAcceptable").value(true));
    }
}
