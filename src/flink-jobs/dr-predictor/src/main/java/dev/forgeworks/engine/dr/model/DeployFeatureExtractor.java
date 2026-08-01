package dev.forgeworks.engine.dr.model;

import dev.forgeworks.engine.dr.NormalizedEvent;
import java.io.Serializable;
import java.util.HashMap;
import java.util.Map;

/**
 * Extracts scoring features from a deploy event.
 *
 * <p>Placeholder implementation — the four feature families defined in AB-028 RFC §4.3 (deploy
 * metadata / recent-history rolling counts / slice-state / deploy-content) require stateful rolling
 * windows across the event stream, which is future work when the AB-028 spike lands. This extractor
 * captures the fields available from a single event so the pipeline runs end-to-end.
 */
public class DeployFeatureExtractor implements Serializable {

    private static final long serialVersionUID = 1L;

    /** Extract scoring features from a single deploy event. */
    public Map<String, Double> extract(NormalizedEvent event) {
        Map<String, Double> features = new HashMap<>();
        Map<String, Object> payload = event.getPayload();
        if (payload == null) return features;

        putIfNumeric(features, "plan_diff_size", payload.get("plan_diff_size"));
        putIfNumeric(features, "resources_touched", payload.get("resources_touched"));
        Object sensitive = payload.get("touched_sensitive_resource");
        if (sensitive instanceof Boolean) {
            features.put("touched_sensitive_resource", ((Boolean) sensitive) ? 1.0 : 0.0);
        }
        return features;
    }

    private static void putIfNumeric(Map<String, Double> features, String key, Object value) {
        if (value instanceof Number) {
            features.put(key, ((Number) value).doubleValue());
        }
    }
}
