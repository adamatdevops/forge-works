package dev.forgeworks.engine.router;

import org.apache.flink.api.common.eventtime.WatermarkStrategy;
import org.apache.flink.connector.kafka.sink.KafkaRecordSerializationSchema;
import org.apache.flink.connector.kafka.sink.KafkaSink;
import org.apache.flink.connector.kafka.source.KafkaSource;
import org.apache.flink.connector.kafka.source.enumerator.initializer.OffsetsInitializer;
import org.apache.kafka.clients.consumer.OffsetResetStrategy;
import org.apache.flink.streaming.api.datastream.DataStream;
import org.apache.flink.streaming.api.datastream.SingleOutputStreamOperator;
import org.apache.flink.streaming.api.environment.StreamExecutionEnvironment;
import org.apache.flink.streaming.api.functions.ProcessFunction;
import org.apache.flink.util.Collector;
import org.apache.flink.util.OutputTag;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.regex.Pattern;

/**
 * ForgeWorks Event Router — the first Flink streaming job.
 *
 * Pipeline:
 *   Kafka (forge.events.*) → Deserialize → Deduplicate → Route → Kafka (output topics)
 *
 * Routing rules:
 *   - GitHub PR/push events      → forge.insights.realtime (pattern analysis)
 *   - ArgoCD sync events         → forge.insights.realtime (deployment tracking)
 *   - Kubernetes pod/node events → forge.insights.realtime (cluster health)
 *   - Unrecognized events        → forge.dlq.events (dead letter)
 *
 * Performance characteristics:
 *   - Deduplication via keyed state (1h TTL, ~100MB state)
 *   - Zero external calls in hot path (all in-JVM)
 *   - Target: <100ms per event end-to-end
 */
public class EventRouterJob {

    private static final Logger LOG = LoggerFactory.getLogger(EventRouterJob.class);

    // Side output for unroutable events → DLQ
    private static final OutputTag<EventEnvelope> DLQ_TAG =
            new OutputTag<EventEnvelope>("dlq") {};

    public static void main(String[] args) throws Exception {
        // Config from environment (set via FlinkDeployment or flink-conf.yaml)
        String kafkaBootstrap = System.getenv("KAFKA_BOOTSTRAP_SERVERS");
        if (kafkaBootstrap == null || kafkaBootstrap.isEmpty()) {
            kafkaBootstrap = "forge-kafka-kafka-bootstrap.forge-engine.svc.cluster.local:9092";
        }

        LOG.info("Starting Event Router — bootstrap: {}", kafkaBootstrap);

        StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();

        // --- Source: consume from all forge.events.* topics ---
        KafkaSource<EventEnvelope> source = KafkaSource.<EventEnvelope>builder()
                .setBootstrapServers(kafkaBootstrap)
                .setTopicPattern(Pattern.compile("forge\\.events\\..*"))
                .setGroupId("forgeworks-event-router")
                .setStartingOffsets(OffsetsInitializer.committedOffsets(OffsetResetStrategy.EARLIEST))
                .setValueOnlyDeserializer(new EventDeserializer())
                .build();

        DataStream<EventEnvelope> events = env
                .fromSource(source, WatermarkStrategy.noWatermarks(), "kafka-events")
                .name("Kafka Source (forge.events.*)");

        // --- Filter nulls (deserialization failures) ---
        DataStream<EventEnvelope> validEvents = events
                .filter(e -> e != null)
                .name("Filter Invalid");

        // --- Deduplicate by event_id ---
        DataStream<EventEnvelope> deduplicated = validEvents
                .keyBy(EventEnvelope::routingKey)
                .filter(new DeduplicationFilter())
                .name("Deduplicate");

        // --- Route events ---
        SingleOutputStreamOperator<EventEnvelope> routed = deduplicated
                .process(new RoutingFunction())
                .name("Route Events");

        // Main output → forge.insights.realtime
        DataStream<EventEnvelope> insights = routed;

        // Side output → forge.dlq.events
        DataStream<EventEnvelope> dlq = routed.getSideOutput(DLQ_TAG);

        // --- Sink: insights → Kafka ---
        KafkaSink<EventEnvelope> insightSink = KafkaSink.<EventEnvelope>builder()
                .setBootstrapServers(kafkaBootstrap)
                .setRecordSerializer(
                        KafkaRecordSerializationSchema.builder()
                                .setTopic("forge.insights.realtime")
                                .setValueSerializationSchema(new EventSerializer())
                                .build())
                .build();

        insights.sinkTo(insightSink).name("Sink → forge.insights.realtime");

        // --- Sink: DLQ → Kafka ---
        KafkaSink<EventEnvelope> dlqSink = KafkaSink.<EventEnvelope>builder()
                .setBootstrapServers(kafkaBootstrap)
                .setRecordSerializer(
                        KafkaRecordSerializationSchema.builder()
                                .setTopic("forge.dlq.events")
                                .setValueSerializationSchema(new EventSerializer())
                                .build())
                .build();

        dlq.sinkTo(dlqSink).name("Sink → forge.dlq.events");

        env.execute("ForgeWorks Event Router");
    }

    /**
     * Routes events based on source and type.
     * Known patterns go to main output (insights).
     * Unknown patterns go to side output (DLQ).
     */
    static class RoutingFunction extends ProcessFunction<EventEnvelope, EventEnvelope> {

        @Override
        public void processElement(EventEnvelope event, Context ctx, Collector<EventEnvelope> out) {
            String source = event.getSource();
            if (source == null) {
                LOG.warn("Event with null source: {}", event.getEventId());
                ctx.output(DLQ_TAG, event);
                return;
            }

            switch (source) {
                case "github":
                case "argocd":
                case "kubernetes":
                    LOG.debug("Routing {} event {} to insights", source, event.getEventId());
                    out.collect(event);
                    break;
                default:
                    LOG.warn("Unknown source '{}' for event {}, sending to DLQ",
                            source, event.getEventId());
                    ctx.output(DLQ_TAG, event);
                    break;
            }
        }
    }
}
