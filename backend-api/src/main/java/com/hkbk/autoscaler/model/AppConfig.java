package com.hkbk.autoscaler.model;

import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

/**
 * Single-row table holding the tunable settings the dashboard's Config page edits.
 * We always use id = 1L - this is intentionally a singleton, not a multi-tenant table.
 */
@Entity
@Table(name = "app_config")
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
public class AppConfig {

    public static final Long SINGLETON_ID = 1L;

    @Id
    private Long id = SINGLETON_ID;

    /** Dollars per running instance per hour - the core input to CostEvaluationService. */
    private Double costPerInstanceHour = 0.05;

    /** CPU % above which an SLA violation is considered to have occurred. */
    private Double slaCpuThreshold = 75.0;

    /** Name of the docker-compose service CloudExecutionService scales. */
    private String targetServiceName = "sample-app";

    /** Current known instance count - updated every time a scaling action is applied. */
    private Integer currentInstanceCount = 2;

    public static AppConfig defaults() {
        return new AppConfig(SINGLETON_ID, 0.05, 75.0, "sample-app", 2);
    }
}
