package com.aitrading.service;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.web.client.RestTemplateBuilder;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestClientException;
import org.springframework.web.client.RestTemplate;

import java.time.Duration;
import java.util.List;
import java.util.Map;
import java.util.Optional;

@Service
public class MlServiceGateway {

    private static final Logger log = LoggerFactory.getLogger(MlServiceGateway.class);

    private final RestTemplate restTemplate;
    private final String mlServiceUrl;

    public MlServiceGateway(
        RestTemplateBuilder restTemplateBuilder,
        @Value("${trading.ml-service.url:http://localhost:8001}") String mlServiceUrl
    ) {
        this.restTemplate = restTemplateBuilder
            .setConnectTimeout(Duration.ofSeconds(3))
            .setReadTimeout(Duration.ofSeconds(10))
            .build();
        this.mlServiceUrl = mlServiceUrl.replaceAll("/+$", "");
    }

    public boolean isHealthy() {
        try {
            ResponseEntity<Map> resp = restTemplate.getForEntity(mlServiceUrl + "/health", Map.class);
            return resp.getStatusCode().is2xxSuccessful();
        } catch (Exception e) {
            log.warn("ML Service health check failed at {}: {}", mlServiceUrl, e.getMessage());
            return false;
        }
    }

    @SuppressWarnings("unchecked")
    public List<Map<String, Object>> listRegisteredModels(String symbol, String timeframe) {
        try {
            String url = String.format("%s/models?symbol=%s&timeframe=%s", mlServiceUrl, symbol, timeframe);
            ResponseEntity<List> resp = restTemplate.getForEntity(url, List.class);
            if (resp.getStatusCode().is2xxSuccessful() && resp.getBody() != null) {
                return (List<Map<String, Object>>) resp.getBody();
            }
        } catch (Exception e) {
            log.warn("Failed to fetch models from ML service: {}", e.getMessage());
        }
        return List.of();
    }

    @SuppressWarnings("unchecked")
    public Optional<Map<String, Object>> requestPrediction(Map<String, Object> requestBody) {
        try {
            ResponseEntity<Map> resp = restTemplate.postForEntity(mlServiceUrl + "/predict", requestBody, Map.class);
            if (resp.getStatusCode().is2xxSuccessful() && resp.getBody() != null) {
                return Optional.of((Map<String, Object>) resp.getBody());
            }
        } catch (Exception e) {
            log.error("ML service /predict call failed: {}", e.getMessage());
        }
        return Optional.empty();
    }

    @SuppressWarnings("unchecked")
    public Optional<Map<String, Object>> requestSignal(Map<String, Object> requestBody) {
        try {
            ResponseEntity<Map> resp = restTemplate.postForEntity(mlServiceUrl + "/signal", requestBody, Map.class);
            if (resp.getStatusCode().is2xxSuccessful() && resp.getBody() != null) {
                return Optional.of((Map<String, Object>) resp.getBody());
            }
        } catch (Exception e) {
            log.error("ML service /signal call failed: {}", e.getMessage());
        }
        return Optional.empty();
    }
}
