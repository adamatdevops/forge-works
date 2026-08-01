package dev.forgeworks.engine.dr.model;

import java.io.Serializable;
import java.util.Map;

/**
 * Scoring interface every DR predictor implementation satisfies.
 *
 * <p>Parallels pattern-matcher's ScoringModel but scoped to the DR estimand's output shape: scored
 * predictions carry a value in [0.0, 1.0] representing the probability of an SLO breach observed
 * within the horizon window per deploy_slo_breach_60m_association_v0.
 *
 * <p>The AB-028 spike will produce a real MLflow-loaded implementation; the placeholder in this
 * module ({@link ConstantPredictor}) exists so the AB-029 sibling-Flink prototype has a runnable
 * pipeline before the spike executes.
 */
public interface ScoringModel extends Serializable {

    /** Stable identifier logged into every prediction's model_ref. */
    String getModelRef();

    /** Score a feature map. Return in [0.0, 1.0]. */
    double score(Map<String, Double> features);
}
