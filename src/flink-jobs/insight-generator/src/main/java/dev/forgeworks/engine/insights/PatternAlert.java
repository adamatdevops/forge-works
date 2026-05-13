package dev.forgeworks.engine.insights;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;
import java.io.Serializable;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * Input model — matches the PatternAlert schema from Pattern Matcher.
 *
 * @schema schemas/pattern-alert.schema.json
 */
@JsonIgnoreProperties(ignoreUnknown = true)
public class PatternAlert implements Serializable {

    private static final long serialVersionUID = 1L;

    @JsonProperty("alert_id")
    private String alertId;

    @JsonProperty("pattern_id")
    private String patternId;

    @JsonProperty("pattern_name")
    private String patternName;

    private String severity;
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

    public PatternAlert() {}

    public String getAlertId() {
        return alertId;
    }

    public void setAlertId(String alertId) {
        this.alertId = alertId;
    }

    public String getPatternId() {
        return patternId;
    }

    public void setPatternId(String patternId) {
        this.patternId = patternId;
    }

    public String getPatternName() {
        return patternName;
    }

    public void setPatternName(String patternName) {
        this.patternName = patternName;
    }

    public String getSeverity() {
        return severity;
    }

    public void setSeverity(String severity) {
        this.severity = severity;
    }

    public String getMessage() {
        return message;
    }

    public void setMessage(String message) {
        this.message = message;
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

    public String getGroupKey() {
        return groupKey;
    }

    public void setGroupKey(String groupKey) {
        this.groupKey = groupKey;
    }

    public int getEventCount() {
        return eventCount;
    }

    public void setEventCount(int eventCount) {
        this.eventCount = eventCount;
    }

    public int getWindowMinutes() {
        return windowMinutes;
    }

    public void setWindowMinutes(int windowMinutes) {
        this.windowMinutes = windowMinutes;
    }

    public List<String> getTriggerEventIds() {
        return triggerEventIds == null ? null : Collections.unmodifiableList(triggerEventIds);
    }

    public void setTriggerEventIds(List<String> triggerEventIds) {
        this.triggerEventIds = triggerEventIds == null ? null : new ArrayList<>(triggerEventIds);
    }

    public Map<String, Object> getContext() {
        return context == null ? null : Collections.unmodifiableMap(context);
    }

    public void setContext(Map<String, Object> context) {
        this.context = context == null ? null : new HashMap<>(context);
    }

    /** Dedup key: same pattern + same group = same logical alert */
    public String dedupKey() {
        return patternId + ":" + groupKey;
    }
}
