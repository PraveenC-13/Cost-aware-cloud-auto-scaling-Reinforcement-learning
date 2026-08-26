package com.hkbk.autoscaler.dto;

import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.time.Instant;

/** One point in the GET /history response - what the dashboard charts are built from. */
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
public class HistoryEntry {
    private Instant timestamp;
    private Double cpu;
    private Double predictedCpu;
    private String action;
    private Integer instanceCount;
}
