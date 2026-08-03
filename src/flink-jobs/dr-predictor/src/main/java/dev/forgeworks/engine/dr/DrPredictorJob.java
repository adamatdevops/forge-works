package dev.forgeworks.engine.dr;

import dev.forgeworks.engine.dr.model.ConstantPredictor;
import dev.forgeworks.engine.dr.model.DeployFeatureExtractor;
import dev.forgeworks.engine.dr.model.ScoringModel;
import java.time.Instant;
import java.util.HashMap;
import java.util.Map;
import java.util.UUID;
import org.apache.flink.api.common.eventtime.WatermarkStrategy;
import org.apache.flink.api.common.functions.MapFunction;
import org.apache.flink.connector.kafka.sink.KafkaRecordSerializationSchema;
import org.apache.flink.connector.kafka.sink.KafkaSink;
import org.apache.flink.connector.kafka.source.KafkaSource;
import org.apache.flink.connector.kafka.source.enumerator.initializer.OffsetsInitializer;
import org.apache.flink.streaming.api.datastream.DataStream;
import org.apache.flink.streaming.api.environment.StreamExecutionEnvironment;
import org.apache.kafka.clients.consumer.OffsetResetStrategy;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * AB-029 Option A — sibling Flink job for the Dynamic Reliability predictor.
 *
 * <p>Pipeline: Kafka (forge.events.normalized.v1) → deserialize → filter (deploy events only) →
 * keyBy (service:environment slice) → score → Kafka (forge.predictions.dynamic_reliability.v1)
 *
 * <p>Model: {@link ConstantPredictor} placeholder until AB-028 spike ships a real MLflow-loaded
 * model. The pipeline shape is production-ready; only the scoring implementation is a placeholder.
 *
 * <p>Estimand: deploy_slo_breach_60m_association_v0 (see PREDICTION_CONTRACT.md §3.0).
 */
public class DrPredictorJob {

    private static final Logger LOG = LoggerFactory.getLogger(DrPredictorJob.class);

    private static final String INPUT_TOPIC = "forge.events.normalized.v1";
    private static final String OUTPUT_TOPIC = "forge.predictions.dynamic_reliability.v1";
    private static final String CONSUMER_GROUP = "forgeworks-dr-predictor";

    public static void main(String[] args) throws Exception {
        String kafkaBootstrap = System.getenv("KAFKA_BOOTSTRAP_SERVERS");
        if (kafkaBootstrap == null || kafkaBootstrap.isEmpty()) {
            kafkaBootstrap = "forge-kafka-kafka-bootstrap.forge-engine.svc.cluster.local:9092";
        }

        LOG.info("Starting DR Predictor — bootstrap: {}", kafkaBootstrap);

        StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();

        KafkaSource<NormalizedEvent> source =
                KafkaSource.<NormalizedEvent>builder()
                        .setBootstrapServers(kafkaBootstrap)
                        .setTopics(INPUT_TOPIC)
                        .setGroupId(CONSUMER_GROUP)
                        .setStartingOffsets(
                                OffsetsInitializer.committedOffsets(OffsetResetStrategy.EARLIEST))
                        .setValueOnlyDeserializer(new EventDeserializer())
                        .build();

        DataStream<NormalizedEvent> events =
                env.fromSource(source, WatermarkStrategy.noWatermarks(), "kafka-normalized")
                        .name("Kafka Source (" + INPUT_TOPIC + ")");

        DataStream<NormalizedEvent> deploys =
                events.filter(e -> e != null && e.isDeploy()).name("Filter Deploys");

        ScoringModel model = new ConstantPredictor();
        DeployFeatureExtractor extractor = new DeployFeatureExtractor();

        DataStream<PredictionEnvelope> predictions =
                deploys.keyBy(NormalizedEvent::sliceKey)
                        .map(new ScoreDeploy(model, extractor))
                        .name("Score Deploy → Prediction");

        KafkaSink<PredictionEnvelope> sink =
                KafkaSink.<PredictionEnvelope>builder()
                        .setBootstrapServers(kafkaBootstrap)
                        .setRecordSerializer(
                                KafkaRecordSerializationSchema.builder()
                                        .setTopic(OUTPUT_TOPIC)
                                        .setValueSerializationSchema(new PredictionSerializer())
                                        .build())
                        .build();

        predictions.sinkTo(sink).name("Sink → " + OUTPUT_TOPIC);

        env.execute("ForgeWorks DR Predictor");
    }

    /** MapFunction that extracts features, scores, and builds a prediction envelope. */
    static final class ScoreDeploy implements MapFunction<NormalizedEvent, PredictionEnvelope> {

        private static final long serialVersionUID = 1L;

        private final ScoringModel model;
        private final DeployFeatureExtractor extractor;

        ScoreDeploy(ScoringModel model, DeployFeatureExtractor extractor) {
            this.model = model;
            this.extractor = extractor;
        }

        @Override
        public PredictionEnvelope map(NormalizedEvent event) {
            // v0.2 (Codex round-1 loop): freshness handling tightened per RFC §6.3 G9.
            //  - Boundary `>= 300` (was `> 300`); PC §3.0 eligibility gate is `< 5 minutes`, so at
            //    exactly 5 minutes the input is NOT fresh enough.
            //  - Null / malformed freshness → abstain with `input_freshness_underspecified`
            //    (was silently coerced to 0L → score). RFC §6.3 G9 requires abstention on
            //    underspecified freshness, not a synthetic zero-age.
            //  - v0.1 field name `input_freshness_seconds` renamed to `input_freshness_age_seconds`
            //    to avoid semantic collision with PC §3.3 `input_freshness` (a timestamp).
            //  - `UUID.randomUUID()` + `Instant.now()` retained pending H10 real-impl PR
            //    (deterministic prediction_id derivation blocked on RFC §5.1 model bundle lock).
            Instant now = Instant.now();
            Map<String, String> slice = buildSlice(event);
            Long freshnessSeconds = computeFreshness(event, now);
            if (freshnessSeconds == null) {
                return PredictionEnvelope.abstain(
                        UUID.randomUUID().toString(),
                        event.getEventId(),
                        "input_freshness_underspecified",
                        slice,
                        model.getModelId(),
                        model.getModelVersion(),
                        now);
            }
            if (freshnessSeconds >= 300) {
                return PredictionEnvelope.abstain(
                        UUID.randomUUID().toString(),
                        event.getEventId(),
                        "input_stale",
                        slice,
                        model.getModelId(),
                        model.getModelVersion(),
                        now);
            }
            double score = model.score(extractor.extract(event));
            return PredictionEnvelope.score(
                    UUID.randomUUID().toString(),
                    event.getEventId(),
                    score,
                    slice,
                    model.getModelId(),
                    model.getModelVersion(),
                    freshnessSeconds,
                    now);
        }

        private static Map<String, String> buildSlice(NormalizedEvent event) {
            Map<String, String> slice = new HashMap<>();
            slice.put("service", "unknown");
            slice.put("environment", "unknown");
            Map<String, Object> meta = event.getMetadata();
            if (meta != null) {
                Object s = meta.get("service");
                Object e = meta.get("environment");
                if (s != null) slice.put("service", s.toString());
                if (e != null) slice.put("environment", e.toString());
            }
            return slice;
        }

        private static Long computeFreshness(NormalizedEvent event, Instant now) {
            String ts = event.getTimestamp();
            if (ts == null) return null;
            try {
                return Math.max(0L, now.getEpochSecond() - Instant.parse(ts).getEpochSecond());
            } catch (Exception e) {
                return null;
            }
        }
    }
}
