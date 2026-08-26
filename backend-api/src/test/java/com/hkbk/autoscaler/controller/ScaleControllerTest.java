package com.hkbk.autoscaler.controller;

import com.hkbk.autoscaler.model.AppConfig;
import com.hkbk.autoscaler.repository.AppConfigRepository;
import com.hkbk.autoscaler.repository.ScalingDecisionRepository;
import com.hkbk.autoscaler.service.CostEvaluationService;
import com.hkbk.autoscaler.service.ExecutionStrategy;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;

import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

/**
 * This test mocks ExecutionStrategy so it never actually shells out to Docker -
 * it only checks that ScaleController wires the pieces together correctly.
 */
@WebMvcTest(ScaleController.class)
class ScaleControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @MockBean
    private ExecutionStrategy executionStrategy;

    @MockBean
    private CostEvaluationService costEvaluationService;

    @MockBean
    private AppConfigRepository appConfigRepository;

    @MockBean
    private ScalingDecisionRepository scalingDecisionRepository;

    @Test
    void scaleUp_appliesActionAndReturnsUpdatedStatus() throws Exception {
        AppConfig config = new AppConfig(AppConfig.SINGLETON_ID, 0.10, 75.0, "sample-app", 2);

        when(costEvaluationService.currentConfig()).thenReturn(config);
        when(executionStrategy.applyAction(eq("sample-app"), eq("scale_up"), eq(2))).thenReturn(3);
        when(costEvaluationService.calculateCostPerHour(3)).thenReturn(0.30);

        String requestBody = """
                { "action": "scale_up", "confidence": 0.91, "reasoning": "predicted spike", "cpu": 78.5, "predictedCpu": 88.0 }
                """;

        mockMvc.perform(post("/scale")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(requestBody))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.instanceCount").value(3))
                .andExpect(jsonPath("$.currentCostPerHour").value(0.30));
    }
}
