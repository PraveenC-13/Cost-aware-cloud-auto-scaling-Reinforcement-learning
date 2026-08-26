package com.hkbk.autoscaler.controller;

import com.hkbk.autoscaler.dto.HistoryEntry;
import com.hkbk.autoscaler.model.ScalingDecision;
import com.hkbk.autoscaler.repository.ScalingDecisionRepository;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.time.Duration;
import java.time.Instant;
import java.util.List;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import java.util.stream.Collectors;

@RestController
public class HistoryController {

    private static final Pattern RANGE_PATTERN = Pattern.compile("^(\\d+)([smhd])$");

    private final ScalingDecisionRepository scalingDecisionRepository;

    public HistoryController(ScalingDecisionRepository scalingDecisionRepository) {
        this.scalingDecisionRepository = scalingDecisionRepository;
    }

    /** GET /history?range=1h - returns everything the dashboard charts need. */
    @GetMapping("/history")
    public List<HistoryEntry> history(@RequestParam(defaultValue = "1h") String range) {
        Instant since = Instant.now().minus(parseRange(range));

        List<ScalingDecision> decisions = scalingDecisionRepository.findByTimestampAfterOrderByTimestampAsc(since);

        return decisions.stream()
                .map(d -> new HistoryEntry(d.getTimestamp(), d.getCpu(), d.getPredictedCpu(), d.getAction(), d.getInstanceCountAfter()))
                .collect(Collectors.toList());
    }

    private Duration parseRange(String range) {
        Matcher matcher = RANGE_PATTERN.matcher(range.trim());
        if (!matcher.matches()) {
            return Duration.ofHours(1); // sensible default if someone sends garbage
        }
        long amount = Long.parseLong(matcher.group(1));
        return switch (matcher.group(2)) {
            case "s" -> Duration.ofSeconds(amount);
            case "m" -> Duration.ofMinutes(amount);
            case "h" -> Duration.ofHours(amount);
            case "d" -> Duration.ofDays(amount);
            default -> Duration.ofHours(1);
        };
    }
}
