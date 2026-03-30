package dev.forgeworks.engine.patterns.model;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.Serializable;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;
import java.util.HashMap;
import java.util.Map;

/**
 * Loads trained models from MLflow registry and adapts them to the ScoringModel interface.
 *
 * All HTTP calls have a 5-second timeout to prevent blocking Flink processing.
 * Called from a background thread, never from the scoring hot path.
 */
public class MLflowModelAdapter implements Serializable {

    private static final Logger LOG = LoggerFactory.getLogger(MLflowModelAdapter.class);
    private static final Duration HTTP_TIMEOUT = Duration.ofSeconds(5);

    private final String mlflowBaseUrl;
    private final Map<String, String> loadedVersions = new HashMap<>();

    public MLflowModelAdapter(String mlflowBaseUrl) {
        this.mlflowBaseUrl = mlflowBaseUrl;
    }

    /**
     * Check MLflow for a newer version of a registered model.
     * Returns a new ScoringModel if updated, null if no change.
     */
    public ScoringModel checkForUpdate(String modelName) {
        try {
            String latestVersion = getLatestVersion(modelName);
            if (latestVersion == null) return null;

            String currentVersion = loadedVersions.get(modelName);
            if (latestVersion.equals(currentVersion)) return null;

            LOG.info("New model version detected: {} v{} (was: {})",
                    modelName, latestVersion, currentVersion);

            Map<String, Double> weights = fetchFeatureImportance(modelName, latestVersion);
            if (weights == null || weights.isEmpty()) {
                LOG.warn("No feature importance found for {} v{}, skipping", modelName, latestVersion);
                return null;
            }

            loadedVersions.put(modelName, latestVersion);

            double normalization = weights.values().stream().mapToDouble(Double::doubleValue).sum() * 3;
            return new WeightedScoringModel(
                    modelName, latestVersion,
                    "MLflow-trained (feature importance weights)",
                    weights, Math.max(normalization, 1.0)
            );
        } catch (Exception e) {
            LOG.warn("Failed to check MLflow for model {}: {}", modelName, e.getMessage());
            return null;
        }
    }

    private String getLatestVersion(String modelName) throws Exception {
        HttpClient client = HttpClient.newBuilder().connectTimeout(HTTP_TIMEOUT).build();
        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(mlflowBaseUrl + "/api/2.0/mlflow/registered-models/get-latest-versions"))
                .header("Content-Type", "application/json")
                .timeout(HTTP_TIMEOUT)
                .POST(HttpRequest.BodyPublishers.ofString("{\"name\":\"" + modelName + "\"}"))
                .build();

        HttpResponse<String> response = client.send(request, HttpResponse.BodyHandlers.ofString());
        if (response.statusCode() != 200) return null;

        ObjectMapper mapper = new ObjectMapper();
        JsonNode versions = mapper.readTree(response.body()).get("model_versions");
        if (versions == null || !versions.isArray() || versions.isEmpty()) return null;
        return versions.get(0).get("version").asText();
    }

    /**
     * Fetch feature importance metrics logged during training.
     * Training logs these as importance_{feature_name} via mlflow.log_metric().
     */
    private Map<String, Double> fetchFeatureImportance(String modelName, String version) throws Exception {
        HttpClient client = HttpClient.newBuilder().connectTimeout(HTTP_TIMEOUT).build();

        // Get run_id for this model version
        HttpRequest versionReq = HttpRequest.newBuilder()
                .uri(URI.create(mlflowBaseUrl + "/api/2.0/mlflow/model-versions/get?name=" +
                        modelName + "&version=" + version))
                .timeout(HTTP_TIMEOUT)
                .GET()
                .build();

        HttpResponse<String> versionResp = client.send(versionReq, HttpResponse.BodyHandlers.ofString());
        if (versionResp.statusCode() != 200) return null;

        ObjectMapper mapper = new ObjectMapper();
        JsonNode versionNode = mapper.readTree(versionResp.body()).get("model_version");
        if (versionNode == null) return null;
        String runId = versionNode.get("run_id").asText();

        // Fetch run metrics
        HttpRequest metricsReq = HttpRequest.newBuilder()
                .uri(URI.create(mlflowBaseUrl + "/api/2.0/mlflow/runs/get?run_id=" + runId))
                .timeout(HTTP_TIMEOUT)
                .GET()
                .build();

        HttpResponse<String> metricsResp = client.send(metricsReq, HttpResponse.BodyHandlers.ofString());
        if (metricsResp.statusCode() != 200) return null;

        JsonNode runNode = mapper.readTree(metricsResp.body()).get("run");
        if (runNode == null) return null;
        JsonNode metrics = runNode.get("data").get("metrics");
        if (metrics == null) return null;

        Map<String, Double> weights = new HashMap<>();
        for (JsonNode metric : metrics) {
            String key = metric.get("key").asText();
            if (key.startsWith("importance_")) {
                String featureName = key.substring("importance_".length());
                weights.put(featureName, metric.get("value").asDouble());
            }
        }

        LOG.info("Loaded {} feature weights from MLflow run {}", weights.size(), runId);
        return weights;
    }
}
