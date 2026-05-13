package dev.forgeworks.engine.patterns;

import java.util.*;

/**
 * Rule-based pattern detection engine.
 *
 * <p>Each rule evaluates a window of recent events for a given group key (e.g., all events from the
 * same repository or namespace). If the rule condition matches, it produces a PatternAlert.
 *
 * <p>Why rules (not ML) for MVP: - Deterministic — easy to debug and explain - Zero training data
 * needed — works from day one - Fast — pure Java logic, no model loading - Extensible — add new
 * rules without retraining
 *
 * <p>ML-based pattern detection comes in Phase 3 (Airflow training pipeline) and Phase 2 Sprint 2.2
 * tasks T-E2.2.5/6 (model loader).
 */
public class PatternRules {

    /**
     * Evaluate all rules against a window of events. Returns a list of alerts (may be empty if no
     * patterns matched).
     */
    public static List<PatternAlert> evaluate(String groupKey, List<EventEnvelope> window) {
        List<PatternAlert> alerts = new ArrayList<>();

        PatternAlert rapid = checkRapidDeployments(groupKey, window);
        if (rapid != null) alerts.add(rapid);

        PatternAlert crashLoop = checkPodCrashLoop(groupKey, window);
        if (crashLoop != null) alerts.add(crashLoop);

        PatternAlert noTests = checkMergeWithoutTests(groupKey, window);
        if (noTests != null) alerts.add(noTests);

        return alerts;
    }

    /**
     * PATTERN: Rapid Successive Deployments Trigger: >3 ArgoCD sync events within the window for
     * the same app Severity: high Why: Multiple rapid deploys often signal instability — rollback
     * loops, config thrashing, or an engineer force-pushing fixes repeatedly.
     */
    static PatternAlert checkRapidDeployments(String groupKey, List<EventEnvelope> window) {
        List<String> syncEventIds = new ArrayList<>();
        for (EventEnvelope e : window) {
            if ("argocd".equals(e.getSource())
                    && e.getType() != null
                    && e.getType().contains("sync")) {
                syncEventIds.add(e.getEventId());
            }
        }

        if (syncEventIds.size() > 3) {
            return PatternAlert.create(
                    "PAT-DEPLOY-001",
                    "Rapid Successive Deployments",
                    "high",
                    syncEventIds.size() + " deployments detected in window for " + groupKey,
                    "argocd",
                    groupKey,
                    syncEventIds.size(),
                    10,
                    syncEventIds,
                    Map.of("threshold", 3, "actual", syncEventIds.size()));
        }
        return null;
    }

    /**
     * PATTERN: Pod Crash Loop Trigger: >3 Kubernetes pod restart/crash events within the window
     * Severity: critical Why: CrashLoopBackOff means the pod keeps dying and restarting. Catching
     * this early prevents cascading failures.
     */
    static PatternAlert checkPodCrashLoop(String groupKey, List<EventEnvelope> window) {
        List<String> crashEventIds = new ArrayList<>();
        for (EventEnvelope e : window) {
            if ("kubernetes".equals(e.getSource())
                    && e.getType() != null
                    && (e.getType().contains("crash")
                            || e.getType().contains("restart")
                            || e.getType().contains("backoff")
                            || e.getType().contains("failed"))) {
                crashEventIds.add(e.getEventId());
            }
        }

        if (crashEventIds.size() > 3) {
            return PatternAlert.create(
                    "PAT-K8S-001",
                    "Pod Crash Loop Detected",
                    "critical",
                    crashEventIds.size() + " crash/restart events for " + groupKey,
                    "kubernetes",
                    groupKey,
                    crashEventIds.size(),
                    5,
                    crashEventIds,
                    Map.of("threshold", 3, "actual", crashEventIds.size()));
        }
        return null;
    }

    /**
     * PATTERN: Merge Without Tests Trigger: GitHub merge event without a corresponding
     * workflow/check event in the window Severity: medium Why: Merging PRs without test runs risks
     * pushing broken code to production. This pattern catches repos where CI isn't running or was
     * skipped.
     */
    static PatternAlert checkMergeWithoutTests(String groupKey, List<EventEnvelope> window) {
        List<String> mergeEventIds = new ArrayList<>();
        boolean hasTestRun = false;

        for (EventEnvelope e : window) {
            if (!"github".equals(e.getSource())) continue;

            String type = e.getType();
            if (type == null) continue;

            if (type.contains("merged") || type.contains("closed")) {
                // Check if action=merged in payload
                Object action = e.getPayload() != null ? e.getPayload().get("action") : null;
                if ("merged".equals(action) || type.contains("merged")) {
                    mergeEventIds.add(e.getEventId());
                }
            }

            if (type.contains("check_run")
                    || type.contains("check_suite")
                    || type.contains("workflow_run")
                    || type.contains("status")) {
                hasTestRun = true;
            }
        }

        if (!mergeEventIds.isEmpty() && !hasTestRun) {
            return PatternAlert.create(
                    "PAT-CI-001",
                    "PR Merged Without Tests",
                    "medium",
                    "PR merged without test/check run detected for " + groupKey,
                    "github",
                    groupKey,
                    mergeEventIds.size(),
                    10,
                    mergeEventIds,
                    Map.of("merge_count", mergeEventIds.size(), "tests_detected", false));
        }
        return null;
    }
}
