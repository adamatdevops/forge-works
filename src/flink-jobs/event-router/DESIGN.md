# Event Router — Design Document

> **Service:** ForgeWorks Event Router
> **Type:** Apache Flink Streaming Job (Java)
> **Phase:** Engine Phase 2 — Real-Time Layer
> **Status:** In Development

---

## Purpose

The Event Router is the first Flink streaming job in the ForgeWorks Engine. It is the bridge between **Phase 1** (Kafka event ingestion) and the rest of the real-time processing pipeline.

```
Webhook Gateway (Phase 1)          Event Router (Phase 2)           Downstream (Phase 2+)
═══════════════════════            ═══════════════════════           ════════════════════

GitHub  ─┐                         ┌─────────────┐
ArgoCD  ─┤→ Kafka (forge.events.*) │  Consume    │
K8s     ─┘                         │  Deduplicate │→ forge.insights.realtime
                                   │  Route       │
                                   │  Serialize   │→ forge.dlq.events (unroutable)
                                   └─────────────┘
```

## What It Does

1. **Consumes** events from all `forge.events.*` Kafka topics (GitHub, ArgoCD, Kubernetes)
2. **Deserializes** JSON into `EventEnvelope` objects (same schema webhook-gateway produces)
3. **Deduplicates** events using Flink keyed state with 1-hour TTL
4. **Routes** known sources (github, argocd, kubernetes) to `forge.insights.realtime`
5. **Dead-letters** unknown sources to `forge.dlq.events`

## Why Flink (Not Another Python Service)

| Concern | Python Service | Flink |
|---------|---------------|-------|
| **Exactly-once processing** | Manual offset management | Built-in with checkpoints |
| **Deduplication** | External store (Redis) | In-JVM keyed state, survives restarts |
| **Backpressure** | Manual, error-prone | Automatic — slows Kafka consumer |
| **Recovery** | Restart from scratch | Resume from checkpoint |
| **Latency at scale** | ~10-50ms + network hops | <10ms in-JVM |
| **State management** | External DB/cache | Co-located, zero network hops |

## Why Java (Not PyFlink)

PyFlink adds a Python process ↔ JVM bridge for every record — ~10-50ms serialization overhead per event. For a routing/deduplication job that is pure data transformation, Java runs natively in the Flink JVM with zero overhead.

**Rule of thumb:** Use Java for Flink jobs that are latency-sensitive or high-throughput. Use PyFlink only when you need Python-specific ML libraries (scikit-learn, numpy) in the processing pipeline.

---

## Architecture

### Pipeline

```
KafkaSource (forge.events.*)
    │
    ▼
Filter Invalid (null check)
    │
    ▼
KeyBy (source:event_id)
    │
    ▼
DeduplicationFilter (keyed state, 1h TTL)
    │
    ▼
RoutingFunction (ProcessFunction)
    │                    │
    ▼                    ▼
Main Output          Side Output (DLQ_TAG)
    │                    │
    ▼                    ▼
KafkaSink            KafkaSink
(forge.insights.     (forge.dlq.events)
 realtime)
```

### Key Classes

| Class | Purpose |
|-------|---------|
| `EventRouterJob` | Main entry point — wires the Flink pipeline |
| `EventEnvelope` | POJO matching webhook-gateway's JSON schema |
| `EventDeserializer` | Kafka bytes → EventEnvelope (handles malformed JSON gracefully) |
| `EventSerializer` | EventEnvelope → Kafka bytes |
| `DeduplicationFilter` | Stateful filter using Flink keyed state with TTL |

### Event Envelope Schema

```json
{
  "event_id": "evt_abc123",
  "correlation_id": "corr_xyz789",
  "timestamp": "2026-01-23T10:30:00Z",
  "source": "github",
  "type": "push",
  "metadata": {
    "repository": "org/repo",
    "sender": "username"
  },
  "payload": { }
}
```

---

## Deduplication Strategy

### How It Works

- Events are keyed by `source:event_id` (the `routingKey()`)
- Flink maintains a `ValueState<Boolean>` per key ("have I seen this?")
- TTL is set to **1 hour** — after that, the state entry is auto-evicted
- If the same `event_id` arrives twice within 1 hour, the second is dropped

### Why Flink State (Not Redis)

| Aspect | Redis | Flink Keyed State |
|--------|-------|-------------------|
| Latency | ~1ms (network hop) | ~0.01ms (in-JVM) |
| Durability | Separate infra to manage | Checkpoint handles it |
| Scaling | Manual sharding | Automatic with Flink parallelism |
| Cleanup | Manual TTL scripts | Built-in `StateTtlConfig` |
| State size | ~100MB (fits easily) | Co-located with processor |

### State Sizing

- Each entry: ~64 bytes (key + boolean + TTL metadata)
- At 1000 events/sec with 1h TTL: ~230MB peak
- Well within TaskManager's 2GB memory allocation

---

## Routing Rules

| Source | Destination | Logic |
|--------|-------------|-------|
| `github` | `forge.insights.realtime` | All GitHub events (push, PR, issues) |
| `argocd` | `forge.insights.realtime` | All ArgoCD events (sync, health) |
| `kubernetes` | `forge.insights.realtime` | All K8s events (pod, node, deploy) |
| Unknown/null | `forge.dlq.events` | Side output for investigation |

