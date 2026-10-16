package com.aitrading.controller;

import com.aitrading.dto.MarketStatusDto;
import com.aitrading.model.MarketCandle;
import com.aitrading.model.MarketSymbol;
import com.aitrading.service.MarketService;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.test.web.servlet.MockMvc;

import java.time.Instant;
import java.util.List;

import static org.mockito.ArgumentMatchers.anyInt;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@WebMvcTest(MarketController.class)
public class MarketControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @MockBean
    private MarketService marketService;

    @Test
    void testGetCandles() throws Exception {
        MarketCandle candle = new MarketCandle();
        candle.setTimeframe("15m");
        candle.setOpenTime(Instant.parse("2026-01-01T00:00:00Z"));
        candle.setCloseTime(Instant.parse("2026-01-01T00:15:00Z"));

        when(marketService.getLatestCandles(eq("BTC/USDT"), eq("15m"), anyInt()))
            .thenReturn(List.of(candle));

        mockMvc.perform(get("/api/v1/market/candles")
                .param("symbol", "BTC/USDT")
                .param("timeframe", "15m"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$").isArray())
            .andExpect(jsonPath("$[0].timeframe").value("15m"));
    }

    @Test
    void testGetSymbols() throws Exception {
        MarketSymbol sym = new MarketSymbol("BTC/USDT", "BINANCE", "BTC", "USDT");
        when(marketService.getAllSymbols()).thenReturn(List.of(sym));

        mockMvc.perform(get("/api/v1/market/symbols"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$[0].symbol").value("BTC/USDT"))
            .andExpect(jsonPath("$[0].exchange").value("BINANCE"));
    }

    @Test
    void testGetDataStatus() throws Exception {
        MarketStatusDto statusDto = new MarketStatusDto(
            "BTC/USDT",
            "15m",
            "BINANCE",
            Instant.parse("2026-01-01T12:00:00Z"),
            1000L,
            true,
            "Data pipeline active and up to date"
        );
        when(marketService.getMarketDataStatus("BTC/USDT", "15m")).thenReturn(statusDto);

        mockMvc.perform(get("/api/v1/market/data-status")
                .param("symbol", "BTC/USDT")
                .param("timeframe", "15m"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.symbol").value("BTC/USDT"))
            .andExpect(jsonPath("$.isFresh").value(true))
            .andExpect(jsonPath("$.totalCandles").value(1000));
    }
}
