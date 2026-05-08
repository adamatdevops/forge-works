# IAM (IRSA) — repo-codified trust + managed policies

This directory is the source of truth for every IAM role and managed policy
that ForgeWorks workloads assume via IRSA. Files here are pulled from the
live AWS account and committed back so least-privilege claims can be
audited and reproduced from git.

## Layout

```
infra/iam/
├── trust-policies/                          # AssumeRolePolicyDocument per role
│   └── {role-name}-trust.json
├── policies/                                # Managed-policy documents
│   └── {policy-name}.json                   # filename matches AWS policy name
└── scripts/
    └── diff-iam.sh                          # diff repo vs. live, exit non-zero on drift
```

The role name embedded in the trust filename (minus the `-trust` suffix) is
the AWS role name. The policy filename's basename is the AWS policy name.

A few legacy policy files use a `-policy.json` suffix that does not appear
in the AWS policy name (`fw-engine-s3-policy.json` → AWS `fw-engine-s3-access`).
`diff-iam.sh` tolerates this; new files should match the AWS name 1:1.

## Roles & policies catalog

| Role | Service Account | Attached managed policy | S3 prefix scope |
|------|-----------------|--------------------------|-----------------|
| `fw-forge-engine-flink-sa` | `forge-engine/flink-sa` | `fw-engine-s3-access` | `s3://fw-state-dev/*`, `s3://fw-logs-dev/*` |
| `fw-forge-engine-airflow-sa` | `forge-engine/airflow-sa` | (read-only via trust) | n/a |
| `fw-forge-engine-normalizer-sa` | `forge-engine/normalizer-sa` | `fw-engine-normalizer-s3-access` | `s3://fw-state-dev/normalizer/configs/*` |
| `fw-forge-engine-normalizer-terraform-sa` | `forge-engine/normalizer-terraform-sa` | `fw-engine-normalizer-terraform-s3-access` | `s3://fw-state-dev/normalizer/configs/terraform/*` |
| `fw-forge-engine-normalizer-github-actions-sa` | `forge-engine/normalizer-github-actions-sa` | `fw-engine-normalizer-github-actions-s3-access` | `s3://fw-state-dev/normalizer/configs/github-actions/*` |
| `fw-forge-ml-ml-runner-sa` | `forge-ml/ml-runner-sa` | `fw-ml-s3-access` | `s3://fw-state-dev/ml/runs/*` |
| `fw-forge-ml-ml-inference-sa` | `forge-ml/ml-inference-sa` | `fw-ml-inference-s3-access` | `s3://fw-state-dev/ml/inference/*` |

## Operational notes

- IAM `iam:CreatePolicy` / `iam:CreateRole` require the `fw-admin` AWS profile.
  The SSO profile `fw-infra-permission-set` lacks these grants.
- After any IAM change applied via console or CLI, regenerate the
  corresponding files here and `diff-iam.sh` should exit 0.
- A future sprint will gate this in CI; today it is a manual reproducibility
  check.

## Verifying repo vs. AWS

```bash
AWS_PROFILE=fw-admin ./infra/iam/scripts/diff-iam.sh
```

Exit 0 means committed JSONs match live state. Exit 1 prints a unified diff
per drifted artifact.
