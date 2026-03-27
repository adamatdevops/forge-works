package dev.forgeworks.engine.patterns;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.apache.flink.api.common.serialization.DeserializationSchema;
import org.apache.flink.api.common.typeinfo.TypeInformation;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.IOException;

public class EventDeserializer implements DeserializationSchema<EventEnvelope> {

    private static final Logger LOG = LoggerFactory.getLogger(EventDeserializer.class);
    private transient ObjectMapper mapper;

    @Override
    public void open(InitializationContext context) {
        mapper = new ObjectMapper();
    }

    @Override
    public EventEnvelope deserialize(byte[] message) throws IOException {
        if (mapper == null) mapper = new ObjectMapper();
        try {
            return mapper.readValue(message, EventEnvelope.class);
        } catch (Exception e) {
            LOG.warn("Failed to deserialize event: {}", new String(message), e);
            return null;
        }
    }

    @Override
    public boolean isEndOfStream(EventEnvelope nextElement) { return false; }

    @Override
    public TypeInformation<EventEnvelope> getProducedType() {
        return TypeInformation.of(EventEnvelope.class);
    }
}
