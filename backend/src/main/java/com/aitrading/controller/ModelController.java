package com.aitrading.controller;

import com.aitrading.dto.ModelVersionDto;
import com.aitrading.service.ModelService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/v1/models")
@CrossOrigin(origins = "*")
public class ModelController {

    private final ModelService modelService;

    public ModelController(ModelService modelService) {
        this.modelService = modelService;
    }

    @GetMapping("/list")
    public ResponseEntity<List<Map<String, Object>>> listModels(
        @RequestParam(defaultValue = "BTC/USDT") String symbol,
        @RequestParam(defaultValue = "15m") String timeframe
    ) {
        return ResponseEntity.ok(modelService.listModels(symbol, timeframe));
    }

    @GetMapping("/{version}")
    public ResponseEntity<ModelVersionDto> getModelDetails(@PathVariable String version) {
        return modelService.getModelDetails(version)
            .map(ResponseEntity::ok)
            .orElseGet(() -> ResponseEntity.notFound().build());
    }

    @GetMapping("/{version}/metrics")
    public ResponseEntity<Map<String, Object>> getModelMetrics(@PathVariable String version) {
        return ResponseEntity.ok(modelService.getModelMetrics(version));
    }
}
