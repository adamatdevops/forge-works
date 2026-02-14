# ForgeWorks Secrets

Secrets are created via kubectl commands (not stored in git).

## Required Secrets

### forge-engine namespace
| Secret Name | Keys | Used By |
|-------------|------|---------|
| `forge-postgres-credentials` | `username`, `password`, `host`, `port`, `database` | Backend, Airflow |
| `forge-redis-credentials` | `host`, `port`, `password` | Backend |

### forge-works namespace
| Secret Name | Keys | Used By |
|-------------|------|---------|
| `forge-app-config` | `secret-key`, `jwt-secret` | Backend API |
| `forge-postgres-credentials` | `username`, `password`, `host`, `port`, `database` | Backend |
| `forge-redis-credentials` | `host`, `port`, `password` | Backend |

### forge-ml namespace
| Secret Name | Keys | Used By |
|-------------|------|---------|
| `forge-ml-config` | `model-registry-url` | ML Runner |

## Create Secrets

Run: `./create-secrets.sh`

## S3 Access

S3 access is configured via IRSA (IAM Roles for Service Accounts).
No S3 credentials are stored as secrets.
