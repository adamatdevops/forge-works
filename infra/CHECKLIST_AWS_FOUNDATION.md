# AWS Foundation Checklist

> **Sprint:** I-(-1)
> **Version:** 1.0.0
> **Created:** 2025-01-26
> **Purpose:** Step-by-step checklist for AWS infrastructure setup before ForgeWorks deployment

---

## Quick Reference

```
EXECUTION ORDER
═══════════════════════════════════════════════════════════════

PHASE A: AWS CLI SETUP
  └─► T-I(-1).1: Update AWS CLI

PHASE B: IAM USERS (can run in parallel)
  ├─► T-I(-1).2: Create fw-infra user
  ├─► T-I(-1).3: Create fw-deploy user
  └─► T-I(-1).4: Create fw-ci user

PHASE C: IAM POLICIES
  └─► T-I(-1).5: Create policies (fw-infra-policy, fw-deploy-policy, fw-ci-policy)

PHASE D: ATTACH & KEYS
  ├─► T-I(-1).6: Attach policies to users
  └─► T-I(-1).7: Generate access keys

PHASE E: LOCAL CONFIGURATION
  ├─► T-I(-1).8: Configure AWS CLI profiles
  └─► T-I(-1).9: Validate AWS access

PHASE F: EKS CLUSTER
  ├─► T-I(-1).10: Provision EKS cluster
  └─► T-I(-1).11: Configure kubectl

═══════════════════════════════════════════════════════════════
```

---

## Phase A: AWS CLI Setup

### T-I(-1).1: Update AWS CLI to Latest Version

**Priority:** CRITICAL | **Status:** ⬜ Pending

#### Pre-Check
```bash
# Check current version
aws --version
```

**Expected:** `aws-cli/2.x.x` or higher

#### Actions

**macOS (Homebrew):**
```bash
brew upgrade awscli
```

**macOS (Installer):**
```bash
curl "https://awscli.amazonaws.com/AWSCLIV2.pkg" -o "AWSCLIV2.pkg"
sudo installer -pkg AWSCLIV2.pkg -target /
rm AWSCLIV2.pkg
```

**Linux:**
```bash
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install --update
rm -rf aws awscliv2.zip
```

#### Verification
```bash
aws --version
# Expected: aws-cli/2.15.x Python/3.x.x Darwin/... or similar
```

#### Completion Criteria
- [ ] AWS CLI version is 2.x or higher
- [ ] `aws --version` runs without error

---

## Phase B: Create IAM Users

> **Note:** These tasks can run in parallel. Use your existing admin credentials temporarily.

### T-I(-1).2: Create IAM User `fw-infra`

**Priority:** CRITICAL | **Status:** ⬜ Pending

#### Purpose
Infrastructure provisioning user for:
- VPC creation and management
- EKS cluster provisioning
- S3 bucket creation
- IAM role management (for IRSA)

#### Action
```bash
aws iam create-user --user-name fw-infra

# Add tags for identification
aws iam tag-user --user-name fw-infra --tags \
  Key=Project,Value=ForgeWorks \
  Key=Purpose,Value=InfraProvisioning \
  Key=CreatedBy,Value=Manual
```

#### Verification
```bash
aws iam get-user --user-name fw-infra
```

#### Completion Criteria
- [ ] User `fw-infra` exists in IAM
- [ ] Tags applied

---

### T-I(-1).3: Create IAM User `fw-deploy`

**Priority:** CRITICAL | **Status:** ⬜ Pending

#### Purpose
Day-to-day deployment user for:
- Deploying workloads to EKS
- Reading/writing to S3 buckets
- Pulling images from ECR

#### Action
```bash
aws iam create-user --user-name fw-deploy

aws iam tag-user --user-name fw-deploy --tags \
  Key=Project,Value=ForgeWorks \
  Key=Purpose,Value=Deployment \
  Key=CreatedBy,Value=Manual
```

