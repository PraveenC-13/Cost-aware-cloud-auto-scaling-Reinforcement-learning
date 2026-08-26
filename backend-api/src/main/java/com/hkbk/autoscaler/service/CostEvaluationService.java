package com.hkbk.autoscaler.service;

import com.hkbk.autoscaler.dto.CostReportResponse;
import com.hkbk.autoscaler.model.AppConfig;
import com.hkbk.autoscaler.model.ScalingDecision;
import com.hkbk.autoscaler.repository.AppConfigRepository;
import com.hkbk.autoscaler.repository.ScalingDecisionRepository;
import org.springframework.stereotype.Service;

import java.time.Duration;
import java.time.Instant;
import java.util.List;

/**
 * The "cost-aware" half of the project's core claim. Two jobs:
 *   1. Turn an instance count into a dollar figure (simple, deliberately).
 *   2. Replay the stored decision history through a naive rule-based baseline
 *      (scale up above SLA threshold, scale down well below it) and compare
 *      its hypothetical cost to what the RL agent actually spent.
 *      This comparison is the single most important number in the report.
 */
@Service
public class CostEvaluationService {

    private static final double RULE_BASED_SCALE_DOWN_MARGIN = 25.0; // percentage points below SLA threshold

    private final AppConfigRepository appConfigRepository;
    private final ScalingDecisionRepository scalingDecisionRepository;

    public CostEvaluationService(AppConfigRepository appConfigRepository,
                                  ScalingDecisionRepository scalingDecisionRepository) {
        this.appConfigRepository = appConfigRepository;
        this.scalingDecisionRepository = scalingDecisionRepository;
    }

    public AppConfig currentConfig() {
        return appConfigRepository.findById(AppConfig.SINGLETON_ID)
                .orElseGet(() -> appConfigRepository.save(AppConfig.defaults()));
    }

    /** Straightforward: cost/hour = instance_count * price_per_instance_hour. */
    public double calculateCostPerHour(int instanceCount) {
        return instanceCount * currentConfig().getCostPerInstanceHour();
    }

    /**
     * Sums actual cost incurred over the stored history using time-weighted
     * integration: each decision's cost/hour applies until the next decision.
     */
    public double calculateActualCumulativeCost(List<ScalingDecision> history) {
        return integrateCost(history, ScalingDecision::getCostPerHourAfter);
    }

    /**
     * Replays the same CPU trace through a simple threshold rule and computes
     * what THAT policy would have cost, so we have a control group to compare
     * the RL agent against.
     */
    public double calculateBaselineCumulativeCost(List<ScalingDecision> history) {
        if (history.isEmpty()) {
            return 0.0;
        }
        double costPerInstanceHour = currentConfig().getCostPerInstanceHour();
        double slaThreshold = currentConfig().getSlaCpuThreshold();

        int simulatedInstances = history.get(0).getInstanceCountAfter();
        double total = 0.0;
        Instant previousTimestamp = history.get(0).getTimestamp();

        for (ScalingDecision decision : history) {
            double hoursSinceLast = Duration.between(previousTimestamp, decision.getTimestamp()).toSeconds() / 3600.0;
            total += simulatedInstances * costPerInstanceHour * Math.max(hoursSinceLast, 0);

            double cpu = decision.getCpu() == null ? 0.0 : decision.getCpu();
            if (cpu > slaThreshold) {
                simulatedInstances = Math.min(simulatedInstances + 1, 10);
            } else if (cpu < slaThreshold - RULE_BASED_SCALE_DOWN_MARGIN) {
                simulatedInstances = Math.max(simulatedInstances - 1, 1);
            }
            previousTimestamp = decision.getTimestamp();
        }
        return total;
    }

    public CostReportResponse buildCostReport(List<ScalingDecision> history) {
        double actual = calculateActualCumulativeCost(history);
        double baseline = calculateBaselineCumulativeCost(history);
        double savingsPct = baseline <= 0 ? 0.0 : ((baseline - actual) / baseline) * 100.0;
        return new CostReportResponse(round2(actual), round2(baseline), round2(savingsPct));
    }

    private double integrateCost(List<ScalingDecision> history, java.util.function.Function<ScalingDecision, Double> costFn) {
        if (history.isEmpty()) {
            return 0.0;
        }
        double total = 0.0;
        Instant previousTimestamp = history.get(0).getTimestamp();
        for (ScalingDecision decision : history) {
            double hoursSinceLast = Duration.between(previousTimestamp, decision.getTimestamp()).toSeconds() / 3600.0;
            Double costPerHour = costFn.apply(decision);
            total += (costPerHour == null ? 0.0 : costPerHour) * Math.max(hoursSinceLast, 0);
            previousTimestamp = decision.getTimestamp();
        }
        return total;
    }

    private double round2(double value) {
        return Math.round(value * 100.0) / 100.0;
    }
}
