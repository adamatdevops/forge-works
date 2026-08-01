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
 */
@JsonInclude(JsonInclude.Include.NON_NULL)
public class PredictionEnvelope implements Serializable {

    private static final long serialVersionUID = 1L;

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

    @JsonProperty("model_ref")
    private final String modelRef;

    @JsonProperty("input_freshness_seconds")
    private final Long inputFreshnessSeconds;

    /** Constructor for a scored prediction. */
    public static PredictionEnvelope score(
            String eventId,
            String correlationId,
            double value,
            Map<String, String> slice,
            String modelRef,
            long inputFreshnessSeconds,
            Instant computedAt) {
        return new PredictionEnvelope(
                eventId,
                correlationId,
                "deploy_slo_breach_60m_association_v0",
                List.of("deploy", "slo"),
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
                modelRef,
                inputFreshnessSeconds);
    }

    /** Constructor for an abstain prediction. */
    public static PredictionEnvelope abstain(
            String eventId,
            String correlationId,
            String abstainReason,
            Map<String, String> slice,
            String modelRef,
            Instant computedAt) {
        return new PredictionEnvelope(
                eventId,
                correlationId,
                "deploy_slo_breach_60m_association_v0",
                List.of("deploy", "slo"),
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
                modelRef,
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
            String modelRef,
            Long inputFreshnessSeconds) {
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
        this.modelRef = modelRef;
        this.inputFreshnessSeconds = inputFreshnessSeconds;
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

    public String getModelRef() {
        return modelRef;
    }

    public Long getInputFreshnessSeconds() {
        return inputFreshnessSeconds;
    }
}
