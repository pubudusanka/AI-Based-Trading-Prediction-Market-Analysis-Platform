package com.aitrading.repository;

import com.aitrading.model.DataIngestionRun;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface DataIngestionRunRepository extends JpaRepository<DataIngestionRun, Long> {
    List<DataIngestionRun> findBySymbolOrderByStartedAtDesc(String symbol, Pageable pageable);
}
