package com.aitrading.repository;

import com.aitrading.model.MarketCandle;
import com.aitrading.model.MarketSymbol;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.time.Instant;
import java.util.List;
import java.util.Optional;

@Repository
public interface MarketCandleRepository extends JpaRepository<MarketCandle, Long> {

    boolean existsBySymbolAndTimeframeAndOpenTime(MarketSymbol symbol, String timeframe, Instant openTime);

    @Query("SELECT c FROM MarketCandle c WHERE c.symbol.id = :symbolId AND c.timeframe = :timeframe ORDER BY c.openTime DESC")
    List<MarketCandle> findLatestCandles(
        @Param("symbolId") Integer symbolId,
        @Param("timeframe") String timeframe,
        Pageable pageable
    );

    @Query("SELECT c FROM MarketCandle c WHERE c.symbol.id = :symbolId AND c.timeframe = :timeframe AND c.openTime >= :startTime AND c.openTime <= :endTime ORDER BY c.openTime ASC")
    List<MarketCandle> findCandlesInRange(
        @Param("symbolId") Integer symbolId,
        @Param("timeframe") String timeframe,
        @Param("startTime") Instant startTime,
        @Param("endTime") Instant endTime
    );

    @Query("SELECT MAX(c.openTime) FROM MarketCandle c WHERE c.symbol.id = :symbolId AND c.timeframe = :timeframe")
    Optional<Instant> findMaxOpenTime(@Param("symbolId") Integer symbolId, @Param("timeframe") String timeframe);
}
