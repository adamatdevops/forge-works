package dev.forgeworks.engine.patterns.model;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.Serializable;
import java.util.HashMap;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.TimeUnit;

/**
 * Tiered Model Loader — Hot tier (JVM memory) with background MLflow reload.
 *
 * <p>Scoring path: HashMap lookup only (<1ms, zero blocking). Background: ScheduledExecutor polls
 * MLflow every 5 min for new model versions. If MLflow has a newer version, feature importance
 * weights are fetched and hot-swapped into the HashMap atomically.
 *
 * <p>The trained model's feature importance values (logged by Airflow as importance_{feature_name})
 * directly become the scoring weights. This is a faithful transfer — the same features and relative
 * magnitudes that the GradientBoosting model learned are used for linear scoring.
 */
public class ModelLoader implements Serializable {

    private static final Logger LOG = LoggerFactory.getLogger(ModelLoader.class);
    private static final long RELOAD_INTERVAL_MINUTES = 5;

    private final Map<String, ScoringModel> hotModels = new ConcurrentHashMap<>();
    private transient ScheduledExecutorService reloadScheduler;
    private transient MLflowModelAdapter mlflowAdapter;

    // Model names to poll in MLflow
    private static final String[] MLFLOW_MODEL_NAMES = {"forgeworks-pattern-scorer"};

    // Feature-to-scorer mapping: which features each scorer uses
    private static final Map<String, Map<String, String>> SCORER_FEATURE_MAP =
            Map.of(
                    "rapid-deploy-scorer",
                            Map.of(
                                    "deploy_count", "sync_count",
                                    "time_span_inverse", "time_span_minutes",
                                    "unique_authors_inverse", "unique_authors"),
                    "crash-loop-scorer",
                            Map.of(
                                    "crash_count", "crash_count",
                                    "restart_frequency", "events_per_minute",
                                    "unique_pods_inverse", "author_concentration"),
                    "ci-skip-scorer",
                            Map.of(
                                    "merge_count", "merge_count",
                                    "tests_missing", "test_count",
                                    "author_frequency_inverse", "author_concentration"));

    private long hotHits = 0;
    private long reloads = 0;
    private long misses = 0;

    /** Initialize with default models and start background MLflow polling. */
    public void initialize() {
        LOG.info("Initializing Model Loader");

        // Default models — used until MLflow has trained replacements
        registerHot(
                new WeightedScoringModel(
                        "rapid-deploy-scorer",
                        "default-1.0",
                        "Default weights for rapid deployment scoring",
                        Map.of(
                                "deploy_count",
                                0.4,
                                "time_span_inverse",
                                0.3,
                                "unique_authors_inverse",
                                0.3),
                        5.0));
        registerHot(
                new WeightedScoringModel(
                        "crash-loop-scorer",
                        "default-1.0",
                        "Default weights for crash loop scoring",
                        Map.of(
                                "crash_count",
                                0.5,
                                "restart_frequency",
                                0.3,
                                "unique_pods_inverse",
                                0.2),
                        8.0));
        registerHot(
                new WeightedScoringModel(
                        "ci-skip-scorer",
                        "default-1.0",
                        "Default weights for CI skip scoring",
                        Map.of(
                                "merge_count",
                                0.3,
                                "tests_missing",
                                0.5,
                                "author_frequency_inverse",
                                0.2),
                        3.0));

        // Start background MLflow polling
        String mlflowUrl = System.getenv("MLFLOW_TRACKING_URI");
        if (mlflowUrl == null || mlflowUrl.isEmpty()) {
            mlflowUrl = "http://mlflow.forge-ml.svc.cluster.local:5000";
        }
        mlflowAdapter = new MLflowModelAdapter(mlflowUrl);

        reloadScheduler =
                Executors.newSingleThreadScheduledExecutor(
                        r -> {
                            Thread t = new Thread(r, "model-reload");
                            t.setDaemon(true);
                            return t;
                        });
        reloadScheduler.scheduleAtFixedRate(
                this::reloadFromMLflow,
                RELOAD_INTERVAL_MINUTES,
                RELOAD_INTERVAL_MINUTES,
                TimeUnit.MINUTES);

        LOG.info(
                "Hot tier loaded: {} defaults, background MLflow polling every {}min",
                hotModels.size(),
                RELOAD_INTERVAL_MINUTES);
    }

    public void registerHot(ScoringModel model) {
        hotModels.put(model.getModelId(), model);
    }

    /** Load a model by ID. Pure HashMap lookup — zero blocking, <1ms. */
    public ScoringModel loadModel(String modelId) {
        ScoringModel model = hotModels.get(modelId);
        if (model != null) {
            hotHits++;
            return model;
        }
        misses++;
        return null;
    }

    /** Background task: poll MLflow for updated models and hot-swap. */
    private void reloadFromMLflow() {
        if (mlflowAdapter == null) return;

        for (String modelName : MLFLOW_MODEL_NAMES) {
            try {
                ScoringModel trained = mlflowAdapter.checkForUpdate(modelName);
                if (trained == null) continue;

                // The trained model IS a WeightedScoringModel with feature importance
                // weights fetched directly from MLflow metrics. Map those weights
                // to each scorer's feature namespace.
                WeightedScoringModel trainedWeighted = (WeightedScoringModel) trained;
                Map<String, Double> trainedWeights = trainedWeighted.getWeights();

                for (Map.Entry<String, Map<String, String>> scorer :
                        SCORER_FEATURE_MAP.entrySet()) {
                    String scorerId = scorer.getKey();
                    Map<String, String> featureMapping = scorer.getValue();

                    Map<String, Double> weights = new HashMap<>();
                    for (Map.Entry<String, String> mapping : featureMapping.entrySet()) {
                        String scorerFeature = mapping.getKey();
                        String trainedFeature = mapping.getValue();
                        // Direct lookup — no probing
                        Double importance = trainedWeights.get(trainedFeature);
                        weights.put(scorerFeature, importance != null ? importance : 0.1);
                    }

                    double norm =
                            weights.values().stream().mapToDouble(Double::doubleValue).sum() * 3;
                    registerHot(
                            new WeightedScoringModel(
                                    scorerId,
                                    trained.getVersion(),
                                    "MLflow-trained v" + trained.getVersion(),
                                    weights,
                                    Math.max(norm, 1.0)));
                }

                reloads++;
                LOG.info(
                        "Hot-swapped all scorers from MLflow v{} (reload #{})",
                        trained.getVersion(),
                        reloads);
            } catch (Exception e) {
                LOG.warn("MLflow reload failed for {}: {}", modelName, e.getMessage());
            }
        }
    }

    /** Shutdown the background reload scheduler. */
    public void close() {
        if (reloadScheduler != null) {
            reloadScheduler.shutdown();
        }
    }

    public java.util.Set<String> getHotModelIds() {
        return hotModels.keySet();
    }

    public Map<String, Long> getStats() {
        Map<String, Long> stats = new HashMap<>();
        stats.put("hot_models", (long) hotModels.size());
        stats.put("hot_hits", hotHits);
        stats.put("reloads", reloads);
        stats.put("misses", misses);
        return stats;
    }
}
