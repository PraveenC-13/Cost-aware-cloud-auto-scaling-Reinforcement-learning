package com.hkbk.autoscaler.service;

import com.hkbk.autoscaler.model.AppConfig;
import com.hkbk.autoscaler.model.ScalingDecision;
import com.hkbk.autoscaler.repository.AppConfigRepository;
import com.hkbk.autoscaler.repository.ScalingDecisionRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import java.time.Instant;
import java.time.temporal.ChronoUnit;
import java.util.List;
import java.util.Optional;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

class CostEvaluationServiceTest {

    private AppConfigRepository appConfigRepository;
    private ScalingDecisionRepository scalingDecisionRepository;
    private CostEvaluationService service;

    @BeforeEach
    void setUp() {
        appConfigRepository = mock(AppConfigRepository.class);
        scalingDecisionRepository = mock(ScalingDecisionRepository.class);
        service = new CostEvaluationService(appConfigRepository, scalingDecisionRepository);

        AppConfig config = new AppConfig(AppConfig.SINGLETON_ID, 0.10, 75.0, "sample-app", 2);
        when(appConfigRepository.findById(AppConfig.SINGLETON_ID)).thenReturn(Optional.of(config));
    }

    @Test
    void calculateCostPerHour_multipliesInstancesByRate() {
        double cost = service.calculateCostPerHour(4);
        assertEquals(0.40, cost, 0.0001);
    }

    @Test
    void calculateActualCumulativeCost_integratesOverTime() {
        Instant t0 = Instant.now();
        ScalingDecision d1 = ScalingDecision.of(t0, 40.0, 45.0, "hold", 0.9, "steady", 2, 0.20);
        ScalingDecision d2 = ScalingDecision.of(t0.plus(1, ChronoUnit.HOURS), 80.0, 85.0, "scale_up", 0.95, "spike", 3, 0.30);

        double actual = service.calculateActualCumulativeCost(List.of(d1, d2));

        // d1's cost (0.20/hr) applies for the 1 hour before d2 happens = 0.20
        assertEquals(0.20, actual, 0.01);
    }

    @Test
    void calculateBaselineCumulativeCost_scalesUpWhenAboveThreshold() {
        Instant t0 = Instant.now();
        ScalingDecision spike = ScalingDecision.of(t0, 90.0, 92.0, "scale_up", 0.9, "spike", 3, 0.30);
        ScalingDecision after = ScalingDecision.of(t0.plus(1, ChronoUnit.HOURS), 90.0, 92.0, "hold", 0.9, "still high", 3, 0.30);

        double baseline = service.calculateBaselineCumulativeCost(List.of(spike, after));

        // starting instance count (3) held for 1 hour at 0.10/instance-hour = 0.30
        assertEquals(0.30, baseline, 0.01);
    }
}
