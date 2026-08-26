package com.hkbk.autoscaler.repository;

import com.hkbk.autoscaler.model.AppConfig;
import org.springframework.data.jpa.repository.JpaRepository;

public interface AppConfigRepository extends JpaRepository<AppConfig, Long> {
}
