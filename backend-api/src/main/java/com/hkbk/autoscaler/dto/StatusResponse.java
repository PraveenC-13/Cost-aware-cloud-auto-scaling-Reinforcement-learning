package com.hkbk.autoscaler.dto;

import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

/** Response for GET /status - consumed by Pooja V's dashboard. */
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
public class StatusResponse {
    private Integer instanceCount;
    private Double currentCostPerHour;
    private Double latestCpu;
}
