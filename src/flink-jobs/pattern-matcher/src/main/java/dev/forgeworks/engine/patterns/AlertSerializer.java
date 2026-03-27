package dev.forgeworks.engine.patterns;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.apache.flink.api.common.serialization.SerializationSchema;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class AlertSerializer implements SerializationSchema<PatternAlert> {

    private static final Logger LOG = LoggerFactory.getLogger(AlertSerializer.class);
    private transient ObjectMapper mapper;

    @Override
    public void open(InitializationContext context) {
        mapper = new ObjectMapper();
    }

    @Override
    public byte[] serialize(PatternAlert alert) {
        if (mapper == null) mapper = new ObjectMapper();
        try {
            return mapper.writeValueAsBytes(alert);
        } catch (Exception e) {
            LOG.error("Failed to serialize alert: {}", alert, e);
            return new byte[0];
        }
    }
}
