package dev.forgeworks.engine.router;

import org.apache.flink.api.common.functions.RichFilterFunction;
import org.apache.flink.api.common.state.StateTtlConfig;
import org.apache.flink.api.common.state.ValueState;
import org.apache.flink.api.common.state.ValueStateDescriptor;
import org.apache.flink.api.common.time.Time;
import org.apache.flink.api.common.typeinfo.TypeInformation;
import org.apache.flink.configuration.Configuration;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * Stateful deduplication filter using Flink keyed state.
 *
 * <p>How it works: - Each event is keyed by source + event_id (routingKey) - State stores a boolean
 * "seen" flag per key - TTL of 1 hour auto-evicts old entries (prevents unbounded state growth) -
 * If we've seen this event_id before, filter it out
 *
 * <p>Why Flink state (not Redis/external): - Zero network hops — state is co-located with
 * processing - Survives restarts via checkpoints - Automatic cleanup via TTL - Scales linearly with
 * Flink parallelism
 */
public class DeduplicationFilter extends RichFilterFunction<EventEnvelope> {

    private static final Logger LOG = LoggerFactory.getLogger(DeduplicationFilter.class);
    private transient ValueState<Boolean> seenState;

    @Override
    public void open(Configuration parameters) {
        StateTtlConfig ttlConfig =
                StateTtlConfig.newBuilder(Time.hours(1))
                        .setUpdateType(StateTtlConfig.UpdateType.OnCreateAndWrite)
                        .cleanupFullSnapshot()
                        .build();

        ValueStateDescriptor<Boolean> descriptor =
                new ValueStateDescriptor<>("event-seen", TypeInformation.of(Boolean.class));
        descriptor.enableTimeToLive(ttlConfig);

        seenState = getRuntimeContext().getState(descriptor);
    }

    @Override
    public boolean filter(EventEnvelope event) throws Exception {
        if (event == null || event.getEventId() == null) {
            return false;
        }

        Boolean seen = seenState.value();
        if (seen != null && seen) {
            LOG.debug("Duplicate event filtered: {}", event.getEventId());
            return false;
        }

        seenState.update(true);
        return true;
    }
}
