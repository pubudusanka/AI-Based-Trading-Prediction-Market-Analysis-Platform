package com.aitrading.repository;

import com.aitrading.model.Prediction;
import com.aitrading.model.PredictionOutcome;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.Optional;

@Repository
public interface PredictionOutcomeRepository extends JpaRepository<PredictionOutcome, Long> {
    Optional<PredictionOutcome> findByPrediction(Prediction prediction);
    Optional<PredictionOutcome> findByPredictionId(Long predictionId);
}
