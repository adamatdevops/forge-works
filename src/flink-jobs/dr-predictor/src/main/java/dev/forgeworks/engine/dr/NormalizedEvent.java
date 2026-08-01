package dev.forgeworks.engine.dr;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;
import java.io.Serializable;
import java.util.Collections;
import java.util.HashMap;
import java.util.Map;

/**
 * Normalized event as read from forge.events.normalized.v1.
 *
 * <p>Same shape as pattern-matcher's EventEnvelope but scoped to the fields the DR predictor
 * consumes. Fields not needed for scoring are dropped via {@link JsonIgnoreProperties}.
 */
@JsonIgnoreProperties(ignoreUnknown = true)
public class NormalizedEvent implements Serializable {

    private static final long serialVersionUID = 1L;

    @JsonProperty("event_id")
    private String eventId;

    @JsonProperty("correlation_id")
    private String correlationId;

    private String timestamp;
    private String source;
    private String type;
    private Map<String, Object> metadata;
    private Map<String, Object> payload;

    public NormalizedEvent() {}

    public String getEventId() {
        return eventId;
    }

    public void setEventId(String eventId) {
        this.eventId = eventId;
    }

    public String getCorrelationId() {
        return correlationId;
    }

    public void setCorrelationId(String correlationId) {
        this.correlationId = correlationId;
    }

    public String getTimestamp() {
        return timestamp;
    }

    public void setTimestamp(String timestamp) {
        this.timestamp = timestamp;
    }

    public String getSource() {
        return source;
    }

    public void setSource(String source) {
        this.source = source;
    }

    public String getType() {
        return type;
    }

    public void setType(String type) {
        this.type = type;
    }

    public Map<String, Object> getMetadata() {
        return metadata == null ? null : Collections.unmodifiableMap(metadata);
    }

    public void setMetadata(Map<String, Object> metadata) {
        this.metadata = metadata == null ? null : new HashMap<>(metadata);
    }

    public Map<String, Object> getPayload() {
        return payload == null ? null : Collections.unmodifiableMap(payload);
    }

    public void setPayload(Map<String, Object> payload) {
        this.payload = payload == null ? null : new HashMap<>(payload);
    }

    /** True when this event is a deploy marker the DR predictor should score. */
    public boolean isDeploy() {
        return "deployment".equals(type) || "deploy".equals(type);
    }

    /**
     * Slice key: (service, environment) — matches the deploy_slo_breach_60m_association_v0
     * estimand's slice shape.
     */
    public String sliceKey() {
        String service = "unknown";
        String environment = "unknown";
        if (metadata != null) {
            Object s = metadata.get("service");
            Object e = metadata.get("environment");
            if (s != null) service = s.toString();
            if (e != null) environment = e.toString();
        }
        return service + ":" + environment;
    }

    @Override
    public String toString() {
        return "NormalizedEvent{eventId='"
                + eventId
                + "', source='"
                + source
                + "', type='"
                + type
                + "'}";
    }
}
