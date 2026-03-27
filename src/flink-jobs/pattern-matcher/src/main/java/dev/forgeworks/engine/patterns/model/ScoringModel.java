package dev.forgeworks.engine.patterns.model;

import java.io.Serializable;
import java.util.List;
import java.util.Map;

/**
 * Interface for scoring models used in pattern detection.
 *
 * A ScoringModel takes a window of events and returns a score (0.0-1.0)
 * representing the probability/severity of a pattern match.
 *
 * Why an interface:
 * - MVP: WeightedScoringModel uses configurable weights (no ML)
 * - Phase 3: MLflow models implement this same interface
 * - Hot/Warm/Cold tiers all return ScoringModel instances
 * - Pattern Matcher doesn't care where the model came from
 *
 * Score interpretation:
 *   0.0 - 0.3 = low confidence (ignore)
 *   0.3 - 0.6 = medium confidence (log, may alert)
 *   0.6 - 0.8 = high confidence (alert)
 *   0.8 - 1.0 = critical confidence (alert + action)
 */
public interface ScoringModel extends Serializable {

    /** Unique model identifier (e.g., "risk-scorer-v1", "deploy-anomaly-v3") */
    String getModelId();

    /** Model version for tracking which model produced a score */
    String getVersion();

    /**
     * Score a window of event features.
     *
     * @param features Map of feature name → value extracted from the event window.
     *                 Examples: {"deploy_count": 5, "time_span_minutes": 8, "unique_authors": 1}
     * @return Score between 0.0 and 1.0
     */
    double score(Map<String, Double> features);

    /** Human-readable description of what this model scores */
    String getDescription();
}
