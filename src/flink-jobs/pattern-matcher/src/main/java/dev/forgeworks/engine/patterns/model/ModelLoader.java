package dev.forgeworks.engine.patterns.model;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.Serializable;
import java.util.HashMap;
import java.util.Map;

/**
 * Tiered Model Loader — loads scoring models from Hot, Warm, or Cold tiers.
 *
 * Architecture:
 * ┌─────────────────────────────────────┐
 * │  HOT TIER (JVM HashMap)             │  ← <1ms lookup
 * │  Pre-loaded at startup              │
 * │  Top models always in memory        │
 * ├─────────────────────────────────────┤
 * │  WARM TIER (Redis)                  │  ← ~1ms network hop
 * │  Loaded on first access, cached     │
 * │  TTL-based eviction                 │
 * ├─────────────────────────────────────┤
 * │  COLD TIER (S3)                     │  ← 500ms-2s (Phase 3)
 * │  On-demand only                     │
 * │  Promotes to Warm after load        │
 * └─────────────────────────────────────┘
 *
 * Flow:
 *   loadModel("rapid-deploy-scorer")
 *     → check Hot (HashMap) → found? return immediately (<1ms)
 *     → check Warm (Redis)  → found? promote to Hot, return (<5ms)
 *     → check Cold (S3)     → found? promote to Warm+Hot, return (Phase 3)
 *     → not found           → return null (use rule-based fallback)
 *
 * Why tiered:
 * - Not all models need to be in memory all the time
 * - Hot tier keeps the 3-5 most used models at zero-latency
 * - Warm tier handles less frequent models without S3 round-trips
 * - Cold tier is insurance — every model is always available
 *
 * Current implementation (MVP):
 * - Hot tier: fully implemented with pre-loaded weighted models
 * - Warm tier: interface ready, Redis integration in Phase 3
 * - Cold tier: deferred to Phase 3 (S3 + MLflow model registry)
 */
public class ModelLoader implements Serializable {

    private static final Logger LOG = LoggerFactory.getLogger(ModelLoader.class);

    // Hot tier — always in JVM memory
    private final Map<String, ScoringModel> hotModels = new HashMap<>();

    // Metrics
    private long hotHits = 0;
    private long warmHits = 0;
    private long misses = 0;

    /**
     * Initialize the loader with pre-loaded Hot tier models.
     * Call this once during Flink job open().
     */
    public void initialize() {
        LOG.info("Initializing Model Loader — loading Hot tier models");

        // MVP models — weighted scoring (will be replaced by MLflow models in Phase 3)
        registerHot(new WeightedScoringModel(
                "rapid-deploy-scorer", "1.0.0",
                "Scores risk of rapid successive deployments",
                Map.of(
                        "deploy_count", 0.4,
                        "time_span_inverse", 0.3,
                        "unique_authors_inverse", 0.3
                ),
                5.0  // normalization: max expected raw score
        ));

        registerHot(new WeightedScoringModel(
                "crash-loop-scorer", "1.0.0",
                "Scores severity of pod crash loop patterns",
                Map.of(
                        "crash_count", 0.5,
                        "restart_frequency", 0.3,
                        "unique_pods_inverse", 0.2
                ),
                8.0
        ));

        registerHot(new WeightedScoringModel(
                "ci-skip-scorer", "1.0.0",
                "Scores risk of merging without CI/CD checks",
                Map.of(
                        "merge_count", 0.3,
                        "tests_missing", 0.5,
                        "author_frequency_inverse", 0.2
                ),
                3.0
        ));

        LOG.info("Hot tier loaded: {} models", hotModels.size());
    }

    /**
     * Register a model in the Hot tier.
     */
    public void registerHot(ScoringModel model) {
        hotModels.put(model.getModelId(), model);
        LOG.debug("Registered Hot model: {} v{}", model.getModelId(), model.getVersion());
    }

    /**
     * Load a model by ID. Checks Hot → Warm → Cold (tiered).
     *
     * @return The model, or null if not found in any tier
     */
    public ScoringModel loadModel(String modelId) {
        // Hot tier — O(1) HashMap lookup, <1ms
        ScoringModel model = hotModels.get(modelId);
        if (model != null) {
            hotHits++;
            return model;
        }

        // Warm tier — Redis lookup (Phase 3)
        // model = loadFromRedis(modelId);
        // if (model != null) {
        //     warmHits++;
        //     registerHot(model);  // promote to Hot
        //     return model;
        // }

        // Cold tier — S3 lookup (Phase 3)
        // model = loadFromS3(modelId);
        // if (model != null) {
        //     registerHot(model);  // promote to Hot
        //     return model;
        // }

        misses++;
        LOG.debug("Model not found: {}", modelId);
        return null;
    }

    /**
     * Get all Hot tier model IDs.
     */
    public java.util.Set<String> getHotModelIds() {
        return hotModels.keySet();
    }

    /**
     * Get loader statistics for monitoring.
     */
    public Map<String, Long> getStats() {
        Map<String, Long> stats = new HashMap<>();
        stats.put("hot_models", (long) hotModels.size());
        stats.put("hot_hits", hotHits);
        stats.put("warm_hits", warmHits);
        stats.put("misses", misses);
        return stats;
    }
}
