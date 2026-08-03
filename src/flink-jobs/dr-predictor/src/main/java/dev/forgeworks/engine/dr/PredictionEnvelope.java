package dev.forgeworks.engine.dr;

import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;
import java.io.Serializable;
import java.time.Instant;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * Prediction output per PREDICTION_CONTRACT.md v0.1 §3 shape.
 *
 * <p>v0 constraints: single pool per §3.1; signal_role=recommendation (T2); type=score for the
 * placeholder predictor; estimand_id=deploy_slo_breach_60m_association_v0 per AB-033.
 *
 * <p>v0.2 changes (Codex round-1 loop, 2026-08-03):
 *
 * <ul>
 *   <li>{@code model_ref} field REPLACED by {@code model_id} + {@code model_version} per PC §4.2
 *       required fields. v0.1's {@code mlflow://...} URI scheme was invented; not in the contract.
 *   <li>Canonical pool: v0.1 emitted {@code ["deploy", "slo"]} which are estimand-topic-names, not
 *       pool names. v0.2 emits single canonical pool {@code "runtime"} (the estimand is about an
 *       SLO breach of a running service — runtime is the closest fit in the canonical set; final
 *       pool assignment to be confirmed against SC §3.1 canonical vocabulary in the real-impl PR).
 *   <li>Freshness field renamed: v0.1's {@code input_freshness_seconds} (a duration) collided with
 *       PC §3.3 {@code input_freshness} (a timestamp / age reference). v0.2 renames to {@code
 *       input_freshness_age_seconds} to avoid the collision. PC §3.3 timestamp semantics will be
 *       added in the real-impl PR alongside PC §3 field completeness.
 * </ul>
 *
 * <p>DEFERRED (not v0.2 apply-now scope; will land in real-impl PR post-scoping-approval): PC §3
 * required-field completeness (pools_contributing_now, structured slice per §3.5, correlation
 * claims per §3.4, revalidate_after per §4.3, human_readable_summary), governance envelope
 * propagation per §3.6, deterministic prediction identity, lifecycle events per §5. Each of these
 * requires wiring beyond a field-rename and is blocked on the RFC §5.1 model-bundle lock.
 */
@JsonInclude(JsonInclude.Include.NON_NULL)
public class PredictionEnvelope implements Serializable {

    private static final long serialVersionUID = 1L;
    private static final String CANONICAL_POOL = "runtime";

    @JsonProperty("event_id")
    private final String eventId;

    @JsonProperty("correlation_id")
    private final String correlationId;

    @JsonProperty("estimand_id")
    private final String estimandId;

    @JsonProperty("pools")
    private final List<String> pools;

    @JsonProperty("signal_role")
    private final String signalRole;

    @JsonProperty("type")
    private final String type;

    @JsonProperty("type_version")
    private final String typeVersion;

    @JsonProperty("value")
    private final Double value;

    @JsonProperty("abstain_reason")
    private final String abstainReason;

    @JsonProperty("horizon")
    private final String horizon;

    @JsonProperty("computed_at")
    private final String computedAt;

    @JsonProperty("valid_from")
    private final String validFrom;

    @JsonProperty("valid_until")
    private final String validUntil;

    @JsonProperty("slice")
    private final Map<String, String> slice;

    @JsonProperty("model_id")
    private final String modelId;

    @JsonProperty("model_version")
    private final String modelVersion;

    @JsonProperty("input_freshness_age_seconds")
    private final Long inputFreshnessAgeSeconds;

    /** Constructor for a scored prediction. */
    public static PredictionEnvelope score(
            String eventId,
            String correlationId,
            double value,
            Map<String, String> slice,
            String modelId,
            String modelVersion,
            long inputFreshnessAgeSeconds,
            Instant computedAt) {
        return new PredictionEnvelope(
                eventId,
                correlationId,
                "deploy_slo_breach_60m_association_v0",
                List.of(CANONICAL_POOL),
                "recommendation",
                "score",
                "1.0",
                value,
                null,
                "next_1h",
                computedAt.toString(),
                computedAt.toString(),
                computedAt.plusSeconds(3600).toString(),
                slice,
                modelId,
                modelVersion,
                inputFreshnessAgeSeconds);
    }

    /** Constructor for an abstain prediction. */
    public static PredictionEnvelope abstain(
            String eventId,
            String correlationId,
            String abstainReason,
            Map<String, String> slice,
            String modelId,
            String modelVersion,
            Instant computedAt) {
        return new PredictionEnvelope(
                eventId,
                correlationId,
                "deploy_slo_breach_60m_association_v0",
                List.of(CANONICAL_POOL),
                "recommendation",
                "abstain",
                "1.0",
                null,
                abstainReason,
                "next_1h",
                computedAt.toString(),
                computedAt.toString(),
                computedAt.plusSeconds(3600).toString(),
                slice,
                modelId,
                modelVersion,
                null);
    }

    @SuppressWarnings("PMD.ExcessiveParameterList")
    private PredictionEnvelope(
            String eventId,
            String correlationId,
            String estimandId,
            List<String> pools,
            String signalRole,
            String type,
            String typeVersion,
            Double value,
            String abstainReason,
            String horizon,
            String computedAt,
            String validFrom,
            String validUntil,
            Map<String, String> slice,
            String modelId,
            String modelVersion,
            Long inputFreshnessAgeSeconds) {
        this.eventId = eventId;
        this.correlationId = correlationId;
        this.estimandId = estimandId;
        this.pools = pools == null ? null : List.copyOf(pools);
        this.signalRole = signalRole;
        this.type = type;
        this.typeVersion = typeVersion;
        this.value = value;
        this.abstainReason = abstainReason;
        this.horizon = horizon;
        this.computedAt = computedAt;
        this.validFrom = validFrom;
        this.validUntil = validUntil;
        this.slice = slice == null ? null : Collections.unmodifiableMap(new HashMap<>(slice));
        this.modelId = modelId;
        this.modelVersion = modelVersion;
        this.inputFreshnessAgeSeconds = inputFreshnessAgeSeconds;
    }

    public String getEventId() {
        return eventId;
    }

    public String getCorrelationId() {
        return correlationId;
    }

    public String getEstimandId() {
        return estimandId;
    }

    public List<String> getPools() {
        return pools;
    }

    public String getSignalRole() {
        return signalRole;
    }

    public String getType() {
        return type;
    }

    public String getTypeVersion() {
        return typeVersion;
    }

    public Double getValue() {
        return value;
    }

    public String getAbstainReason() {
        return abstainReason;
    }

    public String getHorizon() {
        return horizon;
    }

    public String getComputedAt() {
        return computedAt;
    }

    public String getValidFrom() {
        return validFrom;
    }

    public String getValidUntil() {
        return validUntil;
    }

    public Map<String, String> getSlice() {
        return slice;
    }

    public String getModelId() {
        return modelId;
    }

    public String getModelVersion() {
        return modelVersion;
    }

    public Long getInputFreshnessAgeSeconds() {
        return inputFreshnessAgeSeconds;
    }
}