#### Verification
```bash
aws iam get-user --user-name fw-deploy
```

#### Completion Criteria
- [ ] User `fw-deploy` exists in IAM
- [ ] Tags applied

---

### T-I(-1).4: Create IAM User `fw-ci`

**Priority:** HIGH | **Status:** ⬜ Pending

#### Purpose
CI/CD automation user for:
- GitHub Actions deployments
- ECR image push/pull
- S3 artifact storage

#### Action
```bash
aws iam create-user --user-name fw-ci

aws iam tag-user --user-name fw-ci --tags \
  Key=Project,Value=ForgeWorks \
  Key=Purpose,Value=CICD \
  Key=CreatedBy,Value=Manual
```

#### Verification
```bash
aws iam get-user --user-name fw-ci
```

#### Completion Criteria
- [ ] User `fw-ci` exists in IAM
- [ ] Tags applied

---

### Phase B Verification

```bash
# List all ForgeWorks users
aws iam list-users --query 'Users[?starts_with(UserName, `fw-`)].UserName' --output table
```

**Expected Output:**
```
-----------------
|   UserName    |
+---------------+
|  fw-ci        |
|  fw-deploy    |
|  fw-infra     |
+---------------+
```

---

## Phase C: Create IAM Policies

### T-I(-1).5: Create IAM Policies with Least-Privilege

**Priority:** CRITICAL | **Status:** ⬜ Pending

#### Step 1: Create Policy Directory

```bash
mkdir -p ~/git/repos/forge-works/infra/iam/policies
cd ~/git/repos/forge-works/infra/iam/policies
```

#### Step 2: Create Policy Files

**File: `fw-infra-policy.json`**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "EKSFullAccess",
      "Effect": "Allow",
      "Action": ["eks:*"],
      "Resource": "*"
    },
    {
      "Sid": "VPCManagement",
      "Effect": "Allow",
      "Action": [
        "ec2:CreateVpc", "ec2:DeleteVpc", "ec2:DescribeVpcs",
        "ec2:CreateSubnet", "ec2:DeleteSubnet", "ec2:DescribeSubnets",
        "ec2:CreateSecurityGroup", "ec2:DeleteSecurityGroup", "ec2:DescribeSecurityGroups",
        "ec2:AuthorizeSecurityGroupIngress", "ec2:AuthorizeSecurityGroupEgress",
        "ec2:RevokeSecurityGroupIngress", "ec2:RevokeSecurityGroupEgress",
        "ec2:CreateInternetGateway", "ec2:DeleteInternetGateway",
        "ec2:AttachInternetGateway", "ec2:DetachInternetGateway", "ec2:DescribeInternetGateways",
        "ec2:CreateNatGateway", "ec2:DeleteNatGateway", "ec2:DescribeNatGateways",
        "ec2:AllocateAddress", "ec2:ReleaseAddress", "ec2:DescribeAddresses",
        "ec2:CreateRouteTable", "ec2:DeleteRouteTable", "ec2:DescribeRouteTables",
        "ec2:CreateRoute", "ec2:DeleteRoute",
        "ec2:AssociateRouteTable", "ec2:DisassociateRouteTable",
        "ec2:CreateTags", "ec2:DescribeTags", "ec2:DescribeAvailabilityZones"
      ],
      "Resource": "*"
    },
    {
      "Sid": "IAMForEKS",
      "Effect": "Allow",
      "Action": [
        "iam:CreateRole", "iam:DeleteRole", "iam:GetRole", "iam:PassRole",
        "iam:AttachRolePolicy", "iam:DetachRolePolicy",
        "iam:CreatePolicy", "iam:DeletePolicy", "iam:GetPolicy",
        "iam:CreateOpenIDConnectProvider", "iam:DeleteOpenIDConnectProvider",
        "iam:GetOpenIDConnectProvider", "iam:TagOpenIDConnectProvider",
        "iam:ListAttachedRolePolicies", "iam:ListRolePolicies"
      ],
      "Resource": "*"
    },
    {
      "Sid": "S3BucketManagement",
      "Effect": "Allow",
      "Action": [
        "s3:CreateBucket", "s3:DeleteBucket", "s3:ListBucket",
        "s3:GetBucketLocation", "s3:PutBucketPolicy", "s3:GetBucketPolicy",
        "s3:PutBucketVersioning", "s3:GetBucketVersioning",
        "s3:PutEncryptionConfiguration", "s3:GetEncryptionConfiguration",
        "s3:PutBucketTagging", "s3:GetBucketTagging"
      ],
      "Resource": "arn:aws:s3:::fw-*"
    },
    {
      "Sid": "CloudFormationForEKS",
      "Effect": "Allow",
      "Action": ["cloudformation:*"],
      "Resource": "*"
    },
    {
      "Sid": "AutoScalingForEKS",
      "Effect": "Allow",
      "Action": ["autoscaling:*"],
      "Resource": "*"
    },
    {
      "Sid": "LogsAccess",
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup", "logs:DeleteLogGroup",
        "logs:DescribeLogGroups", "logs:PutRetentionPolicy"
      ],
      "Resource": "*"
    }
  ]
}
```

**File: `fw-deploy-policy.json`**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "EKSReadAndConnect",
      "Effect": "Allow",
      "Action": [
        "eks:DescribeCluster",
        "eks:ListClusters",
        "eks:AccessKubernetesApi"
      ],
      "Resource": "*"
    },
    {
      "Sid": "S3ReadWrite",
      "Effect": "Allow",
      "Action": [
        "s3:GetObject", "s3:PutObject", "s3:DeleteObject", "s3:ListBucket"
      ],
      "Resource": ["arn:aws:s3:::fw-*", "arn:aws:s3:::fw-*/*"]
    },
    {
      "Sid": "ECRPull",
      "Effect": "Allow",
      "Action": [
        "ecr:GetDownloadUrlForLayer", "ecr:BatchGetImage",
        "ecr:BatchCheckLayerAvailability", "ecr:GetAuthorizationToken"
      ],
      "Resource": "*"
    }
  ]
}
```

