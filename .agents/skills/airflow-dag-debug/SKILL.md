---
name: airflow-dag-debug
description: Diagnose a failing or stuck Airflow DAG — import errors, task failures, scheduler issues. Use when investigating DAG problems or training pipeline failures.
argument-hint: '[dag-id: model_training_pipeline|pattern_consolidation]'
disable-model-invocation: true
allowed-tools: Bash(kubectl *)
---

Debug Airflow DAG: **$ARGUMENTS**

## Environment

- Namespace: `forge-engine`
- Airflow version: 3.1.8
- Executor: KubernetesExecutor
- DAGs: model_training_pipeline (nightly), pattern_consolidation (weekly)

## Diagnostic Steps

### 1. Check DAG Import Errors

```bash
SCHED=$(kubectl get pods -n forge-engine -l component=scheduler,release=airflow -o jsonpath='{.items[0].metadata.name}')
kubectl exec -n forge-engine $SCHED -c scheduler -- airflow dags list-import-errors 2>&1 | grep -v "info\|Warning\|plugin\|setup"
```

### 2. List DAG Runs

```bash
kubectl exec -n forge-engine $SCHED -c scheduler -- airflow dags list 2>&1 | grep -E "dag_id|$ARGUMENTS"
```

### 3. Check Task Instances

```bash
kubectl exec -n forge-engine $SCHED -c scheduler -- airflow tasks list $ARGUMENTS 2>&1 | grep -v "info\|Warning\|plugin\|setup"
```

### 4. Scheduler Logs (recent errors for this DAG)

```bash
kubectl logs -n forge-engine $SCHED -c scheduler --tail=50 2>&1 | grep "$ARGUMENTS" | grep -iE "success|fail|error|state=" | tail -10
```

### 5. Task Pod Logs (if task pods exist)

```bash
kubectl get pods -n forge-engine --no-headers 2>&1 | grep "$ARGUMENTS"
```

### 6. Airflow Component Health

```bash
kubectl get pods -n forge-engine -l release=airflow --no-headers
```

## Report Format

- **DAG**: name, schedule, last run status
- **Import Errors**: any parse/syntax issues
- **Failed Tasks**: which task, error message
- **Scheduler Health**: running, restarts
- **Recommendation**: fix suggestion
