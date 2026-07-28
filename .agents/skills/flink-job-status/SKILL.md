---
name: flink-job-status
description: Check Flink job health — status, checkpoints, backpressure, errors. Use when a Flink job may be failing, restarting, or producing incorrect output.
argument-hint: '[job-name: event-router|pattern-matcher|insight-generator]'
disable-model-invocation: true
allowed-tools: Bash(kubectl *) Bash(curl *)
---

Check Flink job health for: **$ARGUMENTS**

## Environment

- Namespace: `forge-engine`
- Jobs: event-router, pattern-matcher, insight-generator

## Diagnostic Steps

### 1. FlinkDeployment Status

```bash
kubectl get flinkdeployment $ARGUMENTS -n forge-engine -o jsonpath='{.status.jobStatus.state}{"\t"}{.status.lifecycleState}'
```

### 2. Pod Status

```bash
kubectl get pods -n forge-engine -l app=$ARGUMENTS --no-headers
```

### 3. Checkpoint Info (via REST API)

```bash
JM_POD=$(kubectl get pods -n forge-engine -l app=$ARGUMENTS,component=jobmanager -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
if [ -n "$JM_POD" ]; then
  kubectl exec -n forge-engine $JM_POD -- curl -s localhost:8081/jobs 2>/dev/null | python3 -m json.tool
fi
```

### 4. TaskManager Errors

```bash
kubectl logs -n forge-engine -l app=$ARGUMENTS,component=taskmanager --tail=30 2>/dev/null | grep -iE "error|exception|fail|cause" | tail -10
```

### 5. JobManager Errors

```bash
kubectl logs -n forge-engine -l app=$ARGUMENTS --tail=30 2>/dev/null | grep -iE "error|exception|fail|RUNNING|FAILED" | tail -10
```

### 6. Restart Count

```bash
kubectl get pods -n forge-engine -l app=$ARGUMENTS -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.status.containerStatuses[0].restartCount}{"\n"}{end}'
```

## Report Format

| Metric      | Value                          |
| ----------- | ------------------------------ |
| Job Status  | RUNNING/FAILED/RESTARTING      |
| Lifecycle   | STABLE/DEPLOYED/RECONCILING    |
| Checkpoints | completed count, last duration |
| Restarts    | count                          |
| Errors      | last error message if any      |

**Recommendation**: what to do if unhealthy.