**File: `fw-ci-policy.json`**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "EKSConnect",
      "Effect": "Allow",
      "Action": ["eks:DescribeCluster", "eks:ListClusters"],
      "Resource": "*"
    },
    {
      "Sid": "ECRPushPull",
      "Effect": "Allow",
      "Action": [
        "ecr:GetDownloadUrlForLayer", "ecr:BatchGetImage",
        "ecr:BatchCheckLayerAvailability", "ecr:GetAuthorizationToken",
        "ecr:InitiateLayerUpload", "ecr:UploadLayerPart",
        "ecr:CompleteLayerUpload", "ecr:PutImage"
      ],
      "Resource": "*"
    },
    {
      "Sid": "S3Artifacts",
      "Effect": "Allow",
      "Action": ["s3:GetObject", "s3:PutObject", "s3:ListBucket"],
      "Resource": ["arn:aws:s3:::fw-*", "arn:aws:s3:::fw-*/*"]
    }
  ]
}
```

#### Step 3: Create Policies in AWS

```bash
# Create fw-infra-policy
aws iam create-policy \
  --policy-name fw-infra-policy \
  --policy-document file://fw-infra-policy.json \
  --description "ForgeWorks infrastructure provisioning policy"

# Create fw-deploy-policy
aws iam create-policy \
  --policy-name fw-deploy-policy \
  --policy-document file://fw-deploy-policy.json \
  --description "ForgeWorks deployment policy"

# Create fw-ci-policy
aws iam create-policy \
  --policy-name fw-ci-policy \
  --policy-document file://fw-ci-policy.json \
  --description "ForgeWorks CI/CD policy"
