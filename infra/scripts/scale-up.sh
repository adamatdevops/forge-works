#!/bin/zsh

# Scale up nodes to 3

set -xe

aws eks update-nodegroup-config \
  --cluster-name forge-works-dev \
  --nodegroup-name fw-workers \
  --scaling-config minSize=0,maxSize=5,desiredSize=3 \
  --profile fw-infra \
  --region us-east-1

# Check scaling status
# aws eks describe-nodegroup \
#   --cluster-name forge-works-dev \
#   --nodegroup-name fw-workers \
