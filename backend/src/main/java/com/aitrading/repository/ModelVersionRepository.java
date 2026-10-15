package com.aitrading.repository;

import com.aitrading.model.ModelVersion;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

@Repository
public interface ModelVersionRepository extends JpaRepository<ModelVersion, Integer> {
    Optional<ModelVersion> findByVersion(String version);
    List<ModelVersion> findByModelTypeOrderByCreatedAtDesc(String modelType, Pageable pageable);
}
