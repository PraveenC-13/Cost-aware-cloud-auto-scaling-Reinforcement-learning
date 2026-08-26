package com.hkbk.autoscaler.dto;

import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

/** GET/PUT /config body. */
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
public class ConfigDto {
    private Double costPerInstanceHour;
    private Double slaCpuThreshold;
    private String targetServiceName;
}