```

#### Verification
```bash
aws iam list-policies --scope Local --query 'Policies[?starts_with(PolicyName, `fw-`)].PolicyName' --output table
```

#### Completion Criteria
- [ ] fw-infra-policy created
- [ ] fw-deploy-policy created
- [ ] fw-ci-policy created
- [ ] Policy JSON files committed to repo

---

## Phase D: Attach Policies & Generate Keys

### T-I(-1).6: Attach Policies to IAM Users

**Priority:** CRITICAL | **Status:** ⬜ Pending

#### Get Account ID
```bash
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo "Account ID: $ACCOUNT_ID"
```

#### Attach Policies
```bash
# Attach to fw-infra
aws iam attach-user-policy \
  --user-name fw-infra \
  --policy-arn arn:aws:iam::${ACCOUNT_ID}:policy/fw-infra-policy

# Attach to fw-deploy
aws iam attach-user-policy \
  --user-name fw-deploy \
  --policy-arn arn:aws:iam::${ACCOUNT_ID}:policy/fw-deploy-policy

# Attach to fw-ci
aws iam attach-user-policy \
  --user-name fw-ci \
  --policy-arn arn:aws:iam::${ACCOUNT_ID}:policy/fw-ci-policy
```

#### Verification
```bash
aws iam list-attached-user-policies --user-name fw-infra
aws iam list-attached-user-policies --user-name fw-deploy
aws iam list-attached-user-policies --user-name fw-ci
```

#### Completion Criteria
- [ ] fw-infra has fw-infra-policy attached
- [ ] fw-deploy has fw-deploy-policy attached
- [ ] fw-ci has fw-ci-policy attached

---

### T-I(-1).7: Generate Access Keys for IAM Users

**Priority:** CRITICAL | **Status:** ⬜ Pending

> **SECURITY WARNING:** Save these keys securely. They will only be shown once!

#### Generate Keys
```bash
# fw-infra
echo "=== fw-infra Access Key ==="
aws iam create-access-key --user-name fw-infra

# fw-deploy
echo "=== fw-deploy Access Key ==="
aws iam create-access-key --user-name fw-deploy

# fw-ci
echo "=== fw-ci Access Key ==="
aws iam create-access-key --user-name fw-ci
```

#### Save Keys Securely

**Option A: 1Password / LastPass**
Store each set of credentials with labels:
- `AWS - fw-infra`
- `AWS - fw-deploy`
- `AWS - fw-ci`

**Option B: Encrypted File**
```bash
# Save to encrypted file
cat > /tmp/fw-credentials.txt << 'EOF'
# ForgeWorks AWS Credentials
# Generated: $(date)
# DELETE AFTER CONFIGURING AWS CLI

[fw-infra]
AccessKeyId=AKIA...
SecretAccessKey=...

[fw-deploy]
AccessKeyId=AKIA...
SecretAccessKey=...

[fw-ci]
AccessKeyId=AKIA...
SecretAccessKey=...
EOF

# Encrypt with GPG (recommended)
gpg -c /tmp/fw-credentials.txt
# Creates: /tmp/fw-credentials.txt.gpg

# Delete plaintext
rm /tmp/fw-credentials.txt
```

#### Completion Criteria
- [ ] fw-infra access key generated and saved
- [ ] fw-deploy access key generated and saved
- [ ] fw-ci access key generated and saved
- [ ] Keys stored in secure location (NOT in git!)

---

## Phase E: Local Configuration

### T-I(-1).8: Configure AWS CLI Profiles

**Priority:** CRITICAL | **Status:** ⬜ Pending

#### Configure fw-infra Profile
```bash
aws configure --profile fw-infra

# Prompts:
# AWS Access Key ID [None]: <paste from step above>
# AWS Secret Access Key [None]: <paste from step above>
# Default region name [None]: us-east-1
# Default output format [None]: json
```

#### Configure fw-deploy Profile
```bash
aws configure --profile fw-deploy

