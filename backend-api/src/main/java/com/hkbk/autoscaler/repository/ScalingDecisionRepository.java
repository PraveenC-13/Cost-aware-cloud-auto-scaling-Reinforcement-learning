package com.hkbk.autoscaler.repository;

import com.hkbk.autoscaler.model.ScalingDecision;
import org.springframework.data.jpa.repository.JpaRepository;

import java.time.Instant;
import java.util.List;

public interface ScalingDecisionRepository extends JpaRepository<ScalingDecision, Long> {

    List<ScalingDecision> findByTimestampAfterOrderByTimestampAsc(Instant since);

    ScalingDecision findFirstByOrderByTimestampDesc();
}
