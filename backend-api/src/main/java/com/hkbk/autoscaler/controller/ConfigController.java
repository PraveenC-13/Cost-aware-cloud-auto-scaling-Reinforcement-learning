package com.hkbk.autoscaler.controller;

import com.hkbk.autoscaler.dto.ConfigDto;
import com.hkbk.autoscaler.model.AppConfig;
import com.hkbk.autoscaler.repository.AppConfigRepository;
import com.hkbk.autoscaler.service.CostEvaluationService;
import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/config")
public class ConfigController {

    private final AppConfigRepository appConfigRepository;
    private final CostEvaluationService costEvaluationService;

    public ConfigController(AppConfigRepository appConfigRepository,
                             CostEvaluationService costEvaluationService) {
        this.appConfigRepository = appConfigRepository;
        this.costEvaluationService = costEvaluationService;
    }

    @GetMapping
    public ConfigDto get() {
        AppConfig config = costEvaluationService.currentConfig();
        return new ConfigDto(config.getCostPerInstanceHour(), config.getSlaCpuThreshold(), config.getTargetServiceName());
    }

    @PutMapping
    public ConfigDto update(@Valid @RequestBody ConfigDto update) {
        AppConfig config = costEvaluationService.currentConfig();
        if (update.getCostPerInstanceHour() != null) {
            config.setCostPerInstanceHour(update.getCostPerInstanceHour());
        }
        if (update.getSlaCpuThreshold() != null) {
            config.setSlaCpuThreshold(update.getSlaCpuThreshold());
        }
        if (update.getTargetServiceName() != null) {
            config.setTargetServiceName(update.getTargetServiceName());
        }
        appConfigRepository.save(config);
        return new ConfigDto(config.getCostPerInstanceHour(), config.getSlaCpuThreshold(), config.getTargetServiceName());
    }
}
