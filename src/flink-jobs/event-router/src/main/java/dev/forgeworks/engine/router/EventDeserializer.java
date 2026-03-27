package dev.forgeworks.engine.router;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.apache.flink.api.common.serialization.DeserializationSchema;
import org.apache.flink.api.common.typeinfo.TypeInformation;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.IOException;

/**
 * Deserializes Kafka message bytes into EventEnvelope objects.
 * Invalid JSON is logged and returns null (filtered downstream).
 */
public class EventDeserializer implements DeserializationSchema<EventEnvelope> {

    private static final Logger LOG = LoggerFactory.getLogger(EventDeserializer.class);
    private transient ObjectMapper mapper;

    @Override
    public void open(InitializationContext context) {
        mapper = new ObjectMapper();
    }

    @Override
    public EventEnvelope deserialize(byte[] message) throws IOException {
        if (mapper == null) {
            mapper = new ObjectMapper();
        }
        try {
            return mapper.readValue(message, EventEnvelope.class);
        } catch (Exception e) {
            LOG.warn("Failed to deserialize event: {}", new String(message), e);
            return null;
        }
    }

    @Override
    public boolean isEndOfStream(EventEnvelope nextElement) {
        return false;
    }

    @Override
    public TypeInformation<EventEnvelope> getProducedType() {
        return TypeInformation.of(EventEnvelope.class);
    }
}