# Same prompts, use fw-deploy credentials
```

#### Verify Configuration
```bash
# Check credentials file
cat ~/.aws/credentials

# Should show:
# [fw-infra]
# aws_access_key_id = AKIA...
# aws_secret_access_key = ...
#
# [fw-deploy]
# aws_access_key_id = AKIA...
# aws_secret_access_key = ...
```

#### Completion Criteria
- [ ] ~/.aws/credentials has fw-infra profile
- [ ] ~/.aws/credentials has fw-deploy profile
- [ ] Region set correctly

---

### T-I(-1).9: Validate AWS Access

**Priority:** CRITICAL | **Status:** ⬜ Pending

#### Validation Script

```bash
#!/bin/bash
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║         ForgeWorks AWS Access Validation                  ║"
echo "╚═══════════════════════════════════════════════════════════╝"

PASS=0
FAIL=0

check() {
  if eval "$2" &>/dev/null; then
    echo "✅ $1"
    ((PASS++))
  else
    echo "❌ $1"
    ((FAIL++))
  fi
}

echo ""
echo "=== fw-infra Profile ==="
check "Identity verified" "aws sts get-caller-identity --profile fw-infra"
check "Can list EKS clusters" "aws eks list-clusters --profile fw-infra"
check "Can describe VPCs" "aws ec2 describe-vpcs --profile fw-infra"

echo ""
echo "=== fw-deploy Profile ==="
check "Identity verified" "aws sts get-caller-identity --profile fw-deploy"
check "Can list EKS clusters" "aws eks list-clusters --profile fw-deploy"

echo ""
echo "══════════════════════════════════════════════════════════"
echo "Passed: $PASS | Failed: $FAIL"
echo "══════════════════════════════════════════════════════════"

if [ $FAIL -gt 0 ]; then
  echo "❌ Some checks failed. Review IAM policies."
  exit 1
else
  echo "✅ All checks passed! Ready for EKS provisioning."
fi
```

#### Run Validation
```bash
chmod +x validate-aws-access.sh
./validate-aws-access.sh
```

#### Completion Criteria
- [ ] fw-infra identity verified
- [ ] fw-infra can list EKS clusters
- [ ] fw-infra can describe VPCs
- [ ] fw-deploy identity verified
- [ ] fw-deploy can list EKS clusters

---

## Phase F: EKS Cluster

### T-I(-1).10: Provision EKS Cluster

**Priority:** CRITICAL | **Status:** ⬜ Pending

#### Pre-requisite: Install eksctl
```bash
# macOS
brew install eksctl

# Linux
curl --silent --location "https://github.com/weaveworks/eksctl/releases/latest/download/eksctl_$(uname -s)_amd64.tar.gz" | tar xz -C /tmp
sudo mv /tmp/eksctl /usr/local/bin

# Verify
eksctl version
```

#### Create EKS Cluster

```bash
# Use fw-infra profile
export AWS_PROFILE=fw-infra

# Create cluster (takes 15-20 minutes)
eksctl create cluster \
  --name forge-works-dev \
  --region us-east-1 \
  --version 1.29 \
  --nodegroup-name fw-workers \
  --node-type t3.large \
  --nodes 3 \
  --nodes-min 2 \
  --nodes-max 5 \
  --managed \
  --with-oidc \
  --tags "Project=ForgeWorks,Environment=dev"
```

#### Monitor Progress
```bash
# In another terminal
watch -n 10 'aws cloudformation describe-stacks --profile fw-infra --query "Stacks[?starts_with(StackName, \`eksctl-forge-works\`)].{Name:StackName,Status:StackStatus}" --output table'
```

#### Completion Criteria
- [ ] eksctl installed
- [ ] EKS cluster `forge-works-dev` created
- [ ] 3 nodes in Ready state
- [ ] OIDC provider configured

---

### T-I(-1).11: Configure kubectl for EKS

**Priority:** CRITICAL | **Status:** ⬜ Pending

#### Update kubeconfig

```bash
# Switch to fw-deploy for day-to-day operations
export AWS_PROFILE=fw-deploy

