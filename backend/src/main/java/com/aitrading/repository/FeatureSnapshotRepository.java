package com.aitrading.repository;

import com.aitrading.model.FeatureSnapshot;
import com.aitrading.model.MarketCandle;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

@Repository
public interface FeatureSnapshotRepository extends JpaRepository<FeatureSnapshot, Long> {
    Optional<FeatureSnapshot> findByCandleAndFeatureVersion(MarketCandle candle, String featureVersion);
    List<FeatureSnapshot> findByFeatureVersionOrderByCreatedAtDesc(String featureVersion, Pageable pageable);
}
