package dev.forgeworks.engine.patterns;

import org.apache.flink.api.common.eventtime.WatermarkStrategy;
import org.apache.flink.connector.kafka.sink.KafkaRecordSerializationSchema;
import org.apache.flink.connector.kafka.sink.KafkaSink;
import org.apache.flink.connector.kafka.source.KafkaSource;
import org.apache.flink.connector.kafka.source.enumerator.initializer.OffsetsInitializer;
import org.apache.flink.streaming.api.datastream.DataStream;
import org.apache.flink.streaming.api.environment.StreamExecutionEnvironment;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * ForgeWorks Pattern Matcher — Flink streaming job #2.
 *
 * Pipeline:
 *   Kafka (forge.insights.realtime)
 *     → Deserialize
 *     → KeyBy (group key: source + repo/namespace)
 *     → PatternWindowFunction (stateful, 10-min sliding window)
 *     → Kafka (forge.jobs.pending)
 *
 * Where it sits in the pipeline:
 *   Webhook → Gateway → Kafka → Event Router → forge.insights.realtime
 *                                                      ↓
 *                                               Pattern Matcher (this job)
 *                                                      ↓
 *                                               forge.jobs.pending
 *
 * MVP Rules:
 *   PAT-DEPLOY-001: Rapid successive deployments (>3 ArgoCD syncs in 10 min)
 *   PAT-K8S-001:    Pod crash loop (>3 restart events in 10 min)
 *   PAT-CI-001:     PR merged without tests (merge + no check_run in window)
 *
 * Performance target: Pattern detection within 100ms of event arrival.
 */
public class PatternMatcherJob {

    private static final Logger LOG = LoggerFactory.getLogger(PatternMatcherJob.class);

    public static void main(String[] args) throws Exception {
        String kafkaBootstrap = System.getenv("KAFKA_BOOTSTRAP_SERVERS");
        if (kafkaBootstrap == null || kafkaBootstrap.isEmpty()) {
            kafkaBootstrap = "forge-kafka-kafka-bootstrap.forge-engine.svc.cluster.local:9092";
        }

        LOG.info("Starting Pattern Matcher — bootstrap: {}", kafkaBootstrap);

        StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();

        // --- Source: consume from forge.insights.realtime (Event Router output) ---
        KafkaSource<EventEnvelope> source = KafkaSource.<EventEnvelope>builder()
                .setBootstrapServers(kafkaBootstrap)
                .setTopics("forge.insights.realtime")
                .setGroupId("forgeworks-pattern-matcher")
                .setStartingOffsets(OffsetsInitializer.committedOffsets(OffsetsInitializer.earliest()))
                .setValueOnlyDeserializer(new EventDeserializer())
                .build();

        DataStream<EventEnvelope> events = env
                .fromSource(source, WatermarkStrategy.noWatermarks(), "kafka-insights")
                .name("Kafka Source (forge.insights.realtime)");

        // --- Filter nulls ---
        DataStream<EventEnvelope> validEvents = events
                .filter(e -> e != null)
                .name("Filter Invalid");

        // --- Key by group (source:repo or source:namespace/name) ---
        // --- Evaluate patterns against windowed state ---
        DataStream<PatternAlert> alerts = validEvents
                .keyBy(EventEnvelope::groupKey)
                .process(new PatternWindowFunction())
                .name("Pattern Matcher");

        // --- Sink: alerts → forge.jobs.pending ---
        KafkaSink<PatternAlert> alertSink = KafkaSink.<PatternAlert>builder()
                .setBootstrapServers(kafkaBootstrap)
                .setRecordSerializer(
                        KafkaRecordSerializationSchema.builder()
                                .setTopic("forge.jobs.pending")
                                .setValueSerializationSchema(new AlertSerializer())
                                .build())
                .build();

        alerts.sinkTo(alertSink).name("Sink → forge.jobs.pending");

        env.execute("ForgeWorks Pattern Matcher");
    }
}
