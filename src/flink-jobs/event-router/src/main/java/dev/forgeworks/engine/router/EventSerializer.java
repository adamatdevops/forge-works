package dev.forgeworks.engine.router;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.apache.flink.api.common.serialization.SerializationSchema;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/** Serializes EventEnvelope objects to JSON bytes for Kafka output. */
public class EventSerializer implements SerializationSchema<EventEnvelope> {

    private static final long serialVersionUID = 1L;
    private static final Logger LOG = LoggerFactory.getLogger(EventSerializer.class);
    private transient ObjectMapper mapper;

    @Override
    public void open(InitializationContext context) {
        mapper = new ObjectMapper();
    }

    @Override
    public byte[] serialize(EventEnvelope event) {
        if (mapper == null) {
            mapper = new ObjectMapper();
        }
        try {
            return mapper.writeValueAsBytes(event);
        } catch (Exception e) {
            LOG.error("Failed to serialize event: {}", event.getEventId(), e);
            throw new RuntimeException("Serialization failed for event " + event.getEventId(), e);
        }
    }
}
