package com.hkbk.autoscaler.controller;

import com.hkbk.autoscaler.dto.StatusResponse;
import com.hkbk.autoscaler.model.AppConfig;
import com.hkbk.autoscaler.model.ScalingDecision;
import com.hkbk.autoscaler.repository.ScalingDecisionRepository;
import com.hkbk.autoscaler.service.CostEvaluationService;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class StatusController {

    private final ScalingDecisionRepository scalingDecisionRepository;
    private final CostEvaluationService costEvaluationService;

    public StatusController(ScalingDecisionRepository scalingDecisionRepository,
                             CostEvaluationService costEvaluationService) {
        this.scalingDecisionRepository = scalingDecisionRepository;
        this.costEvaluationService = costEvaluationService;
    }

    @GetMapping("/health")
    public String health() {
        return "{\"status\":\"ok\"}";
    }

    @GetMapping("/status")
    public StatusResponse status() {
        AppConfig config = costEvaluationService.currentConfig();
        ScalingDecision latest = scalingDecisionRepository.findFirstByOrderByTimestampDesc();

        int instanceCount = config.getCurrentInstanceCount();
        double costPerHour = costEvaluationService.calculateCostPerHour(instanceCount);
        Double latestCpu = latest == null ? null : latest.getCpu();

        return new StatusResponse(instanceCount, costPerHour, latestCpu);
    }
}
