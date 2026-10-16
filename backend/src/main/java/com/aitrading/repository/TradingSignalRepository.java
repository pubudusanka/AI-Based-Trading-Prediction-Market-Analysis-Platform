package com.aitrading.repository;

import com.aitrading.model.TradingSignalRecord;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

@Repository
public interface TradingSignalRepository extends JpaRepository<TradingSignalRecord, Long> {
    List<TradingSignalRecord> findBySymbolAndTimeframeOrderByCandleTimeDesc(String symbol, String timeframe, Pageable pageable);
    Optional<TradingSignalRecord> findTopBySymbolAndTimeframeOrderByCandleTimeDesc(String symbol, String timeframe);
}
