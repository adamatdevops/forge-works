package dev.forgeworks.engine.insights;

import java.util.ArrayList;
import java.util.List;
import org.apache.flink.api.common.state.StateTtlConfig;
import org.apache.flink.api.common.state.ValueState;
import org.apache.flink.api.common.state.ValueStateDescriptor;
import org.apache.flink.api.common.time.Time;
import org.apache.flink.api.common.typeinfo.TypeInformation;
import org.apache.flink.configuration.Configuration;
import org.apache.flink.streaming.api.functions.KeyedProcessFunction;
import org.apache.flink.util.Collector;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * Deduplicates alerts and produces consolidated insights with recommendations.
 *
 * <p>How deduplication works: - Alerts are keyed by pattern_id:group_key (dedupKey) - State stores
 * the last emitted Insight for each key - Cooldown: 5 minutes — if an insight was emitted within 5
 * min, suppress - After cooldown expires (TTL), next alert creates a fresh insight
 *
 * <p>Why 5-minute cooldown: - Without it, every event through the Pattern Matcher fires a new alert
 * (e.g., 10 merges without tests = 10 alerts for the same repo) - With cooldown: first merge
 * triggers alert, next 4 within 5 min are counted but suppressed. After 5 min, if still happening,
 * re-alert. - The alert_count in the insight shows how many were suppressed
 *
 * <p>State sizing: - Each entry: ~1KB (serialized Insight) - Expected keys: ~50-200 (pattern:group
 * combinations) - Total: ~200KB (negligible)
 */
public class InsightAggregator extends KeyedProcessFunction<String, PatternAlert, Insight> {

    private static final long serialVersionUID = 1L;
    private static final Logger LOG = LoggerFactory.getLogger(InsightAggregator.class);
    private transient ValueState<Insight> lastInsightState;

    @Override
    public void open(Configuration parameters) {
        StateTtlConfig ttlConfig =
                StateTtlConfig.newBuilder(Time.minutes(5))
                        .setUpdateType(StateTtlConfig.UpdateType.OnCreateAndWrite)
                        .cleanupFullSnapshot()
                        .build();

        ValueStateDescriptor<Insight> descriptor =
                new ValueStateDescriptor<>("last-insight", TypeInformation.of(Insight.class));
        descriptor.enableTimeToLive(ttlConfig);

        lastInsightState = getRuntimeContext().getState(descriptor);
    }

    @Override
    public void processElement(PatternAlert alert, Context ctx, Collector<Insight> out)
            throws Exception {
        Insight existing = lastInsightState.value();

        if (existing != null) {
            // Within cooldown — aggregate but suppress
            existing.setAlertCount(existing.getAlertCount() + 1);
            existing.setLastSeen(alert.getTimestamp());
            if (alert.getTriggerEventIds() != null) {
                List<String> existingIds = existing.getTriggerEventIds();
                List<String> combined =
                        existingIds == null ? new ArrayList<>() : new ArrayList<>(existingIds);
                combined.addAll(alert.getTriggerEventIds());
                existing.setTriggerEventIds(combined);
            }
            lastInsightState.update(existing);

            LOG.debug(
                    "Alert suppressed (cooldown): {} for {} — total: {}",
                    alert.getPatternId(),
                    alert.getGroupKey(),
                    existing.getAlertCount());
            return;
        }

        // New insight — first alert after cooldown expired
        Insight insight = Insight.fromAlert(alert);

        // Add recommendations
        List<String> recs = Recommendations.forPattern(alert.getPatternId(), insight);
        insight.setRecommendations(recs);

        // Store for dedup
        lastInsightState.update(insight);

        LOG.info(
                "Insight generated: {} — {} (group: {}, score: {})",
                insight.getPatternId(),
                insight.getPatternName(),
                insight.getGroupKey(),
                insight.getModelScore());

        out.collect(insight);
    }
}
