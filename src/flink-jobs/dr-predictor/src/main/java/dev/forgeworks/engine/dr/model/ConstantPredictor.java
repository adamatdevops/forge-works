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
 */
public final class ConstantPredictor implements ScoringModel {

    private static final long serialVersionUID = 1L;
    private static final String MODEL_REF =
            "mlflow://models/dr-predictor/placeholder-constant/0.1.0";
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
    public String getModelRef() {
        return MODEL_REF;
    }

    @Override
    public double score(Map<String, Double> features) {
        return value;
    }
}
