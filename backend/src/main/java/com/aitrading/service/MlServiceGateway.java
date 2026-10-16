package com.aitrading.service;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.web.client.RestTemplateBuilder;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpMethod;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import java.time.Duration;
import java.util.List;
import java.util.Map;
import java.util.Optional;

@Service
@SuppressWarnings("null")
public class MlServiceGateway {

    private static final Logger log = LoggerFactory.getLogger(MlServiceGateway.class);

    private static final ParameterizedTypeReference<Map<String, Object>> MAP_TYPE =
        new ParameterizedTypeReference<>() {};
    private static final ParameterizedTypeReference<List<Map<String, Object>>> LIST_MAP_TYPE =
        new ParameterizedTypeReference<>() {};

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
            String url = mlServiceUrl + "/health";
            ResponseEntity<Map<String, Object>> resp = restTemplate.exchange(
                url,
                HttpMethod.GET,
                null,
                MAP_TYPE
            );
            return resp.getStatusCode().is2xxSuccessful();
        } catch (Exception e) {
            log.warn("ML Service health check failed at {}: {}", mlServiceUrl, e.getMessage());
            return false;
        }
    }

    public List<Map<String, Object>> listRegisteredModels(String symbol, String timeframe) {
        try {
            String url = mlServiceUrl + "/models?symbol=" + symbol + "&timeframe=" + timeframe;
            ResponseEntity<List<Map<String, Object>>> resp = restTemplate.exchange(
                url,
                HttpMethod.GET,
                null,
                LIST_MAP_TYPE
            );
            if (resp.getStatusCode().is2xxSuccessful() && resp.getBody() != null) {
                return resp.getBody();
            }
        } catch (Exception e) {
            log.warn("Failed to fetch models from ML service: {}", e.getMessage());
        }
        return List.of();
    }

    public Optional<Map<String, Object>> requestPrediction(Map<String, Object> requestBody) {
        try {
            String url = mlServiceUrl + "/predict";
            HttpEntity<Map<String, Object>> entity = new HttpEntity<>(requestBody);
            ResponseEntity<Map<String, Object>> resp = restTemplate.exchange(
                url,
                HttpMethod.POST,
                entity,
                MAP_TYPE
            );
            if (resp.getStatusCode().is2xxSuccessful() && resp.getBody() != null) {
                return Optional.ofNullable(resp.getBody());
            }
        } catch (Exception e) {
            log.error("ML service /predict call failed: {}", e.getMessage());
        }
        return Optional.empty();
    }

    public Optional<Map<String, Object>> requestSignal(Map<String, Object> requestBody) {
        try {
            String url = mlServiceUrl + "/signal";
            HttpEntity<Map<String, Object>> entity = new HttpEntity<>(requestBody);
            ResponseEntity<Map<String, Object>> resp = restTemplate.exchange(
                url,
                HttpMethod.POST,
                entity,
                MAP_TYPE
            );
            if (resp.getStatusCode().is2xxSuccessful() && resp.getBody() != null) {
                return Optional.ofNullable(resp.getBody());
            }
        } catch (Exception e) {
            log.error("ML service /signal call failed: {}", e.getMessage());
        }
        return Optional.empty();
    }
}
