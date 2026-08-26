package com.hkbk.autoscaler.controller;

import com.hkbk.autoscaler.dto.ScaleDecisionRequest;
import com.hkbk.autoscaler.dto.StatusResponse;
import com.hkbk.autoscaler.model.AppConfig;
import com.hkbk.autoscaler.model.ScalingDecision;
import com.hkbk.autoscaler.repository.AppConfigRepository;
import com.hkbk.autoscaler.repository.ScalingDecisionRepository;
import com.hkbk.autoscaler.service.CostEvaluationService;
import com.hkbk.autoscaler.service.ExecutionStrategy;
import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;

import java.time.Instant;

/**
 * POST /scale is the hinge of the whole system: it's what Pooja Surve's
 * rl-engine calls right after it decides an action. This controller applies
 * the action for real (via ExecutionStrategy), records it for history/reporting,
 * and returns the resulting status.
 */
@RestController
public class ScaleController {

    private final ExecutionStrategy executionStrategy;
    private final CostEvaluationService costEvaluationService;
    private final AppConfigRepository appConfigRepository;
    private final ScalingDecisionRepository scalingDecisionRepository;

    public ScaleController(ExecutionStrategy executionStrategy,
                            CostEvaluationService costEvaluationService,
                            AppConfigRepository appConfigRepository,
                            ScalingDecisionRepository scalingDecisionRepository) {
        this.executionStrategy = executionStrategy;
        this.costEvaluationService = costEvaluationService;
        this.appConfigRepository = appConfigRepository;
        this.scalingDecisionRepository = scalingDecisionRepository;
    }

    @PostMapping("/scale")
    public StatusResponse scale(@Valid @RequestBody ScaleDecisionRequest request) {
        AppConfig config = costEvaluationService.currentConfig();
        int before = config.getCurrentInstanceCount();

        int after = executionStrategy.applyAction(config.getTargetServiceName(), request.getAction(), before);

        config.setCurrentInstanceCount(after);
        appConfigRepository.save(config);

        double newCostPerHour = costEvaluationService.calculateCostPerHour(after);

        ScalingDecision decision = ScalingDecision.of(
                Instant.now(),
                request.getCpu(),
                request.getPredictedCpu(),
                request.getAction(),
                request.getConfidence(),
                request.getReasoning(),
                after,
                newCostPerHour
        );
        scalingDecisionRepository.save(decision);

        return new StatusResponse(after, newCostPerHour, request.getCpu());
    }
}