# Update kubeconfig
aws eks update-kubeconfig \
  --region us-east-1 \
  --name forge-works-dev \
  --alias fw-dev
```

#### Verify Connection

```bash
# Cluster info
kubectl cluster-info

# List nodes
kubectl get nodes -o wide

# Check permissions
kubectl auth can-i create deployments --all-namespaces
kubectl auth can-i create customresourcedefinitions
```

#### Expected Output
```
NAME                              STATUS   ROLES    AGE   VERSION
ip-192-168-xx-xx.ec2.internal    Ready    <none>   10m   v1.29.x
ip-192-168-xx-xx.ec2.internal    Ready    <none>   10m   v1.29.x
ip-192-168-xx-xx.ec2.internal    Ready    <none>   10m   v1.29.x
```

#### Completion Criteria
- [ ] kubeconfig updated with fw-dev context
- [ ] kubectl cluster-info shows cluster
- [ ] 3 nodes in Ready state
- [ ] Can create deployments
- [ ] Can create CRDs

---

## Final Checklist

```
AWS FOUNDATION COMPLETE CHECKLIST
═══════════════════════════════════════════════════════════════

PHASE A: AWS CLI
[  ] T-I(-1).1: AWS CLI version >= 2.x

PHASE B: IAM USERS
[  ] T-I(-1).2: fw-infra user created
[  ] T-I(-1).3: fw-deploy user created
[  ] T-I(-1).4: fw-ci user created

PHASE C: IAM POLICIES
[  ] T-I(-1).5a: fw-infra-policy created
[  ] T-I(-1).5b: fw-deploy-policy created
[  ] T-I(-1).5c: fw-ci-policy created

PHASE D: ATTACH & KEYS
[  ] T-I(-1).6a: fw-infra-policy → fw-infra
[  ] T-I(-1).6b: fw-deploy-policy → fw-deploy
[  ] T-I(-1).6c: fw-ci-policy → fw-ci
[  ] T-I(-1).7a: fw-infra access key saved
[  ] T-I(-1).7b: fw-deploy access key saved
[  ] T-I(-1).7c: fw-ci access key saved

PHASE E: LOCAL CONFIGURATION
[  ] T-I(-1).8a: AWS CLI profile fw-infra configured
[  ] T-I(-1).8b: AWS CLI profile fw-deploy configured
[  ] T-I(-1).9: AWS access validated

PHASE F: EKS CLUSTER
[  ] T-I(-1).10: EKS cluster forge-works-dev provisioned
[  ] T-I(-1).11a: kubectl configured
[  ] T-I(-1).11b: 3 nodes in Ready state

═══════════════════════════════════════════════════════════════

ALL COMPLETE? → Proceed to Sprint I-0 (Prerequisites & Configuration)
═══════════════════════════════════════════════════════════════
```

---

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| `AccessDenied` on create-user | Not using admin account | Use admin credentials for IAM setup |
| Policy creation fails | Malformed JSON | Validate JSON with `jq . < policy.json` |
| eksctl hangs | CloudFormation issue | Check AWS Console → CloudFormation |
| kubectl can't connect | Wrong kubeconfig | Run `aws eks update-kubeconfig` again |
| Nodes not Ready | Node group issue | Check EC2 Console → Auto Scaling Groups |

---

## Next Steps

After completing Sprint I-(-1):
1. Proceed to **Sprint I-0** in [ACTION_PLAN_INFRASTRUCTURE.md](ACTION_PLAN_INFRASTRUCTURE.md)
2. Run pre-flight check from [PREREQUISITES.md](PREREQUISITES.md)
3. Begin ForgeWorks deployment

---

*Checklist Version: 1.0.0*
*Created: 2025-01-26*
*For: ForgeWorks Infrastructure Deployment*
