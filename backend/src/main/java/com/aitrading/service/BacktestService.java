package com.aitrading.service;

import com.aitrading.dto.BacktestResultDto;
import com.aitrading.model.BacktestRun;
import com.aitrading.repository.BacktestRunRepository;
import org.springframework.data.domain.PageRequest;
import org.springframework.stereotype.Service;

import java.math.BigDecimal;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.Optional;

@Service
public class BacktestService {

    private final BacktestRunRepository backtestRunRepository;

    public BacktestService(BacktestRunRepository backtestRunRepository) {
        this.backtestRunRepository = backtestRunRepository;
    }

    public List<BacktestResultDto> getResults(String symbol, int limit) {
        return backtestRunRepository.findBySymbolOrderByCreatedAtDesc(symbol, PageRequest.of(0, Math.min(limit, 50)))
            .stream()
            .map(this::mapToDto)
            .toList();
    }

    public Optional<BacktestResultDto> getBacktestById(Long id) {
        if (id == null) {
            return Optional.empty();
        }
        return backtestRunRepository.findById(id).map(this::mapToDto);
    }

    public BacktestResultDto createBacktestRun(
        String strategyVersion,
        String modelVersion,
        String symbol,
        String timeframe,
        Instant startTime,
        Instant endTime,
        BigDecimal initialCapital
    ) {
        BacktestRun run = new BacktestRun();
        run.setStrategyVersion(strategyVersion);
        run.setModelVersion(modelVersion);
        run.setSymbol(symbol);
        run.setTimeframe(timeframe);
        run.setStartTime(startTime != null ? startTime : Instant.now().minusSeconds(86400 * 30));
        run.setEndTime(endTime != null ? endTime : Instant.now());
        run.setInitialCapital(initialCapital != null ? initialCapital : new BigDecimal("10000.0000"));
        run.setTotalTrades(0);
        run.setWinRate(BigDecimal.ZERO);
        run.setProfitFactor(BigDecimal.ZERO);
        run.setMaxDrawdown(BigDecimal.ZERO);
        run.setSharpeRatio(BigDecimal.ZERO);
        run.setTotalReturn(BigDecimal.ZERO);

        BacktestRun saved = backtestRunRepository.save(run);
        return mapToDto(saved);
    }

    public List<Map<String, Object>> getBacktestTrades(Long id) {
        // Return structured sample/completed trades for visualization
        return List.of(
            Map.of(
                "tradeId", "TRD_00001",
                "backtestId", id,
                "symbol", "BTC/USDT",
                "side", "BUY",
                "outcome", "WIN",
                "netPnl", 98.50,
                "exitReason", "TAKE_PROFIT"
            )
        );
    }

    private BacktestResultDto mapToDto(BacktestRun r) {
        return new BacktestResultDto(
            r.getId(),
            r.getStrategyVersion(),
            r.getModelVersion(),
            r.getSymbol(),
            r.getTimeframe(),
            r.getStartTime(),
            r.getEndTime(),
            r.getInitialCapital(),
            r.getTotalTrades(),
            r.getWinRate(),
            r.getProfitFactor(),
            r.getMaxDrawdown(),
            r.getSharpeRatio(),
            r.getTotalReturn(),
            List.of()
        );
    }
}
