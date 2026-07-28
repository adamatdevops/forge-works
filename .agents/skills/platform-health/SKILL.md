---
name: platform-health
description: Full stack health check across Kafka, Flink, Airflow, MLflow, and K8s workloads. Use when asked about system status, before deployments, or to diagnose widespread issues.
context: fork
agent: Explore
allowed-tools: Bash(kubectl *) Bash(curl *)
---

Run a comprehensive health check across all ForgeWorks platform components.

## Current Cluster

- Context: !`kubectl config current-context 2>/dev/null || echo "unknown"`

## Check Each Component

### 1. Kubernetes Nodes

```bash
kubectl get nodes -o wide
```

### 2. Unhealthy Pods (all namespaces)

```bash
kubectl get pods -A --no-headers | grep -v "Running\|Completed" | head -20
```

### 3. Kafka (forge-engine)

```bash
kubectl get pods -n forge-engine -l strimzi.io/cluster=forge-kafka --no-headers
kubectl exec -n forge-engine forge-kafka-forge-kafka-pool-0 -- bin/kafka-topics.sh --bootstrap-server localhost:9092 --list 2>/dev/null
```

### 4. Flink Jobs

```bash
kubectl get flinkdeployments -n forge-engine
```

### 5. Webhook Gateway (forge-works)

```bash
kubectl get pods -n forge-works -l app.kubernetes.io/name=webhook-gateway --no-headers
```

### 6. Job Dispatcher (forge-engine)

```bash
kubectl get pods -n forge-engine -l app.kubernetes.io/name=job-dispatcher --no-headers
```

### 7. Airflow (forge-engine)

```bash
kubectl get pods -n forge-engine -l release=airflow --no-headers
```

### 8. MLflow (forge-ml)

```bash
kubectl get pods -n forge-ml --no-headers
```

### 9. Recent Warning/Error Events

```bash
kubectl get events -A --field-selector type!=Normal --sort-by=.lastTimestamp 2>/dev/null | tail -10
```

## Output Format

Summarize as a status table:

| Component  | Status           | Details                   |
| ---------- | ---------------- | ------------------------- |
| Nodes      | healthy/degraded | count, not-ready          |
| Kafka      | healthy/degraded | broker count, topic count |
| Flink      | healthy/degraded | jobs running/failed       |
| Gateway    | healthy/degraded | pod status                |
| Dispatcher | healthy/degraded | pod status                |
| Airflow    | healthy/degraded | component status          |
| MLflow     | healthy/degraded | pod status                |

Flag anything that needs immediate attention.
