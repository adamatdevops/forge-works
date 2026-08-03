package dev.forgeworks.engine.dr.model;

import java.util.Map;

/**
 * Placeholder scoring model — returns a fixed constant regardless of features.
 *
 * <p>Exists so the sibling-Flink prototype has a runnable pipeline before AB-028 delivers a real
 * calibrated model. The value 0.05 is the observed base-rate placeholder from AB-028 RFC §4.4.
 *
 * <p>WHY a constant rather than a random or a rule-based baseline: constants make it trivial to
 * verify the pipeline (deserialize → extract features → score → serialize → publish) end-to-end
 * without confounding the AB-029 placement measurement with predictor variance. The rules-baseline
 * from AB-028 is deliberately NOT reused here — that baseline is part of the AB-028 spike's own
 * evidence set and lives in Python.
 *
 * <p>v0.2 (Codex round-1 loop, 2026-08-03): {@code model_id} + {@code model_version} replace the
 * v0.1 invented {@code mlflow://models/dr-predictor/placeholder-constant/0.1.0} URI. The v0.1
 * scheme was not backed by any real MLflow-registered model — it was a URI-shaped label. The v0.2
 * fields honestly declare the placeholder: {@code MODEL_ID = "placeholder-constant"} with {@code
 * MODEL_VERSION = "0.1.0-placeholder"} explicitly noting the artifact is NOT in the MLflow
 * registry. The AB-028 spike will produce a real MLflow-anchored model with a real registered-model
 * version.
 */
public final class ConstantPredictor implements ScoringModel {

    private static final long serialVersionUID = 1L;
    private static final String MODEL_ID = "placeholder-constant";
    private static final String MODEL_VERSION = "0.1.0-placeholder";
    private static final double DEFAULT_VALUE = 0.05;

    private final double value;

    public ConstantPredictor() {
        this(DEFAULT_VALUE);
    }

    public ConstantPredictor(double value) {
        if (value < 0.0 || value > 1.0) {
            throw new IllegalArgumentException("value must be in [0.0, 1.0], got " + value);
        }
        this.value = value;
    }

    @Override
    public String getModelId() {
        return MODEL_ID;
    }

    @Override
    public String getModelVersion() {
        return MODEL_VERSION;
    }

    @Override
    public double score(Map<String, Double> features) {
        return value;
    }
}