This is the **MVP routing table**. Phase 2 Sprint 2.2 will add the Pattern Matcher job which consumes from `forge.insights.realtime` and applies rule-based pattern detection.

---

## Build & Dependency Management

### Jackson Shading (Critical)

Flink has its own Jackson version bundled inside `flink-dist-1.20.3.jar` (shaded/relocated). If we bundle a different Jackson version in our fat jar, the JVM loads both — leading to `NoSuchMethodError` at runtime when one version's `ObjectMapper` calls the other version's `BufferRecycler`.

**Solution:** We bundle Jackson 2.15.3 and **relocate** it during the Maven shade phase:

```xml
<relocation>
    <pattern>com.fasterxml.jackson</pattern>
    <shadedPattern>dev.forgeworks.shaded.jackson</shadedPattern>
</relocation>
```

This renames all Jackson classes in our jar to `dev.forgeworks.shaded.jackson.*`, so they never conflict with Flink's internal Jackson. Our code references `com.fasterxml.jackson.databind.ObjectMapper` in source, but at runtime it becomes `dev.forgeworks.shaded.jackson.databind.ObjectMapper` — completely isolated.

### Dependencies

| Dependency | Version | Scope | Notes |
|------------|---------|-------|-------|
| flink-streaming-java | 1.20.3 | provided | Flink runtime provides this |
| flink-clients | 1.20.3 | provided | Flink runtime provides this |
| flink-connector-kafka | 3.3.0-1.20 | compile (shaded) | Bundled in fat jar |
| jackson-core | 2.15.3 | compile (shaded+relocated) | Isolated from Flink's Jackson |
| jackson-databind | 2.15.3 | compile (shaded+relocated) | Isolated from Flink's Jackson |
| jackson-annotations | 2.15.3 | compile (shaded+relocated) | Isolated from Flink's Jackson |
| slf4j-api | 2.0.9 | provided | Flink runtime provides this |

---

## Deployment

### FlinkDeployment CRD

The Event Router is deployed as a separate `FlinkDeployment` (not sharing the base `forge-flink` cluster). This gives it:
- Its own JobManager and TaskManager
- Independent scaling and resource allocation
- Isolated failure domain — if Event Router crashes, other Flink jobs are unaffected

### Resources (Dev)

| Component | CPU | Memory |
|-----------|-----|--------|
| JobManager | 0.5 | 1536m |
| TaskManager | 0.5 | 2048m |

### Configuration

| Setting | Value | Why |
|---------|-------|-----|
| Checkpointing | EXACTLY_ONCE, 60s | Ensures no duplicate processing on restart |
| State backend | hashmap | Dev — sufficient for <500MB state |
| Restart strategy | exponential-delay (1s→60s) | Self-healing without overwhelming Kafka |
| Kafka offset | `latest` | Only process new events (not replay history) |
| Consumer group | `forgeworks-event-router` | Dedicated group for offset tracking |

---

## Observability

### Flink Dashboard

Port-forward the JobManager REST API:
```bash
kubectl port-forward svc/event-router-rest 8081:8081 -n forge-engine
```

### Key Metrics to Watch

| Metric | Healthy | Alert |
|--------|---------|-------|
| Job status | RUNNING | RESTARTING / FAILED |
| Consumer lag | <100 | >1000 |
| Checkpoint duration | <5s | >30s |
| Records in/out | Roughly equal | Large divergence |

---

## Testing

### End-to-End Test

```bash
# 1. Send webhook
curl -X POST localhost:8080/webhook/github \
  -H 'Content-Type: application/json' \
  -d '{"action":"push","repository":{"full_name":"test/repo"},"sender":{"login":"adam"}}'

# 2. Consume from insights topic
kubectl run kafka-test -n forge-engine --rm -it --restart=Never \
  --image=quay.io/strimzi/kafka:0.50.0-kafka-4.1.1 \
  -- bin/kafka-console-consumer.sh \
  --bootstrap-server forge-kafka-kafka-bootstrap.forge-engine.svc.cluster.local:9092 \
  --topic forge.insights.realtime --from-beginning --max-messages 1

# Expected: EventEnvelope JSON with source=github, type=unknown.push
```

---

## File Structure

```
src/flink-jobs/event-router/
├── pom.xml                                          # Maven build config
├── Dockerfile                                       # Multi-stage: Maven build → Flink runtime
├── DESIGN.md                                        # This document
└── src/main/
    ├── java/dev/forgeworks/engine/router/
    │   ├── EventRouterJob.java                      # Pipeline entry point
    │   ├── EventEnvelope.java                       # Event POJO
    │   ├── EventDeserializer.java                   # Kafka → EventEnvelope
    │   ├── EventSerializer.java                     # EventEnvelope → Kafka
    │   └── DeduplicationFilter.java                 # Stateful dedup filter
    └── resources/
        └── log4j2.properties                        # Logging config
```

---

*Created: 2026-03-22*
*Phase: Engine Phase 2 — Sprint 2.2 (T-E2.2.1, T-E2.2.2)*
