package dev.forgeworks.engine.router;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;
import java.io.Serializable;
import java.util.Map;

/**
 * Normalized event envelope — matches the schema produced by webhook-gateway.
 *
 * @schema schemas/event-envelope.schema.json
 *
 * Example:
 * {
 *   "event_id": "evt_abc123",
 *   "correlation_id": "corr_xyz789",
 *   "timestamp": "2026-01-23T10:30:00Z",
 *   "source": "github",
 *   "type": "push",
 *   "metadata": {"repository": "org/repo", "sender": "user"},
 *   "payload": { ... }
 * }
 */
@JsonIgnoreProperties(ignoreUnknown = true)
public class EventEnvelope implements Serializable {

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

    public String getEventId() { return eventId; }
    public void setEventId(String eventId) { this.eventId = eventId; }

    public String getCorrelationId() { return correlationId; }
    public void setCorrelationId(String correlationId) { this.correlationId = correlationId; }

    public String getTimestamp() { return timestamp; }
    public void setTimestamp(String timestamp) { this.timestamp = timestamp; }

    public String getSource() { return source; }
    public void setSource(String source) { this.source = source; }

    public String getType() { return type; }
    public void setType(String type) { this.type = type; }

    public Map<String, Object> getMetadata() { return metadata; }
    public void setMetadata(Map<String, Object> metadata) { this.metadata = metadata; }

    public Map<String, Object> getPayload() { return payload; }
    public void setPayload(Map<String, Object> payload) { this.payload = payload; }

    /**
     * Routing key for deduplication and partitioning.
     * Combines source + event_id for uniqueness.
     */
    public String routingKey() {
        return source + ":" + eventId;
    }

    @Override
    public String toString() {
        return "EventEnvelope{" +
                "eventId='" + eventId + '\'' +
                ", source='" + source + '\'' +
                ", type='" + type + '\'' +
                ", correlationId='" + correlationId + '\'' +
                '}';
    }
}
