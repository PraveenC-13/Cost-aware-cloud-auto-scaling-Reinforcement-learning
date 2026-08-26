package com.hkbk.autoscaler.controller;

import com.hkbk.autoscaler.dto.CostReportResponse;
import com.hkbk.autoscaler.model.ScalingDecision;
import com.hkbk.autoscaler.repository.ScalingDecisionRepository;
import com.hkbk.autoscaler.service.CostEvaluationService;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

/** GET /cost-report - the RL-vs-baseline comparison the dashboard's CostComparisonPanel shows. */
@RestController
public class CostReportController {

    private final ScalingDecisionRepository scalingDecisionRepository;
    private final CostEvaluationService costEvaluationService;

    public CostReportController(ScalingDecisionRepository scalingDecisionRepository,
                                 CostEvaluationService costEvaluationService) {
        this.scalingDecisionRepository = scalingDecisionRepository;
        this.costEvaluationService = costEvaluationService;
    }

    @GetMapping("/cost-report")
    public CostReportResponse costReport() {
        List<ScalingDecision> allHistory = scalingDecisionRepository.findAll();
        return costEvaluationService.buildCostReport(allHistory);
    }
}
