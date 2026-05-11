package dev.forgeworks.engine.patterns;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.io.Serializable;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

/**
 * Output of the Pattern Matcher — a detected pattern with context.
 *
 * @schema schemas/pattern-alert.schema.json
 *     <p>Published to forge.jobs.pending for downstream action (notifications, automated
 *     remediation, dashboard updates).
 */
public class PatternAlert implements Serializable {

    private static final long serialVersionUID = 1L;

    @JsonProperty("alert_id")
    private String alertId;

    @JsonProperty("pattern_id")
    private String patternId;

    @JsonProperty("pattern_name")
    private String patternName;

    private String severity; // critical, high, medium, low
    private String message;
    private String timestamp;
    private String source;

    @JsonProperty("group_key")
    private String groupKey;

    @JsonProperty("event_count")
    private int eventCount;

    @JsonProperty("window_minutes")
    private int windowMinutes;

    @JsonProperty("trigger_event_ids")
    private List<String> triggerEventIds;

    private Map<String, Object> context;

    public PatternAlert() {
        this.alertId = "alert_" + UUID.randomUUID().toString().substring(0, 12);
        this.timestamp = Instant.now().toString();
    }

    public static PatternAlert create(
            String patternId,
            String patternName,
            String severity,
            String message,
            String source,
            String groupKey,
            int eventCount,
            int windowMinutes,
            List<String> triggerEventIds,
            Map<String, Object> context) {
        PatternAlert alert = new PatternAlert();
        alert.patternId = patternId;
        alert.patternName = patternName;
        alert.severity = severity;
        alert.message = message;
        alert.source = source;
        alert.groupKey = groupKey;
        alert.eventCount = eventCount;
        // Use mutable collections — Flink's Kryo serializer cannot copy immutable ones
        alert.windowMinutes = windowMinutes;
        alert.triggerEventIds = new java.util.ArrayList<>(triggerEventIds);
        alert.context = new java.util.HashMap<>(context);
        return alert;
    }

    // Getters
    public String getAlertId() {
        return alertId;
    }

    public String getPatternId() {
        return patternId;
    }

    public String getPatternName() {
        return patternName;
    }

    public String getSeverity() {
        return severity;
    }

    public String getMessage() {
        return message;
    }

    public String getTimestamp() {
        return timestamp;
    }

    public String getSource() {
        return source;
    }

    public String getGroupKey() {
        return groupKey;
    }

    public int getEventCount() {
        return eventCount;
    }

    public int getWindowMinutes() {
        return windowMinutes;
    }

    public List<String> getTriggerEventIds() {
        return triggerEventIds == null ? null : Collections.unmodifiableList(triggerEventIds);
    }

    public Map<String, Object> getContext() {
        return context == null ? null : Collections.unmodifiableMap(context);
    }

    // Setters for deserialization
    public void setAlertId(String alertId) {
        this.alertId = alertId;
    }

    public void setPatternId(String patternId) {
        this.patternId = patternId;
    }

    public void setPatternName(String patternName) {
        this.patternName = patternName;
    }

    public void setSeverity(String severity) {
        this.severity = severity;
    }

    public void setMessage(String message) {
        this.message = message;
    }

    public void setTimestamp(String timestamp) {
        this.timestamp = timestamp;
    }

    public void setSource(String source) {
        this.source = source;
    }

    public void setGroupKey(String groupKey) {
        this.groupKey = groupKey;
    }

    public void setEventCount(int eventCount) {
        this.eventCount = eventCount;
    }

    public void setWindowMinutes(int windowMinutes) {
        this.windowMinutes = windowMinutes;
    }

    public void setTriggerEventIds(List<String> triggerEventIds) {
        this.triggerEventIds = triggerEventIds == null ? null : new ArrayList<>(triggerEventIds);
    }

    public void setContext(Map<String, Object> context) {
        this.context = context == null ? null : new HashMap<>(context);
    }

    @Override
    public String toString() {
        return "PatternAlert{alertId='"
                + alertId
                + "', pattern='"
                + patternName
                + "', severity='"
                + severity
                + "', group='"
                + groupKey
                + "'}";
    }
}
