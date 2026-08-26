package com.hkbk.autoscaler.dto;

import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

/** Response for GET /cost-report - the "does the RL agent actually save money" answer. */
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
public class CostReportResponse {
    private Double rlCumulativeCost;
    private Double baselineCumulativeCost;
    private Double savingsPct;
}
