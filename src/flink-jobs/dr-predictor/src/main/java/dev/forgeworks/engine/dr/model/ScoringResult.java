package dev.forgeworks.engine.dr.model;

import java.io.Serializable;
import java.util.Optional;

/**
 * Bounded result of a scoring attempt — carries either a score value OR an abstention reason.
 *
 * <p>v0.2 introduction (Codex round-1 loop, 2026-08-03) — type surface only. The full abstention
 * wiring (try/catch around {@link ScoringModel#score}, timeout budget, model-artifact-unavailable
 * detection) is deferred to the AB-029 Option A real-implementation PR that ships after RFC §5.1
 * dependency gate resolution and AB-032 verdict. This class exists now so callers can start using
 * the ScoringResult surface without waiting for the abstention-wiring landing.
 *
 * <p>Semantics: exactly one of {@link #getValue()} or {@link #getReason()} is populated. Consumers
 * MUST branch on {@link #isAbstention()} before reading either. Per RFC §6.3 G9 + PC §3 abstention
 * contract, a scoring failure MUST produce an abstention with a documented reason (never a silent
 * degraded prediction).
 *
 * <p>Reason codes (v0.2 initial set, extensible in real-impl PR):
 *
 * <ul>
 *   <li>{@code model_unavailable} — model artifact could not be loaded / resolved.
 *   <li>{@code scoring_timeout} — score() call exceeded budget.
 *   <li>{@code scoring_error} — score() threw an exception.
 *   <li>{@code input_stale} — freshness gate rejected input (currently handled at DrPredictorJob
 *       level, may migrate here in real-impl PR).
 *   <li>{@code input_freshness_underspecified} — freshness metadata missing or malformed.
 * </ul>
 */
public final class ScoringResult implements Serializable {

    private static final long serialVersionUID = 1L;

    private final Double value;
    private final String reason;

    private ScoringResult(Double value, String reason) {
        this.value = value;
        this.reason = reason;
    }

    public static ScoringResult ofScore(double value) {
        if (value < 0.0 || value > 1.0) {
            throw new IllegalArgumentException("value must be in [0.0, 1.0], got " + value);
        }
        return new ScoringResult(value, null);
    }

    public static ScoringResult abstain(String reason) {
        if (reason == null || reason.isBlank()) {
            throw new IllegalArgumentException("reason must be non-empty for abstention");
        }
        return new ScoringResult(null, reason);
    }

    public boolean isAbstention() {
        return reason != null;
    }

    public Optional<Double> getValue() {
        return Optional.ofNullable(value);
    }

    public Optional<String> getReason() {
        return Optional.ofNullable(reason);
    }
}
