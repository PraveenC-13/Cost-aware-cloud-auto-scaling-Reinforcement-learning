package com.hkbk.autoscaler.model;

import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.time.Instant;

/**
 * One row per scaling decision the RL engine made and this service executed.
 * This table is the source of truth for /history and /cost-report.
 */
@Entity
@Table(name = "scaling_decisions")
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
public class ScalingDecision {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false)
    private Instant timestamp;

    /** CPU % reported by the monitoring-agent at decision time. */
    private Double cpu;

    /** CPU % forecast by the prediction-service for the next horizon. */
    private Double predictedCpu;

    /** One of: scale_up, scale_down, hold */
    @Column(nullable = false)
    private String action;

    /** How confident the RL policy was in this action (0-1). */
    private Double confidence;

    /** Free-text explanation returned by the RL engine, stored for audit/report use. */
    @Column(length = 500)
    private String reasoning;

    /** Instance count AFTER this decision was applied. */
    @Column(nullable = false)
    private Integer instanceCountAfter;

    /** Cost per hour AFTER this decision, at the configured rate. */
    @Column(nullable = false)
    private Double costPerHourAfter;

    public static ScalingDecision of(Instant timestamp, Double cpu, Double predictedCpu,
                                      String action, Double confidence, String reasoning,
                                      Integer instanceCountAfter, Double costPerHourAfter) {
        ScalingDecision d = new ScalingDecision();
        d.setTimestamp(timestamp);
        d.setCpu(cpu);
        d.setPredictedCpu(predictedCpu);
        d.setAction(action);
        d.setConfidence(confidence);
        d.setReasoning(reasoning);
        d.setInstanceCountAfter(instanceCountAfter);
        d.setCostPerHourAfter(costPerHourAfter);
        return d;
    }
}
