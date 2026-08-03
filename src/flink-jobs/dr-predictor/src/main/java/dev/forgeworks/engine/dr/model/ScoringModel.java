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
 *
 * <p>v0.2 (Codex round-1 loop, 2026-08-03): {@code getModelRef} replaced with {@link #getModelId}
 * and {@link #getModelVersion} to align with PREDICTION_CONTRACT.md §4.2 required fields ({@code
 * model_id}, {@code model_version}). The v0.1 {@code mlflow://...} URI scheme was invented and does
 * not appear in the contract.
 */
public interface ScoringModel extends Serializable {

    /**
     * MLflow-anchored stable identifier for the model. Populated into every prediction's {@code
     * model_id} field per PC §4.2.
     */
    String getModelId();

    /**
     * Semantic version of the model. Populated into every prediction's {@code model_version} field
     * per PC §4.2. For placeholder / non-registry-backed models, the version string SHOULD carry a
     * suffix indicating provenance (e.g. {@code 0.1.0-placeholder}).
     */
    String getModelVersion();

    /** Score a feature map. Return in [0.0, 1.0]. */
    double score(Map<String, Double> features);
}
