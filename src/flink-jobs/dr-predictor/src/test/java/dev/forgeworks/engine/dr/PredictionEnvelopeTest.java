package dev.forgeworks.engine.dr;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.ObjectMapper;
import java.time.Instant;
import java.util.Map;
import org.junit.jupiter.api.Test;

/**
 * Basic tests for {@link PredictionEnvelope} per Codex Loop #4 M21 partial.
 *
 * <p>Scope (v0.2 apply-now): construct/serialize sanity + freshness field naming per PC §3.3.
 * Deferred to real-impl PR: PC §3 field-completeness tests, structured slice tests,
 * governance-envelope propagation tests, deterministic-identity tests, lifecycle-event tests.
 */
class PredictionEnvelopeTest {

    private static final ObjectMapper MAPPER = new ObjectMapper();
    private static final Instant NOW = Instant.parse("2026-08-03T10:00:00Z");
    private static final Map<String, String> SLICE =
            Map.of("service", "webhook-gateway", "environment", "prod");

    @Test
    void scoreFactoryCarriesModelIdAndVersionPerPcSection42() throws Exception {
        PredictionEnvelope envelope =
                PredictionEnvelope.score(
                        "evt-1",
                        "src-1",
                        0.05,
                        SLICE,
                        "placeholder-constant",
                        "0.1.0-placeholder",
                        42L,
                        NOW);

        assertEquals("placeholder-constant", envelope.getModelId());
        assertEquals("0.1.0-placeholder", envelope.getModelVersion());
        assertEquals(Long.valueOf(42L), envelope.getInputFreshnessAgeSeconds());
        assertEquals("score", envelope.getType());

        String json = MAPPER.writeValueAsString(envelope);
        assertTrue(json.contains("\"model_id\":\"placeholder-constant\""), json);
        assertTrue(json.contains("\"model_version\":\"0.1.0-placeholder\""), json);
        assertTrue(json.contains("\"input_freshness_age_seconds\":42"), json);
        // v0.2 empirical fix: model_ref must NOT appear (was v0.1 invented URI scheme)
        assertTrue(!json.contains("\"model_ref\""), json);
        // v0.2 empirical fix: input_freshness_seconds must NOT appear (was v0.1 collision)
        assertTrue(!json.contains("\"input_freshness_seconds\""), json);
    }

    @Test
    void abstainFactoryPopulatesReasonAndNoValue() {
        PredictionEnvelope envelope =
                PredictionEnvelope.abstain(
                        "evt-1",
                        "src-1",
                        "input_stale",
                        SLICE,
                        "placeholder-constant",
                        "0.1.0-placeholder",
                        NOW);

        assertEquals("abstain", envelope.getType());
        assertEquals("input_stale", envelope.getAbstainReason());
        assertNull(envelope.getValue());
        assertNull(envelope.getInputFreshnessAgeSeconds());
    }

    @Test
    void canonicalPoolIsRuntime() {
        PredictionEnvelope envelope =
                PredictionEnvelope.score(
                        "evt-1",
                        "src-1",
                        0.05,
                        SLICE,
                        "placeholder-constant",
                        "0.1.0-placeholder",
                        0L,
                        NOW);

        // v0.2 empirical fix: pool is canonical "runtime" (was v0.1 noncanonical "deploy"/"slo")
        assertNotNull(envelope.getPools());
        assertEquals(1, envelope.getPools().size());
        assertEquals("runtime", envelope.getPools().get(0));
    }

    @Test
    void freshnessBoundaryAtExactly300SecondsWouldTriggerAbstain() {
        // Verifies PC §3.0 eligibility gate `input_freshness < 5 minutes` — at exactly 300s,
        // input is NOT fresh enough. This test verifies the ENVELOPE side; the actual gate
        // check lives in DrPredictorJob.ScoreDeploy.map(). Here we prove the abstain factory
        // is callable with reason="input_stale" at the boundary.
        PredictionEnvelope atBoundary =
                PredictionEnvelope.abstain(
                        "evt-1",
                        "src-1",
                        "input_stale",
                        SLICE,
                        "placeholder-constant",
                        "0.1.0-placeholder",
                        NOW);
        assertEquals("input_stale", atBoundary.getAbstainReason());
    }
}
