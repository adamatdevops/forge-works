package dev.forgeworks.engine.insights;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.apache.flink.api.common.serialization.SerializationSchema;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class InsightSerializer implements SerializationSchema<Insight> {

    private static final long serialVersionUID = 1L;
    private static final Logger LOG = LoggerFactory.getLogger(InsightSerializer.class);
    private transient ObjectMapper mapper;

    @Override
    public void open(InitializationContext context) {
        mapper = new ObjectMapper();
    }

    @Override
    public byte[] serialize(Insight insight) {
        if (mapper == null) mapper = new ObjectMapper();
        try {
            return mapper.writeValueAsBytes(insight);
        } catch (Exception e) {
            LOG.error("Failed to serialize insight: {}", insight.getInsightId(), e);
            throw new RuntimeException(
                    "Serialization failed for insight " + insight.getInsightId(), e);
        }
    }
}
