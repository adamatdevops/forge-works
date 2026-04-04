---
name: orchestration-ops
description: Manage Airflow, Flink, and K8s service lifecycle — restart, scale, redeploy, trigger DAGs, manage Flink savepoints. Use for operational tasks on the ForgeWorks engine.
argument-hint: "[action] [target] — e.g., restart flink/event-router, trigger dag/model_training_pipeline, scale gateway 2"
disable-model-invocation: true
allowed-tools: Bash(kubectl *) Bash(helm *) Bash(docker *)
---

Orchestration operation: **$ARGUMENTS**

## Available Actions

### Flink Operations
- **restart [job-name]**: Delete and re-apply FlinkDeployment
  ```bash
  kubectl delete flinkdeployment [job] -n forge-engine
  sleep 15
  kubectl apply -f infra/flink/base/[job].yaml
  ```
- **savepoint [job-name]**: Trigger savepoint before maintenance
- **status**: Show all FlinkDeployment states

### Airflow Operations
- **trigger [dag-id]**: Manually trigger a DAG run
  ```bash
  SCHED=$(kubectl get pods -n forge-engine -l component=scheduler,release=airflow -o jsonpath='{.items[0].metadata.name}')
  kubectl exec -n forge-engine $SCHED -c scheduler -- airflow dags trigger [dag-id]
  ```
- **pause/unpause [dag-id]**: Toggle DAG scheduling
- **sync-dags**: Copy updated DAGs to Airflow pods

### K8s Service Operations
- **restart [service]**: Rolling restart of a deployment
  ```bash
  kubectl rollout restart deployment/[service] -n [namespace]
  ```
- **scale [service] [replicas]**: Scale a deployment
- **logs [service]**: Tail recent logs

### Build & Deploy
- **build [service]**: Docker buildx + push to GHCR
  ```bash
  docker buildx build --no-cache --platform linux/amd64 \
    -t ghcr.io/adamatdevops/forge-works/[service]:dev \
    --push src/[service]/
  ```
- **deploy [service]**: Apply K8s manifests
  ```bash
  kubectl apply -k infra/[service]/base/
  ```

## Safety Rules
- Always confirm before destructive operations (delete, scale to 0)
- Check current state before modifying
- Report the before/after state
