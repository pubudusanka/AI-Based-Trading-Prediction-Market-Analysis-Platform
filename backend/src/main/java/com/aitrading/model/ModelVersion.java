package com.aitrading.model;

import jakarta.persistence.*;
import java.time.Instant;

@Entity
@Table(name = "model_version", indexes = {
    @Index(name = "idx_model_version_lookup", columnList = "model_name, version")
})
public class ModelVersion {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Integer id;

    @Column(name = "model_name", nullable = false, length = 100)
    private String modelName;

    @Column(name = "model_type", nullable = false, length = 50)
    private String modelType; // XGBOOST, RANDOM_FOREST, LOGISTIC_REGRESSION

    @Column(nullable = false, unique = true, length = 50)
    private String version;

    @Column(name = "dataset_version", length = 50)
    private String datasetVersion;

    @Column(name = "feature_version", length = 50)
    private String featureVersion;

    @Column(columnDefinition = "TEXT")
    private String hyperparameters; // JSON string

    @Column(name = "training_start")
    private Instant trainingStart;

    @Column(name = "training_end")
    private Instant trainingEnd;

    @Column(name = "validation_start")
    private Instant validationStart;

    @Column(name = "validation_end")
    private Instant validationEnd;

    @Column(name = "test_start")
    private Instant testStart;

    @Column(name = "test_end")
    private Instant testEnd;

    @Column(columnDefinition = "TEXT")
    private String metrics; // JSON string (accuracy, f1, log_loss, etc.)

    @Column(name = "artifact_location", length = 255)
    private String artifactLocation;

    @Column(name = "created_at", updatable = false)
    private Instant createdAt = Instant.now();

    public ModelVersion() {}

    public Integer getId() { return id; }
    public void setId(Integer id) { this.id = id; }

    public String getModelName() { return modelName; }
    public void setModelName(String modelName) { this.modelName = modelName; }

    public String getModelType() { return modelType; }
    public void setModelType(String modelType) { this.modelType = modelType; }

    public String getVersion() { return version; }
    public void setVersion(String version) { this.version = version; }

    public String getDatasetVersion() { return datasetVersion; }
    public void setDatasetVersion(String datasetVersion) { this.datasetVersion = datasetVersion; }

    public String getFeatureVersion() { return featureVersion; }
    public void setFeatureVersion(String featureVersion) { this.featureVersion = featureVersion; }

    public String getHyperparameters() { return hyperparameters; }
    public void setHyperparameters(String hyperparameters) { this.hyperparameters = hyperparameters; }

    public Instant getTrainingStart() { return trainingStart; }
    public void setTrainingStart(Instant trainingStart) { this.trainingStart = trainingStart; }

    public Instant getTrainingEnd() { return trainingEnd; }
    public void setTrainingEnd(Instant trainingEnd) { this.trainingEnd = trainingEnd; }

    public Instant getValidationStart() { return validationStart; }
    public void setValidationStart(Instant validationStart) { this.validationStart = validationStart; }

    public Instant getValidationEnd() { return validationEnd; }
    public void setValidationEnd(Instant validationEnd) { this.validationEnd = validationEnd; }

    public Instant getTestStart() { return testStart; }
    public void setTestStart(Instant testStart) { this.testStart = testStart; }

    public Instant getTestEnd() { return testEnd; }
    public void setTestEnd(Instant testEnd) { this.testEnd = testEnd; }

    public String getMetrics() { return metrics; }
    public void setMetrics(String metrics) { this.metrics = metrics; }

    public String getArtifactLocation() { return artifactLocation; }
    public void setArtifactLocation(String artifactLocation) { this.artifactLocation = artifactLocation; }

    public Instant getCreatedAt() { return createdAt; }
}
