#!/bin/zsh

set -xe

aws eks update-nodegroup-config \
  --cluster-name forge-works-dev \
  --nodegroup-name fw-workers \
  --scaling-config minSize=0,maxSize=5,desiredSize=0 \
  --profile fw-infra \
  --region us-east-1

