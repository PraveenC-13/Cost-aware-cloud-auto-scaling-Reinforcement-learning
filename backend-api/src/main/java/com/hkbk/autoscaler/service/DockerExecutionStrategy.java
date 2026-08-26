package com.hkbk.autoscaler.service;

import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.concurrent.TimeUnit;

/**
 * Executes scaling actions by shelling out to the Docker Compose CLI:
 *   docker compose -f <file> up -d --scale <service>=<N> --no-recreate
 *
 * This is the pragmatic choice for a student/demo project: it needs no extra
 * Java dependency (no docker-java client, no AWS SDK), it's easy to explain
 * in a viva, and it actually scales real containers you can watch in
 * `docker ps` during the live demo.
 *
 * Minimum instances is clamped to 1 so the app is never scaled to zero.
 * Maximum instances is clamped to 10 as a safety limit for a laptop demo.
 */
@Slf4j
@Service
public class DockerExecutionStrategy implements ExecutionStrategy {

    private static final int MIN_INSTANCES = 1;
    private static final int MAX_INSTANCES = 10;

    @Value("${autoscaler.docker.compose-file:infra/docker-compose.yml}")
    private String composeFile;

    @Override
    public int applyAction(String targetService, String action, int currentCount) {
        int newCount = switch (action) {
            case "scale_up" -> Math.min(currentCount + 1, MAX_INSTANCES);
            case "scale_down" -> Math.max(currentCount - 1, MIN_INSTANCES);
            case "hold" -> currentCount;
            default -> {
                log.warn("Unknown action '{}', treating as hold", action);
                yield currentCount;
            }
        };

        if (newCount == currentCount) {
            log.info("No-op scaling action ({}), staying at {} instance(s) of {}", action, currentCount, targetService);
            return currentCount;
        }

        boolean success = runComposeScale(targetService, newCount);
        if (!success) {
            log.error("docker compose scale failed - keeping previous instance count {}", currentCount);
            return currentCount;
        }

        log.info("Scaled {} from {} -> {} instance(s)", targetService, currentCount, newCount);
        return newCount;
    }

    @Override
    public int getCurrentInstanceCount(String targetService) {
        try {
            Process process = new ProcessBuilder(
                    "docker", "compose", "-f", composeFile, "ps", "-q", targetService)
                    .redirectErrorStream(true)
                    .start();
            int count = 0;
            try (BufferedReader reader = new BufferedReader(
                    new InputStreamReader(process.getInputStream(), StandardCharsets.UTF_8))) {
                while (reader.readLine() != null) {
                    count++;
                }
            }
            process.waitFor(10, TimeUnit.SECONDS);
            return count == 0 ? MIN_INSTANCES : count;
        } catch (IOException | InterruptedException e) {
            log.warn("Could not read current instance count from docker compose, defaulting to 1: {}", e.getMessage());
            Thread.currentThread().interrupt();
            return MIN_INSTANCES;
        }
    }

    private boolean runComposeScale(String targetService, int newCount) {
        try {
            Process process = new ProcessBuilder(
                    "docker", "compose", "-f", composeFile,
                    "up", "-d", "--scale", targetService + "=" + newCount, "--no-recreate")
                    .redirectErrorStream(true)
                    .start();

            try (BufferedReader reader = new BufferedReader(
                    new InputStreamReader(process.getInputStream(), StandardCharsets.UTF_8))) {
                String line;
                while ((line = reader.readLine()) != null) {
                    log.debug("[docker compose] {}", line);
                }
            }

            boolean finished = process.waitFor(30, TimeUnit.SECONDS);
            return finished && process.exitValue() == 0;
        } catch (IOException | InterruptedException e) {
            log.error("Failed to run docker compose scale command", e);
            Thread.currentThread().interrupt();
            return false;
        }
    }
}
