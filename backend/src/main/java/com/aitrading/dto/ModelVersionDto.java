package com.aitrading.dto;

import java.time.Instant;

public record ModelVersionDto(
    Integer id,
    String version,
    String modelType,
    String datasetVersion,
    String status,
    String metrics,
    Instant createdAt
) {}
