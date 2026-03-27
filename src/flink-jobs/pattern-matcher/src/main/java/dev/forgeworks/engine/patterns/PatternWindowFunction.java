package dev.forgeworks.engine.patterns;

import dev.forgeworks.engine.patterns.model.FeatureExtractor;
import dev.forgeworks.engine.patterns.model.ModelLoader;
import dev.forgeworks.engine.patterns.model.ScoringModel;
import org.apache.flink.api.common.state.ListState;
import org.apache.flink.api.common.state.ListStateDescriptor;
import org.apache.flink.api.common.state.StateTtlConfig;
import org.apache.flink.api.common.time.Time;
import org.apache.flink.api.common.typeinfo.TypeInformation;
import org.apache.flink.configuration.Configuration;
import org.apache.flink.streaming.api.functions.KeyedProcessFunction;
import org.apache.flink.util.Collector;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * Stateful pattern evaluation using a sliding event window.
 *
 * Two-layer detection:
 * 1. Rule-based (PatternRules) — binary match, fast, deterministic
 * 2. Model-scored (ModelLoader) — probability score, enriches alerts
 *
 * How it works:
 * 1. Each incoming event is appended to a keyed ListState (per group key)
 * 2. The window is bounded by TTL (10 minutes) — old events auto-evict
 * 3. On each new event, rules are evaluated against the full window
 * 4. If a rule matches, the corresponding scoring model enriches the alert
 *    with a confidence score (0.0-1.0)
 * 5. Matched patterns produce PatternAlert objects with scores
 */
public class PatternWindowFunction
        extends KeyedProcessFunction<String, EventEnvelope, PatternAlert> {

    private static final Logger LOG = LoggerFactory.getLogger(PatternWindowFunction.class);
    private transient ListState<EventEnvelope> eventWindow;
    private transient ModelLoader modelLoader;

    // Maps pattern IDs to their scoring model + feature extractor
    private static final Map<String, String> PATTERN_TO_MODEL = new HashMap<>() {{
        put("PAT-DEPLOY-001", "rapid-deploy-scorer");
        put("PAT-K8S-001", "crash-loop-scorer");
        put("PAT-CI-001", "ci-skip-scorer");
    }};

    @Override
    public void open(Configuration parameters) {
        // State setup
        StateTtlConfig ttlConfig = StateTtlConfig.newBuilder(Time.minutes(10))
                .setUpdateType(StateTtlConfig.UpdateType.OnCreateAndWrite)
                .cleanupFullSnapshot()
                .build();

        ListStateDescriptor<EventEnvelope> descriptor = new ListStateDescriptor<>(
                "event-window", TypeInformation.of(EventEnvelope.class));
        descriptor.enableTimeToLive(ttlConfig);
        eventWindow = getRuntimeContext().getListState(descriptor);

        // Model Loader — Hot tier pre-loaded
        modelLoader = new ModelLoader();
        modelLoader.initialize();
        LOG.info("PatternWindowFunction initialized — models: {}", modelLoader.getHotModelIds());
    }

    @Override
    public void processElement(EventEnvelope event, Context ctx, Collector<PatternAlert> out)
            throws Exception {
        // Add event to window
        eventWindow.add(event);

        // Collect current window
        List<EventEnvelope> window = new ArrayList<>();
        for (EventEnvelope e : eventWindow.get()) {
            window.add(e);
        }

        // Rule-based detection
        List<PatternAlert> alerts = PatternRules.evaluate(ctx.getCurrentKey(), window);

        // Enrich each alert with model score
        for (PatternAlert alert : alerts) {
            enrichWithScore(alert, window);
            LOG.info("Pattern matched: {} — {} (group: {}, events: {}, score: {})",
                    alert.getPatternId(), alert.getPatternName(),
                    alert.getGroupKey(), alert.getEventCount(),
                    alert.getContext().get("model_score"));
            out.collect(alert);
        }
    }

    /**
     * Enrich a rule-based alert with a model confidence score.
     * If no model is available, adds score=null (rule-only detection).
     */
    private void enrichWithScore(PatternAlert alert, List<EventEnvelope> window) {
        String modelId = PATTERN_TO_MODEL.get(alert.getPatternId());
        if (modelId == null) return;

        ScoringModel model = modelLoader.loadModel(modelId);
        if (model == null) return;

        // Extract features based on pattern type
        Map<String, Double> features;
        switch (alert.getPatternId()) {
            case "PAT-DEPLOY-001":
                features = FeatureExtractor.extractDeployFeatures(window);
                break;
            case "PAT-K8S-001":
                features = FeatureExtractor.extractCrashFeatures(window);
                break;
            case "PAT-CI-001":
                features = FeatureExtractor.extractCIFeatures(window);
                break;
            default:
                return;
        }

        double score = model.score(features);

        // Add score metadata to alert context
        alert.getContext().put("model_score", score);
        alert.getContext().put("model_id", model.getModelId());
        alert.getContext().put("model_version", model.getVersion());
        alert.getContext().put("features", new HashMap<>(features));
    }
}
