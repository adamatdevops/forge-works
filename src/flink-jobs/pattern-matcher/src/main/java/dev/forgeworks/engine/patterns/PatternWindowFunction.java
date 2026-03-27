package dev.forgeworks.engine.patterns;

import org.apache.flink.api.common.state.ListState;
import org.apache.flink.api.common.state.ListStateDescriptor;
import org.apache.flink.api.common.state.StateTtlConfig;
import org.apache.flink.api.common.time.Time;
import org.apache.flink.api.common.typeinfo.TypeInformation;
import org.apache.flink.configuration.Configuration;
import org.apache.flink.streaming.api.functions.KeyedProcessFunction;
import org.apache.flink.util.Collector;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.ArrayList;
import java.util.List;

/**
 * Stateful pattern evaluation using a sliding event window.
 *
 * How it works:
 * 1. Each incoming event is appended to a keyed ListState (per group key)
 * 2. The window is bounded by TTL (10 minutes) — old events auto-evict
 * 3. On each new event, ALL rules are evaluated against the full window
 * 4. Matched patterns produce PatternAlert objects
 *
 * Why ListState with TTL (not Flink windows):
 * - Flink's built-in windows (tumbling/sliding) fire on window close,
 *   meaning you wait for the window to end before detecting patterns.
 *   For real-time "BEFORE" insights, we need to evaluate on every event.
 * - ListState + TTL gives us an ever-sliding view of recent events,
 *   evaluated eagerly on each arrival.
 * - TTL auto-cleanup prevents unbounded state growth.
 *
 * State sizing:
 * - Each event in state: ~500 bytes (serialized EventEnvelope)
 * - At 100 events/sec per group key, 10 min window: ~30MB per key
 * - Expected key count (repos + namespaces): ~50-100
 * - Total state: ~500MB-3GB (fits in TaskManager's 2GB for dev load)
 */
public class PatternWindowFunction
        extends KeyedProcessFunction<String, EventEnvelope, PatternAlert> {

    private static final Logger LOG = LoggerFactory.getLogger(PatternWindowFunction.class);
    private transient ListState<EventEnvelope> eventWindow;

    @Override
    public void open(Configuration parameters) {
        StateTtlConfig ttlConfig = StateTtlConfig.newBuilder(Time.minutes(10))
                .setUpdateType(StateTtlConfig.UpdateType.OnCreateAndWrite)
                .cleanupFullSnapshot()
                .build();

        ListStateDescriptor<EventEnvelope> descriptor = new ListStateDescriptor<>(
                "event-window", TypeInformation.of(EventEnvelope.class));
        descriptor.enableTimeToLive(ttlConfig);

        eventWindow = getRuntimeContext().getListState(descriptor);
    }

    @Override
    public void processElement(EventEnvelope event, Context ctx, Collector<PatternAlert> out)
            throws Exception {
        // Add event to window
        eventWindow.add(event);

        // Collect current window into a list for rule evaluation
        List<EventEnvelope> window = new ArrayList<>();
        for (EventEnvelope e : eventWindow.get()) {
            window.add(e);
        }

        // Evaluate all rules
        List<PatternAlert> alerts = PatternRules.evaluate(ctx.getCurrentKey(), window);

        for (PatternAlert alert : alerts) {
            LOG.info("Pattern matched: {} — {} (group: {}, events: {})",
                    alert.getPatternId(), alert.getPatternName(),
                    alert.getGroupKey(), alert.getEventCount());
            out.collect(alert);
        }
    }
}
