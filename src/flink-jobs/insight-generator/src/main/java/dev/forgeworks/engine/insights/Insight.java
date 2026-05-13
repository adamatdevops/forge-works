package dev.forgeworks.engine.insights;

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
 * Consolidated, actionable insight — the final output of the engine.
 *
 * <p>An Insight is different from a PatternAlert: - Alert = "this pattern was detected" (raw, may
 * repeat) - Insight = "here's what happened, why it matters, and what to do" (deduplicated,
 * actionable)
 *
 * <p>Consumers: UI dashboard, Slack notifications, automated remediation (Phase 4)
 */
public class Insight implements Serializable {

    private static final long serialVersionUID = 1L;

    @JsonProperty("insight_id")
    private String insightId;

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

    private List<String> recommendations;

    @JsonProperty("alert_count")
    private int alertCount;

    @JsonProperty("first_seen")
    private String firstSeen;

    @JsonProperty("last_seen")
    private String lastSeen;

    @JsonProperty("model_score")
    private Double modelScore;

    @JsonProperty("trigger_event_ids")
    private List<String> triggerEventIds;

    private Map<String, Object> context;

    public Insight() {
        this.insightId = "ins_" + UUID.randomUUID().toString().substring(0, 12);
        this.timestamp = Instant.now().toString();
        this.recommendations = new ArrayList<>();
        this.triggerEventIds = new ArrayList<>();
        this.context = new HashMap<>();
    }

    public static Insight fromAlert(PatternAlert alert) {
        Insight insight = new Insight();
        insight.patternId = alert.getPatternId();
        insight.patternName = alert.getPatternName();
        insight.severity = alert.getSeverity();
        insight.message = alert.getMessage();
        insight.source = alert.getSource();
        insight.groupKey = alert.getGroupKey();
        insight.alertCount = 1;
        insight.firstSeen = alert.getTimestamp();
        insight.lastSeen = alert.getTimestamp();
        if (alert.getTriggerEventIds() != null) {
            insight.triggerEventIds = new ArrayList<>(alert.getTriggerEventIds());
        }
        if (alert.getContext() != null) {
            insight.context = new HashMap<>(alert.getContext());
            Object score = alert.getContext().get("model_score");
            if (score instanceof Number) {
                insight.modelScore = ((Number) score).doubleValue();
            }
        }
        return insight;
    }

    // Getters and setters
    public String getInsightId() {
        return insightId;
    }

    public void setInsightId(String insightId) {
        this.insightId = insightId;
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

    public List<String> getRecommendations() {
        return recommendations == null ? null : Collections.unmodifiableList(recommendations);
    }

    public void setRecommendations(List<String> recommendations) {
        this.recommendations = recommendations == null ? null : new ArrayList<>(recommendations);
    }

    public int getAlertCount() {
        return alertCount;
    }

    public void setAlertCount(int alertCount) {
        this.alertCount = alertCount;
    }

    public String getFirstSeen() {
        return firstSeen;
    }

    public void setFirstSeen(String firstSeen) {
        this.firstSeen = firstSeen;
    }

    public String getLastSeen() {
        return lastSeen;
    }

    public void setLastSeen(String lastSeen) {
        this.lastSeen = lastSeen;
    }

    public Double getModelScore() {
        return modelScore;
    }

    public void setModelScore(Double modelScore) {
        this.modelScore = modelScore;
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

    @Override
    public String toString() {
        return "Insight{id='"
                + insightId
                + "', pattern='"
                + patternName
                + "', severity='"
                + severity
                + "', alerts="
                + alertCount
                + "}";
    }
}
