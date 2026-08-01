package dev.forgeworks.engine.dr;

import com.fasterxml.jackson.databind.ObjectMapper;
import java.io.IOException;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import org.apache.flink.api.common.serialization.DeserializationSchema;
import org.apache.flink.api.common.typeinfo.TypeInformation;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/** Deserializes normalized events from Kafka. Mirrors pattern-matcher/EventDeserializer. */
public class EventDeserializer implements DeserializationSchema<NormalizedEvent> {

    private static final long serialVersionUID = 1L;
    private static final Logger LOG = LoggerFactory.getLogger(EventDeserializer.class);
    private transient ObjectMapper mapper;

    @Override
    public void open(InitializationContext context) {
        mapper = new ObjectMapper();
    }

    @Override
    public NormalizedEvent deserialize(byte[] message) throws IOException {
        if (mapper == null) mapper = new ObjectMapper();
        try {
            return mapper.readValue(message, NormalizedEvent.class);
        } catch (Exception e) {
            LOG.warn(
                    "Failed to deserialize event: size={}, sha256={}",
                    message.length,
                    sha256(message),
                    e);
            return null;
        }
    }

    @Override
    public boolean isEndOfStream(NormalizedEvent nextElement) {
        return false;
    }

    @Override
    public TypeInformation<NormalizedEvent> getProducedType() {
        return TypeInformation.of(NormalizedEvent.class);
    }

    private static String sha256(byte[] data) {
        try {
            byte[] hash = MessageDigest.getInstance("SHA-256").digest(data);
            StringBuilder sb = new StringBuilder();
            for (int i = 0; i < Math.min(8, hash.length); i++) {
                sb.append(String.format("%02x", hash[i]));
            }
            return sb.toString();
        } catch (NoSuchAlgorithmException e) {
            return "unknown";
        }
    }
}
