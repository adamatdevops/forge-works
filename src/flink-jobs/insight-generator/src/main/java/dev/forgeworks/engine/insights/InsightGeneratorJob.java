package dev.forgeworks.engine.insights;

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
 * ForgeWorks Insight Generator — Flink streaming job #3.
 *
 * Pipeline:
 *   Kafka (forge.jobs.pending)
 *     → Deserialize PatternAlert
 *     → KeyBy (pattern_id:group_key)
 *     → InsightAggregator (dedup, recommend, consolidate)
 *     → Kafka (forge.learning.outcomes)
 *
 * Where it sits in the full pipeline:
 *   Webhook → Gateway → Kafka → Event Router → Pattern Matcher → forge.jobs.pending
 *                                                                       ↓
 *                                                              Insight Generator (this)
 *                                                                       ↓
 *                                                            forge.learning.outcomes
 *                                                   (deduplicated insights with recommendations)
 *
 * What it adds over raw alerts:
 * 1. Deduplication — 5 min cooldown per pattern+group
 * 2. Recommendations — actionable "what to do" per pattern
 * 3. Aggregation — counts suppressed alerts, tracks first/last seen
 * 4. Learning output — forge.learning.outcomes feeds Phase 3 ML training
 */
public class InsightGeneratorJob {

    private static final Logger LOG = LoggerFactory.getLogger(InsightGeneratorJob.class);

    public static void main(String[] args) throws Exception {
        String kafkaBootstrap = System.getenv("KAFKA_BOOTSTRAP_SERVERS");
        if (kafkaBootstrap == null || kafkaBootstrap.isEmpty()) {
            kafkaBootstrap = "forge-kafka-kafka-bootstrap.forge-engine.svc.cluster.local:9092";
        }

        LOG.info("Starting Insight Generator — bootstrap: {}", kafkaBootstrap);

        StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();

        // --- Source: consume pattern alerts ---
        KafkaSource<PatternAlert> source = KafkaSource.<PatternAlert>builder()
                .setBootstrapServers(kafkaBootstrap)
                .setTopics("forge.jobs.pending")
                .setGroupId("forgeworks-insight-generator")
                .setStartingOffsets(OffsetsInitializer.latest())
                .setValueOnlyDeserializer(new AlertDeserializer())
                .build();

        DataStream<PatternAlert> alerts = env
                .fromSource(source, WatermarkStrategy.noWatermarks(), "kafka-alerts")
                .name("Kafka Source (forge.jobs.pending)");

        // --- Filter nulls ---
        DataStream<PatternAlert> validAlerts = alerts
                .filter(a -> a != null)
                .name("Filter Invalid");

        // --- Deduplicate, aggregate, recommend ---
        DataStream<Insight> insights = validAlerts
                .keyBy(PatternAlert::dedupKey)
                .process(new InsightAggregator())
                .name("Insight Aggregator");

        // --- Sink: insights → forge.learning.outcomes ---
        KafkaSink<Insight> insightSink = KafkaSink.<Insight>builder()
                .setBootstrapServers(kafkaBootstrap)
                .setRecordSerializer(
                        KafkaRecordSerializationSchema.builder()
                                .setTopic("forge.learning.outcomes")
                                .setValueSerializationSchema(new InsightSerializer())
                                .build())
                .build();

        insights.sinkTo(insightSink).name("Sink → forge.learning.outcomes");

        env.execute("ForgeWorks Insight Generator");
    }
}
