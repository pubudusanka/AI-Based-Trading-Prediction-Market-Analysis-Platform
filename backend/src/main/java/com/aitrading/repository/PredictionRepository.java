package com.aitrading.repository;

import com.aitrading.model.Prediction;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.time.Instant;
import java.util.List;
import java.util.Optional;

@Repository
public interface PredictionRepository extends JpaRepository<Prediction, Long> {
    List<Prediction> findBySymbolAndTimeframeOrderByCandleTimeDesc(String symbol, String timeframe, Pageable pageable);
    Optional<Prediction> findTopBySymbolAndTimeframeOrderByCandleTimeDesc(String symbol, String timeframe);
    List<Prediction> findByCandleTimeBetween(Instant start, Instant end);
}
