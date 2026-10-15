package com.aitrading.service;

import com.aitrading.model.DataIngestionRun;
import com.aitrading.model.MarketCandle;
import com.aitrading.model.MarketSymbol;
import com.aitrading.provider.MarketDataProvider;
import com.aitrading.provider.dto.CandleDto;
import com.aitrading.repository.DataIngestionRunRepository;
import com.aitrading.repository.MarketCandleRepository;
import com.aitrading.repository.MarketSymbolRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.Instant;
import java.util.ArrayList;
import java.util.List;

@Service
public class DataIngestionService {

    private static final Logger log = LoggerFactory.getLogger(DataIngestionService.class);

    private final MarketDataProvider marketDataProvider;
    private final MarketSymbolRepository symbolRepository;
    private final MarketCandleRepository candleRepository;
    private final DataIngestionRunRepository runRepository;

    public DataIngestionService(
        MarketDataProvider marketDataProvider,
        MarketSymbolRepository symbolRepository,
        MarketCandleRepository candleRepository,
        DataIngestionRunRepository runRepository
    ) {
        this.marketDataProvider = marketDataProvider;
        this.symbolRepository = symbolRepository;
        this.candleRepository = candleRepository;
        this.runRepository = runRepository;
    }

    @Transactional
    public DataIngestionRun backfillCandles(
        String symbolStr,
        String timeframe,
        Instant startTime,
        Instant endTime
    ) {
        MarketSymbol symbol = symbolRepository.findBySymbol(symbolStr)
            .orElseGet(() -> {
                String[] parts = symbolStr.split("[/_-]");
                String base = parts.length > 0 ? parts[0] : symbolStr;
                String quote = parts.length > 1 ? parts[1] : "USDT";
                return symbolRepository.save(new MarketSymbol(symbolStr, marketDataProvider.getProviderName(), base, quote));
            });

        DataIngestionRun run = new DataIngestionRun();
        run.setProvider(marketDataProvider.getProviderName());
        run.setSymbol(symbolStr);
        run.setTimeframe(timeframe);
        run.setStartTime(startTime != null ? startTime : Instant.EPOCH);
        run.setEndTime(endTime != null ? endTime : Instant.now());
        run.setStatus(DataIngestionRun.Status.RUNNING);
        run = runRepository.save(run);

        int totalReceived = 0;
        int totalInserted = 0;
        Instant currentStart = startTime;

        try {
            while (true) {
                List<CandleDto> batch = marketDataProvider.fetchHistoricalCandles(
                    symbolStr,
                    timeframe,
                    currentStart,
                    endTime,
                    1000
                );

                if (batch.isEmpty()) {
                    break;
                }

                totalReceived += batch.size();
                List<MarketCandle> toInsert = new ArrayList<>();

                for (CandleDto dto : batch) {
                    boolean exists = candleRepository.existsBySymbolAndTimeframeAndOpenTime(
                        symbol,
                        timeframe,
                        dto.openTime()
                    );

                    if (!exists) {
                        MarketCandle entity = new MarketCandle();
                        entity.setSymbol(symbol);
                        entity.setTimeframe(timeframe);
                        entity.setOpenTime(dto.openTime());
                        entity.setCloseTime(dto.closeTime());
                        entity.setOpen(dto.open());
                        entity.setHigh(dto.high());
                        entity.setLow(dto.low());
                        entity.setClose(dto.close());
                        entity.setVolume(dto.volume());
                        entity.setQuoteVolume(dto.quoteVolume());
                        entity.setTradeCount(dto.tradeCount());
                        toInsert.add(entity);
                    }
                }

                if (!toInsert.isEmpty()) {
                    candleRepository.saveAll(toInsert);
                    totalInserted += toInsert.size();
                }

                CandleDto last = batch.get(batch.size() - 1);
                log.info("Ingestion batch persisted: {} inserted. Last candle openTime: {}", toInsert.size(), last.openTime());

                if (batch.size() < 1000 || (endTime != null && !last.openTime().isBefore(endTime))) {
                    break;
                }

                currentStart = last.openTime().plusMillis(1);
            }

            run.setStatus(DataIngestionRun.Status.COMPLETED);
            run.setRecordsReceived(totalReceived);
            run.setRecordsInserted(totalInserted);
            run.setCompletedAt(Instant.now());

        } catch (Exception ex) {
            log.error("Ingestion failed: {}", ex.getMessage(), ex);
            run.setStatus(DataIngestionRun.Status.FAILED);
            run.setErrorMessage(ex.getMessage());
            run.setCompletedAt(Instant.now());
        }

        return runRepository.save(run);
    }
}
