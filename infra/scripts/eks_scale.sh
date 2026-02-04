#!/bin/zsh

# To scale down nodes to 0
aws eks update-nodegroup-config \
  --cluster-name forge-works-dev \
  --nodegroup-name fw-workers \
  --scaling-config minSize=0,maxSize=5,desiredSize=0 \
  --profile fw-infra \
    --region us-east-1

# To scale up nodes to 3
aws eks update-nodegroup-config \
  --cluster-name forge-works-dev \
  --nodegroup-name fw-workers \
  --scaling-config minSize=0,maxSize=5,desiredSize=3 \
  --profile fw-infra \
  --region us-east-1

# Check scaling status (takes 2-5 minutes)
aws eks describe-nodegroup \
  --cluster-name forge-works-dev \
  --nodegroup-name fw-workers \
  --profile fw-infra \
  --region us-east-1 \
  --query 'nodegroup.{Status:status,DesiredSize:scalingConfig.desiredSize,CurrentSize:scalingConfig.desiredSize}'


# Update kubeconfig to use [example_profile] (cluster creator)
aws eks update-kubeconfig \
  --region us-east-1 \
  --name forge-works-dev \
  --profile fw-infra \
  --alias fw-dev

# Test once nodes are ready
kubectl get nodes -o wide


# Step 1: Create IAM OIDC Provider (if not exists)
eksctl utils associate-iam-oidc-provider \
  --region us-east-1 \
  --cluster forge-works-dev \
  --approve \
  --profile fw-infra

# Step 2: Create IAM Role for EBS CSI Driver
eksctl create iamserviceaccount \
  --name ebs-csi-controller-sa \
  --namespace kube-system \
  --cluster forge-works-dev \
  --role-name AmazonEKS_EBS_CSI_DriverRole \
  --role-only \
  --attach-policy-arn arn:aws:iam::aws:policy/service-role/AmazonEBSCSIDriverPolicy \
  --approve \
  --profile fw-infra \
  --region us-east-1


# Step 3: Install EBS CSI Driver Add-on
eksctl create addon \
  --name aws-ebs-csi-driver \
  --cluster forge-works-dev \
  --service-account-role-arn arn:aws:iam::525320085763:role/AmazonEKS_EBS_CSI_DriverRole \
  --force \
  --profile fw-infra \
  --region us-east-1

# Step 4: Create gp3 StorageClass
kubectl apply -f - <<EOF
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: gp3
  annotations:
    storageclass.kubernetes.io/is-default-class: "true"
provisioner: ebs.csi.aws.com
parameters:
  type: gp3
  encrypted: "true"
reclaimPolicy: Delete
volumeBindingMode: WaitForFirstConsumer
allowVolumeExpansion: true
EOF

---

# T-I0.5: Container Registry

# Per our TECH_STACK.md decision: GHCR (ghcr.io/forge-works)

# Verify cluster can pull public images:
kubectl run test-pull --rm -it --restart=Never \
  --image=ghcr.io/containerbase/base:latest \
  -- echo "GHCR pull works!"
