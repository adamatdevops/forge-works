package dev.forgeworks.engine.dr;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.apache.flink.api.common.serialization.SerializationSchema;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/** Serializes prediction envelopes to Kafka. Mirrors pattern-matcher/AlertSerializer. */
public class PredictionSerializer implements SerializationSchema<PredictionEnvelope> {

    private static final long serialVersionUID = 1L;
    private static final Logger LOG = LoggerFactory.getLogger(PredictionSerializer.class);
    private transient ObjectMapper mapper;

    @Override
    public void open(InitializationContext context) {
        mapper = new ObjectMapper();
    }

    @Override
    public byte[] serialize(PredictionEnvelope prediction) {
        if (mapper == null) mapper = new ObjectMapper();
        try {
            return mapper.writeValueAsBytes(prediction);
        } catch (Exception e) {
            LOG.error("Failed to serialize prediction: {}", prediction.getEventId(), e);
            throw new RuntimeException(
                    "Serialization failed for prediction " + prediction.getEventId(), e);
        }
    }
}
