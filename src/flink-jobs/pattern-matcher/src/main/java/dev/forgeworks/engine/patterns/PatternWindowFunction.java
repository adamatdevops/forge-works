package dev.forgeworks.engine.patterns;

import dev.forgeworks.engine.patterns.model.ModelLoader;
import dev.forgeworks.engine.patterns.model.ScoringModel;
import org.apache.flink.api.common.state.ValueState;
import org.apache.flink.api.common.state.ValueStateDescriptor;
import org.apache.flink.api.common.typeinfo.TypeInformation;
import org.apache.flink.configuration.Configuration;
import org.apache.flink.streaming.api.functions.KeyedProcessFunction;
import org.apache.flink.util.Collector;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.Serializable;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

/**
 * Stateful pattern evaluation using incremental counters with timer-based reset.
 *
 * How aging works:
 * - Each key gets a processing-time timer set 10 minutes after the first event
 * - When the timer fires, counters are cleared (fresh window starts)
 * - Under continuous traffic, counters reset every 10 min (true sliding semantics)
 * - Under no traffic, state TTL (15 min) cleans up the entry entirely
 *
 * eventIds are capped at MAX_EVENT_IDS to prevent unbounded growth.
 */
public class PatternWindowFunction
        extends KeyedProcessFunction<String, EventEnvelope, PatternAlert> {

    private static final Logger LOG = LoggerFactory.getLogger(PatternWindowFunction.class);
    private static final long WINDOW_DURATION_MS = 10 * 60 * 1000; // 10 minutes
    private static final int MAX_EVENT_IDS = 50;

    private transient ValueState<EventCounters> countersState;
    private transient ValueState<Long> timerState;  // tracks active timer timestamp
    private transient ModelLoader modelLoader;

    private static final Map<String, String> PATTERN_TO_MODEL = new HashMap<>() {{
        put("PAT-DEPLOY-001", "rapid-deploy-scorer");
        put("PAT-K8S-001", "crash-loop-scorer");
        put("PAT-CI-001", "ci-skip-scorer");
    }};

    @Override
    public void open(Configuration parameters) {
        countersState = getRuntimeContext().getState(
                new ValueStateDescriptor<>("event-counters", TypeInformation.of(EventCounters.class)));

        timerState = getRuntimeContext().getState(
                new ValueStateDescriptor<>("window-timer", TypeInformation.of(Long.class)));

        modelLoader = new ModelLoader();
        modelLoader.initialize();
        LOG.info("PatternWindowFunction initialized (incremental counters + timer reset) — models: {}",
                modelLoader.getHotModelIds());
    }

    @Override
    public void close() {
        if (modelLoader != null) {
            modelLoader.close();
        }
    }

    @Override
    public void processElement(EventEnvelope event, Context ctx, Collector<PatternAlert> out)
            throws Exception {
        // Get or create counters
        EventCounters counters = countersState.value();
        if (counters == null) {
            counters = new EventCounters();
        }

        // Register window reset timer on first event in this window
        Long existingTimer = timerState.value();
        if (existingTimer == null) {
            long timerTs = ctx.timerService().currentProcessingTime() + WINDOW_DURATION_MS;
            ctx.timerService().registerProcessingTimeTimer(timerTs);
            timerState.update(timerTs);
        }

        // Incremental update — O(1)
        counters.update(event);
        countersState.update(counters);

        // Evaluate rules
        String groupKey = ctx.getCurrentKey();
        List<PatternAlert> alerts = evaluateRules(groupKey, counters);

        for (PatternAlert alert : alerts) {
            enrichWithScore(alert, counters);
            LOG.info("Pattern matched: {} — {} (group: {}, events: {}, score: {})",
                    alert.getPatternId(), alert.getPatternName(),
                    alert.getGroupKey(), alert.getEventCount(),
                    alert.getContext().get("model_score"));
            out.collect(alert);
        }
    }

    @Override
    public void onTimer(long timestamp, OnTimerContext ctx, Collector<PatternAlert> out)
            throws Exception {
        // Window expired — reset counters for fresh 10-minute window
        countersState.clear();
        timerState.clear();
        LOG.debug("Window reset for key: {}", ctx.getCurrentKey());
    }

    private List<PatternAlert> evaluateRules(String groupKey, EventCounters c) {
        List<PatternAlert> alerts = new ArrayList<>();

        if (c.syncCount > 3) {
            alerts.add(PatternAlert.create(
                    "PAT-DEPLOY-001", "Rapid Successive Deployments", "high",
                    c.syncCount + " deployments detected in window for " + groupKey,
                    "argocd", groupKey, c.syncCount, 10,
                    new ArrayList<>(c.eventIds),
                    new HashMap<>() {{ put("threshold", 3); put("actual", c.syncCount); }}
            ));
        }

        if (c.crashCount > 3) {
            alerts.add(PatternAlert.create(
                    "PAT-K8S-001", "Pod Crash Loop Detected", "critical",
                    c.crashCount + " crash/restart events for " + groupKey,
                    "kubernetes", groupKey, c.crashCount, 5,
                    new ArrayList<>(c.eventIds),
                    new HashMap<>() {{ put("threshold", 3); put("actual", c.crashCount); }}
            ));
        }

        if (c.mergeCount > 0 && c.testCount == 0) {
            alerts.add(PatternAlert.create(
                    "PAT-CI-001", "PR Merged Without Tests", "medium",
                    "PR merged without test/check run detected for " + groupKey,
                    "github", groupKey, c.mergeCount, 10,
                    new ArrayList<>(c.eventIds),
                    new HashMap<>() {{ put("merge_count", c.mergeCount); put("tests_detected", false); }}
            ));
        }

        return alerts;
    }

    private void enrichWithScore(PatternAlert alert, EventCounters c) {
        String modelId = PATTERN_TO_MODEL.get(alert.getPatternId());
        if (modelId == null) return;

        ScoringModel model = modelLoader.loadModel(modelId);
        if (model == null) return;

        Map<String, Double> features = c.toFeatures();
        double score = model.score(features);

        alert.getContext().put("model_score", score);
        alert.getContext().put("model_id", model.getModelId());
        alert.getContext().put("model_version", model.getVersion());
        alert.getContext().put("features", new HashMap<>(features));
    }

    /**
     * Incremental counters — O(1) update per event.
     * Cleared by onTimer every 10 minutes for true windowing semantics.
     * eventIds capped at MAX_EVENT_IDS to prevent unbounded growth.
     */
    public static class EventCounters implements Serializable {
        public int eventCount = 0;
        public int syncCount = 0;
        public int crashCount = 0;
        public int mergeCount = 0;
        public int testCount = 0;
        public int pushCount = 0;
        public Set<String> authors = new HashSet<>();
        public List<String> eventIds = new ArrayList<>();

        public void update(EventEnvelope event) {
            eventCount++;
            if (event.getEventId() != null && eventIds.size() < MAX_EVENT_IDS) {
                eventIds.add(event.getEventId());
            }

            String type = event.getType();
            if (type == null) return;

            if (type.contains("sync")) syncCount++;
            if (type.contains("crash") || type.contains("restart")
                    || type.contains("backoff") || type.contains("failed")) crashCount++;
            if (type.contains("merged")) mergeCount++;
            if (type.contains("check_run") || type.contains("check_suite")
                    || type.contains("workflow_run") || type.contains("status")) testCount++;
            if (type.contains("push")) pushCount++;

            if (event.getMetadata() != null) {
                Object sender = event.getMetadata().get("sender");
                if (sender != null) authors.add(sender.toString());
            }
        }

        public Map<String, Double> toFeatures() {
            Map<String, Double> f = new HashMap<>();
            f.put("event_count", (double) eventCount);
            f.put("sync_count", (double) syncCount);
            f.put("crash_count", (double) crashCount);
            f.put("merge_count", (double) mergeCount);
            f.put("test_count", (double) testCount);
            f.put("push_count", (double) pushCount);
            f.put("unique_authors", (double) authors.size());
            f.put("events_per_minute", eventCount > 0 ? eventCount / 10.0 : 0.0);
            f.put("author_concentration", authors.isEmpty() ? 1.0 : 1.0 / authors.size());
            f.put("time_span_minutes", 10.0);
            f.put("deploy_count", (double) syncCount);
            f.put("tests_missing", testCount == 0 ? 1.0 : 0.0);
            f.put("restart_frequency", crashCount > 0 ? crashCount / 10.0 : 0.0);
            f.put("unique_pods_inverse", authors.isEmpty() ? 1.0 : 1.0 / authors.size());
            f.put("time_span_inverse", eventCount > 1 ? eventCount / 10.0 : 0.0);
            f.put("unique_authors_inverse", authors.isEmpty() ? 1.0 : 1.0 / authors.size());
            f.put("author_frequency_inverse", authors.isEmpty() ? 1.0 : 1.0 / authors.size());
            return f;
        }
    }
}
