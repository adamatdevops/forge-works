package dev.forgeworks.engine.patterns.model;

import dev.forgeworks.engine.patterns.EventEnvelope;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

/**
 * Extracts numeric features from event windows for model scoring.
 *
 * <p>Why a separate extractor: - Models need numeric inputs, events are structured JSON - Feature
 * engineering is reusable across models - Decouples "what to measure" from "how to score" -
 * Features become training data in Phase 3 (logged to Kafka)
 *
 * <p>Feature naming convention: {category}_{metric} deploy_count, crash_count, merge_count — raw
 * counts time_span_inverse — 1.0/minutes (higher = faster = riskier) unique_*_inverse — 1.0/count
 * (higher = fewer unique = riskier) *_missing — 1.0 if absent, 0.0 if present
 */
public class FeatureExtractor {

    /** Extract deployment-related features from an ArgoCD event window. */
    public static Map<String, Double> extractDeployFeatures(List<EventEnvelope> window) {
        Map<String, Double> features = new HashMap<>();

        int deployCount = 0;
        Set<String> authors = new HashSet<>();

        for (EventEnvelope e : window) {
            if ("argocd".equals(e.getSource())
                    && e.getType() != null
                    && e.getType().contains("sync")) {
                deployCount++;
                if (e.getMetadata() != null) {
                    Object sender = e.getMetadata().get("sender");
                    if (sender != null) authors.add(sender.toString());
                }
            }
        }

        features.put("deploy_count", (double) deployCount);
        features.put("time_span_inverse", deployCount > 1 ? 1.0 / 10.0 * deployCount : 0.0);
        features.put("unique_authors_inverse", authors.isEmpty() ? 1.0 : 1.0 / authors.size());

        return features;
    }

    /** Extract crash-loop features from a Kubernetes event window. */
    public static Map<String, Double> extractCrashFeatures(List<EventEnvelope> window) {
        Map<String, Double> features = new HashMap<>();

        int crashCount = 0;
        Set<String> pods = new HashSet<>();

        for (EventEnvelope e : window) {
            if ("kubernetes".equals(e.getSource())
                    && e.getType() != null
                    && (e.getType().contains("crash")
                            || e.getType().contains("restart")
                            || e.getType().contains("backoff")
                            || e.getType().contains("failed"))) {
                crashCount++;
                if (e.getMetadata() != null) {
                    Object name = e.getMetadata().get("name");
                    if (name != null) pods.add(name.toString());
                }
            }
        }

        features.put("crash_count", (double) crashCount);
        features.put("restart_frequency", crashCount > 0 ? (double) crashCount / 10.0 : 0.0);
        features.put("unique_pods_inverse", pods.isEmpty() ? 1.0 : 1.0 / pods.size());

        return features;
    }

    /** Extract CI/CD skip features from a GitHub event window. */
    public static Map<String, Double> extractCIFeatures(List<EventEnvelope> window) {
        Map<String, Double> features = new HashMap<>();

        int mergeCount = 0;
        boolean hasTests = false;
        Set<String> authors = new HashSet<>();

        for (EventEnvelope e : window) {
            if (!"github".equals(e.getSource())) continue;
            String type = e.getType();
            if (type == null) continue;

            if (type.contains("merged")) {
                mergeCount++;
                if (e.getMetadata() != null) {
                    Object sender = e.getMetadata().get("sender");
                    if (sender != null) authors.add(sender.toString());
                }
            }

            if (type.contains("check_run")
                    || type.contains("check_suite")
                    || type.contains("workflow_run")
                    || type.contains("status")) {
                hasTests = true;
            }
        }

        features.put("merge_count", (double) mergeCount);
        features.put("tests_missing", hasTests ? 0.0 : 1.0);
        features.put("author_frequency_inverse", authors.isEmpty() ? 1.0 : 1.0 / authors.size());

        return features;
    }
}
