# ForgeWorks Kafka Infrastructure

> **Component:** Event Bus Infrastructure
> **Version:** 1.0.0
> **Status:** Phase 1 Foundation

---

## Overview

This directory contains the Strimzi Kafka deployment manifests for ForgeWorks Engine.

## Architecture Decision

**Choice:** Strimzi (Kubernetes Operator)

See [ADR-007: Kafka Deployment Strategy](../../adr/007-kafka-deployment.md) for full rationale.

## Directory Structure

```
infra/kafka/
├── README.md                          # This file
├── base/
│   ├── kustomization.yaml             # Base Kustomize config
│   ├── namespace.yaml                 # forge-engine namespace
│   ├── kafka-cluster.yaml             # Strimzi Kafka CRD
│   ├── kafka-metrics-config.yaml      # JMX to Prometheus config
│   └── topics/
│       ├── forge-events-github.yaml   # GitHub webhook events
│       ├── forge-events-argocd.yaml   # ArgoCD sync events
│       ├── forge-events-kubernetes.yaml # K8s events
│       ├── forge-insights-realtime.yaml # Flink real-time output
│       ├── forge-jobs-pending.yaml    # Jobs awaiting execution
│       ├── forge-jobs-results.yaml    # Job completion results
│       ├── forge-learning-feedback.yaml # User feedback
│       ├── forge-learning-outcomes.yaml # Transformation outcomes
│       ├── forge-mcp-updates.yaml     # MCP template updates
│       └── forge-dlq-events.yaml      # Dead Letter Queue
└── overlays/
    ├── dev/
    │   └── kustomization.yaml         # Dev overrides (1 broker)
    └── prod/
        └── kustomization.yaml         # Prod enhancements

```

---

## Topic Partitioning Strategy

### Design Principles

1. **Event-Driven Ordering:** Partition by logical key to ensure related events stay ordered
2. **Parallel Processing:** Higher partitions for high-volume topics
3. **Consumer Scalability:** Partitions >= expected consumer instances

### Topic Categories

| Category | Topics | Partitions | Key Strategy |
|----------|--------|------------|--------------|
| **Events** | github, argocd, kubernetes | 6 | Source identifier (repo, app, namespace) |
| **Insights** | realtime | 6 | Correlation ID |
| **Jobs** | pending, results | 6 | Job ID |
| **Learning** | feedback, outcomes | 3 | Correlation ID / Job ID |
| **MCP** | updates | 3 | Template name |
| **DLQ** | events | 3 | Original topic |

### Partitioning Rationale

**High Volume Topics (6 partitions):**
- `forge.events.*` - Expected 100s of events/minute at scale
- `forge.insights.realtime` - Matches Flink parallelism
- `forge.jobs.*` - Enables parallel job processing

**Lower Volume Topics (3 partitions):**
- `forge.learning.*` - Batch-oriented, lower throughput
- `forge.mcp.updates` - Infrequent template updates
- `forge.dlq.events` - Hopefully minimal traffic

### Key Selection

| Topic | Key | Ordering Guarantee |
|-------|-----|-------------------|
| `forge.events.github` | `repository.full_name` | All events for same repo ordered |
| `forge.events.argocd` | `application.name` | All events for same app ordered |
| `forge.events.kubernetes` | `namespace/name` | All events for same resource ordered |
| `forge.jobs.*` | `job_id` | Job lifecycle events ordered |
| `forge.learning.*` | `correlation_id` / `job_id` | Related data stays together |
| `forge.dlq.events` | `original_topic` | Group by source for debugging |

---

## Retention Policy

| Topic Category | Retention | Rationale |
|---------------|-----------|-----------|
| Events | 7 days | Short-lived processing data |
| Insights | 14 days | Longer for analysis |
| Jobs | 7-14 days | Match job lifecycle |
| Learning | 30-90 days | Historical training data |
| MCP | 30 days | Template version history |
| DLQ | 30 days | Debugging failed events |

---

## Prerequisites

### 1. Install Strimzi Operator

```bash
# Create Strimzi namespace
kubectl create namespace kafka

# Install Strimzi via Helm
helm repo add strimzi https://strimzi.io/charts/
helm repo update
helm install strimzi-cluster-operator strimzi/strimzi-kafka-operator \
  --namespace kafka \
  --set watchNamespaces="{forge-engine}"
```

Or via YAML:

