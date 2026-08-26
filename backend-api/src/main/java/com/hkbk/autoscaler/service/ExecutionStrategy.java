package com.hkbk.autoscaler.service;

/**
 * Abstraction over "how do we actually change the number of running instances".
 * DockerExecutionStrategy is the default (used for local/demo).
 * Add an AwsExecutionStrategy later (EC2 Auto Scaling Group SetDesiredCapacity)
 * behind this same interface if AWS credits become available - nothing else
 * in the codebase needs to change.
 */
public interface ExecutionStrategy {

    /**
     * Apply one scaling action.
     *
     * @param targetService the docker-compose service name (or ASG name) to act on
     * @param action        one of: scale_up, scale_down, hold
     * @param currentCount  instance count before this action
     * @return the instance count AFTER applying the action
     */
    int applyAction(String targetService, String action, int currentCount);

    /**
     * Best-effort read of how many instances are currently running.
     * Used at startup / for reconciliation if state drifts.
     */
    int getCurrentInstanceCount(String targetService);
}
