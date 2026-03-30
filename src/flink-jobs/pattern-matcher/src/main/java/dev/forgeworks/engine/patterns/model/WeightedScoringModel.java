package dev.forgeworks.engine.patterns.model;

import java.util.HashMap;
import java.util.Map;

/**
 * MVP scoring model using configurable feature weights.
 *
 * How it works:
 *   score = sum(feature_value * weight) / max_possible_score
 *   Result is clamped to [0.0, 1.0]
 *
 * This is NOT machine learning — it's a weighted linear combination.
 * But it implements the same ScoringModel interface that future ML models
 * will use, so the Pattern Matcher doesn't need to change when we swap
 * in real models from Phase 3 (Airflow + MLflow).
 *
 * Why weighted scoring over pure rules:
 * - Rules are binary (match/no-match). Scoring gives granularity.
 * - "3 deploys = alert" vs "3 deploys from 1 author in 5 min = 0.85 score"
 * - Enables threshold tuning without code changes
 * - Scores can be logged for future ML training data (Phase 3)
 *
 * Example:
 *   Model: "rapid-deploy-scorer"
 *   Weights: {deploy_count: 0.4, time_span_inverse: 0.3, unique_authors_inverse: 0.3}
 *   Features: {deploy_count: 5.0, time_span_inverse: 0.8, unique_authors_inverse: 1.0}
 *   Score: (5*0.4 + 0.8*0.3 + 1.0*0.3) / normalization → 0.87
 */
public class WeightedScoringModel implements ScoringModel {

    private final String modelId;
    private final String version;
    private final String description;
    private final Map<String, Double> weights;
    private final double normalizationFactor;

    public WeightedScoringModel(String modelId, String version, String description,
                                 Map<String, Double> weights, double normalizationFactor) {
        this.modelId = modelId;
        this.version = version;
        this.description = description;
        this.weights = new HashMap<>(weights);
        this.normalizationFactor = normalizationFactor;
    }

    @Override
    public String getModelId() { return modelId; }

    @Override
    public String getVersion() { return version; }

    @Override
    public String getDescription() { return description; }

    /** Direct access to weight map for MLflow reload mapping. */
    public Map<String, Double> getWeights() { return new HashMap<>(weights); }

    @Override
    public double score(Map<String, Double> features) {
        double rawScore = 0.0;
        for (Map.Entry<String, Double> entry : weights.entrySet()) {
            Double featureValue = features.get(entry.getKey());
            if (featureValue != null) {
                rawScore += featureValue * entry.getValue();
            }
        }
        // Normalize and clamp to [0.0, 1.0]
        double normalized = rawScore / normalizationFactor;
        return Math.max(0.0, Math.min(1.0, normalized));
    }

    @Override
    public String toString() {
        return "WeightedScoringModel{id='" + modelId + "', version='" + version + "'}";
    }
}