```bash
kubectl create -f 'https://strimzi.io/install/latest?namespace=kafka' -n kafka
```

### 2. Verify Operator Running

```bash
kubectl get pods -n kafka
# NAME                                        READY   STATUS    RESTARTS   AGE
# strimzi-cluster-operator-xxxxx-xxxxx        1/1     Running   0          1m
```

---

## Deployment

### Development Environment

```bash
# Deploy with dev overlay (1 broker, reduced resources)
kubectl apply -k infra/kafka/overlays/dev

# Verify deployment
kubectl get kafka -n forge-engine
kubectl get kafkatopic -n forge-engine
```

### Production Environment

```bash
# Deploy with prod overlay (3 brokers, enhanced resources)
kubectl apply -k infra/kafka/overlays/prod
```

### Verify Deployment

```bash
# Check Kafka cluster status
kubectl get kafka forge-kafka -n forge-engine -o jsonpath='{.status.conditions}'

# List topics
kubectl get kafkatopic -n forge-engine

# Check pod status
kubectl get pods -n forge-engine -l strimzi.io/cluster=forge-kafka
```

---

## Operations

### Produce Test Message

```bash
# Get bootstrap server
BOOTSTRAP=$(kubectl get kafka forge-kafka -n forge-engine -o jsonpath='{.status.listeners[0].bootstrapServers}')

# Port forward for local access
kubectl port-forward svc/forge-kafka-kafka-bootstrap -n forge-engine 9092:9092

# Produce message
kubectl run kafka-producer -ti --rm \
  --image=quay.io/strimzi/kafka:latest-kafka-3.6.1 \
  --restart=Never \
  -- bin/kafka-console-producer.sh \
  --bootstrap-server forge-kafka-kafka-bootstrap.forge-engine:9092 \
  --topic forge.events.github
```

### Consume Test Message

```bash
kubectl run kafka-consumer -ti --rm \
  --image=quay.io/strimzi/kafka:latest-kafka-3.6.1 \
  --restart=Never \
  -- bin/kafka-console-consumer.sh \
  --bootstrap-server forge-kafka-kafka-bootstrap.forge-engine:9092 \
  --topic forge.events.github \
  --from-beginning
```

### Check Consumer Lag

```bash
kubectl run kafka-lag -ti --rm \
  --image=quay.io/strimzi/kafka:latest-kafka-3.6.1 \
  --restart=Never \
  -- bin/kafka-consumer-groups.sh \
  --bootstrap-server forge-kafka-kafka-bootstrap.forge-engine:9092 \
  --describe --all-groups
```

---

## Monitoring

### Prometheus Metrics

Kafka metrics are exposed via JMX exporter. Configure Prometheus to scrape:

```yaml
- job_name: 'kafka'
  kubernetes_sd_configs:
    - role: pod
      namespaces:
        names:
          - forge-engine
  relabel_configs:
    - source_labels: [__meta_kubernetes_pod_label_strimzi_io_kind]
      regex: Kafka
      action: keep
```

### Key Metrics

| Metric | Description |
|--------|-------------|
| `kafka_server_brokertopicmetrics_messagesinpersec` | Messages/sec per topic |
| `kafka_server_replicamanager_underreplicatedpartitions` | Under-replicated partitions |
| `kafka_controller_kafkacontroller_activecontrollercount` | Active controller (should be 1) |
| `kafka_network_requestmetrics_requestspersec` | Request throughput |

---

## Troubleshooting

### Common Issues

**Pods not starting:**
```bash
kubectl describe pod -n forge-engine -l strimzi.io/cluster=forge-kafka
kubectl logs -n forge-engine -l strimzi.io/cluster=forge-kafka
```

**Topic creation fails:**
```bash
kubectl describe kafkatopic <topic-name> -n forge-engine
```

**Insufficient storage:**
```bash
# Check PVC status
kubectl get pvc -n forge-engine
```

---

## References

- [Strimzi Documentation](https://strimzi.io/docs/)
- [Kafka Configuration Reference](https://kafka.apache.org/documentation/#configuration)
- [ADR-007: Kafka Deployment](../../adr/007-kafka-deployment.md)
- [ACTION_PLAN_PHASE-1.md](../../roadmap/ACTION_PLAN_PHASE-1.md)

---

*Created: 2025-01-23*
*Last Updated: 2025-01-23*
