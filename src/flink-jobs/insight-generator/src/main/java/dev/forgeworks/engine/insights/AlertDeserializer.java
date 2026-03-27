package dev.forgeworks.engine.insights;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.apache.flink.api.common.serialization.DeserializationSchema;
import org.apache.flink.api.common.typeinfo.TypeInformation;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.IOException;

public class AlertDeserializer implements DeserializationSchema<PatternAlert> {

    private static final Logger LOG = LoggerFactory.getLogger(AlertDeserializer.class);
    private transient ObjectMapper mapper;

    @Override
    public void open(InitializationContext context) { mapper = new ObjectMapper(); }

    @Override
    public PatternAlert deserialize(byte[] message) throws IOException {
        if (mapper == null) mapper = new ObjectMapper();
        try {
            return mapper.readValue(message, PatternAlert.class);
        } catch (Exception e) {
            LOG.warn("Failed to deserialize alert: {}", new String(message), e);
            return null;
        }
    }

    @Override
    public boolean isEndOfStream(PatternAlert next) { return false; }

    @Override
    public TypeInformation<PatternAlert> getProducedType() {
        return TypeInformation.of(PatternAlert.class);
    }
}
