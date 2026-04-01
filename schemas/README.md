# ForgeWorks Canonical Schemas

These JSON Schemas define the contract for data flowing through the ForgeWorks pipeline. All implementations (Python Pydantic models, Java POJOs) must conform to these schemas.

## Schemas

| Schema | Producers | Consumers |
|--------|-----------|-----------|
| `event-envelope.schema.json` | Webhook Gateway (Python) | Event Router (Java), Pattern Matcher (Java) |
| `pattern-alert.schema.json` | Pattern Matcher (Java) | Insight Generator (Java), Job Dispatcher (Python) |

## Implementations

Each implementation is annotated with `@schema: <schema-file>` to indicate which canonical schema it conforms to.

| Schema | Python | Java |
|--------|--------|------|
| Event Envelope | `src/webhook-gateway/app/schemas.py:EventEnvelope` | `src/flink-jobs/event-router/.../EventEnvelope.java`, `src/flink-jobs/pattern-matcher/.../EventEnvelope.java` |
| Pattern Alert | `src/job-dispatcher/app/schemas.py:Insight` (consumer side) | `src/flink-jobs/pattern-matcher/.../PatternAlert.java` (producer), `src/flink-jobs/insight-generator/.../PatternAlert.java` (consumer) |

## Why JSON Schema (not Avro/Protobuf)

- **No build-time code generation** needed — implementations are hand-written
- **Language-neutral** — works for Python + Java without tooling
- **Validation** — can be used in CI to validate test payloads
- **Documentation** — self-documenting with descriptions
- **Low friction** — no schema registry infrastructure required for dev

For production, consider migrating to Avro + Confluent Schema Registry for runtime schema evolution enforcement.
