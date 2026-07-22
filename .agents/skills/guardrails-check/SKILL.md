---
name: guardrails-check
description: Validate authorization boundaries, RBAC, PodSecurity compliance, and adapter execution guardrails. Use before deployments or when reviewing security posture.
argument-hint: '[scope: all|rbac|podsecurity|adapters|secrets]'
disable-model-invocation: true
allowed-tools: Bash(kubectl *) Read Grep Glob
---

Security guardrails check — scope: **$ARGUMENTS**

## Checks

### 1. RBAC Audit

Verify each service account has minimal permissions:

```bash
echo "=== Service Accounts ==="
kubectl get sa -n forge-engine --no-headers
kubectl get sa -n forge-works --no-headers
kubectl get sa -n forge-ml --no-headers

echo "=== Roles & Bindings ==="
kubectl get roles,rolebindings -n forge-engine --no-headers
kubectl get roles,rolebindings -n forge-works --no-headers
```

For each Role, verify it follows least-privilege:

- No `*` verbs
- No `*` resources
- No cluster-admin bindings

### 2. PodSecurity Compliance

Check all deployments comply with "restricted" policy:

```bash
for ns in forge-engine forge-works forge-ml; do
  echo "=== $ns ==="
  kubectl get pods -n $ns -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.spec.securityContext}{"\n"}{end}'
done
```

Verify:

- `runAsNonRoot: true`
- `seccompProfile.type: RuntimeDefault`
- `allowPrivilegeEscalation: false`
- `capabilities.drop: ["ALL"]`

### 3. Secrets Exposure

Check for hardcoded secrets or exposed sensitive data:

```bash
# Check for secrets in configmaps
kubectl get configmaps -A -o json | python3 -c "
import json,sys
data = json.load(sys.stdin)
for cm in data['items']:
  for k,v in (cm.get('data') or {}).items():
    if any(s in k.lower() for s in ['password','secret','token','key']):
      print(f\"WARNING: {cm['metadata']['namespace']}/{cm['metadata']['name']} has key: {k}\")
"
```

### 4. Adapter Execution Boundaries

Verify the Job Dispatcher can only create jobs in allowed namespace:

```bash
# Check dispatcher RBAC scope
kubectl get role job-dispatcher-role -n forge-engine -o yaml | grep -A5 "rules:"
```

Verify:

- Jobs only created in `forge-engine` namespace
- No cluster-scoped permissions
- Pod logs read-only (get, list, watch — no exec)

### 5. Webhook Auth Status

```bash
# Check if webhook secrets are configured
kubectl get deployment webhook-gateway -n forge-works -o jsonpath='{.spec.template.spec.containers[0].env}' | python3 -m json.tool 2>/dev/null | grep -i "secret\|require"
```

## Report Format

| Check        | Status    | Finding             |
| ------------ | --------- | ------------------- |
| RBAC         | pass/fail | details             |
| PodSecurity  | pass/fail | non-compliant pods  |
| Secrets      | pass/fail | exposed secrets     |
| Adapters     | pass/fail | boundary violations |
| Webhook Auth | pass/fail | auth configuration  |
