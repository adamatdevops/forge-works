package dev.forgeworks.engine.patterns;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;
import java.io.Serializable;
import java.util.Collections;
import java.util.HashMap;
import java.util.Map;

/**
 * Normalized event envelope — same schema as Event Router produces.
 *
 * @schema schemas/event-envelope.schema.json
 */
@JsonIgnoreProperties(ignoreUnknown = true)
public class EventEnvelope implements Serializable {

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

    public EventEnvelope() {}

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

    public String groupKey() {
        if (metadata != null) {
            Object repo = metadata.get("repository");
            if (repo != null) return source + ":" + repo;
            Object ns = metadata.get("namespace");
            Object name = metadata.get("name");
            if (ns != null && name != null) return source + ":" + ns + "/" + name;
        }
        return source + ":default";
    }

    @Override
    public String toString() {
        return "EventEnvelope{eventId='"
                + eventId
                + "', source='"
                + source
                + "', type='"
                + type
                + "'}";
    }
}
