---
name: kafka-debug
description: Diagnose a Kafka topic or consumer group — lag, partition skew, broker health, message inspection. Use when investigating delivery issues, consumer lag, or message flow problems.
argument-hint: "[topic-name or consumer-group-name]"
disable-model-invocation: true
allowed-tools: Bash(kubectl *)
---

Diagnose Kafka issue for: **$ARGUMENTS**

## Environment
- Kafka broker: `forge-kafka-forge-kafka-pool-0` in namespace `forge-engine`
- Bootstrap: `forge-kafka-kafka-bootstrap.forge-engine.svc.cluster.local:9092`

## Diagnostic Steps

### 1. Topic Details (if argument looks like a topic name)
```bash
kubectl exec -n forge-engine forge-kafka-forge-kafka-pool-0 -- bin/kafka-topics.sh \
  --bootstrap-server localhost:9092 --describe --topic $ARGUMENTS
```

### 2. Consumer Group Lag (if argument looks like a consumer group)
```bash
kubectl exec -n forge-engine forge-kafka-forge-kafka-pool-0 -- bin/kafka-consumer-groups.sh \
  --bootstrap-server localhost:9092 --describe --group $ARGUMENTS
```

### 3. List All Consumer Groups (if unsure)
```bash
kubectl exec -n forge-engine forge-kafka-forge-kafka-pool-0 -- bin/kafka-consumer-groups.sh \
  --bootstrap-server localhost:9092 --list
```

### 4. Peek at Recent Messages (last 3)
```bash
kubectl exec -n forge-engine forge-kafka-forge-kafka-pool-0 -- bin/kafka-console-consumer.sh \
  --bootstrap-server localhost:9092 --topic $ARGUMENTS --from-beginning --max-messages 3 --timeout-ms 10000
```

### 5. Broker Health
```bash
kubectl get pods -n forge-engine -l strimzi.io/cluster=forge-kafka --no-headers
kubectl get kafka forge-kafka -n forge-engine -o jsonpath='{.status.conditions[*].type}{"\t"}{.status.conditions[*].status}'
```

## Report Format

- **Topic/Group**: name, partition count, replication factor
- **Lag**: per-partition lag, total lag
- **Issues Found**: under-replicated, offline partitions, stuck consumers
- **Recommendation**: what to do next
