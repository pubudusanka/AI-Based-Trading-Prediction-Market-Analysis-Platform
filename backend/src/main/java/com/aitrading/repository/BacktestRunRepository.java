package com.aitrading.repository;

import com.aitrading.model.BacktestRun;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface BacktestRunRepository extends JpaRepository<BacktestRun, Long> {
    List<BacktestRun> findBySymbolOrderByCreatedAtDesc(String symbol, Pageable pageable);
    List<BacktestRun> findByModelVersionOrderBySharpeRatioDesc(String modelVersion, Pageable pageable);
}
