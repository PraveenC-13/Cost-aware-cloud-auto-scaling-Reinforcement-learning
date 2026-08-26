package com.hkbk.autoscaler.dto;

import jakarta.validation.constraints.NotBlank;
import lombok.Getter;
import lombok.Setter;

/**
 * Body of POST /scale.
 * This matches exactly what Pooja Surve's rl-engine POST /decide returns:
 *   { "action": "scale_up", "confidence": 0.92, "reasoning": "..." }
 * cpu / predictedCpu are optional extras (not part of the original /decide response) -
 * the rl-engine already has them since they were part of ITS OWN request, so it's a
 * one-line change on her side to pass them through here for a richer audit log.
 * If she doesn't send them, they simply come through as null - the app still works.
 */
@Getter
@Setter
public class ScaleDecisionRequest {

    @NotBlank(message = "action is required")
    private String action; // scale_up | scale_down | hold

    private Double confidence;

    private String reasoning;

    private Double cpu;

    private Double predictedCpu;
}
