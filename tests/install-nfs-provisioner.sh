#!/usr/bin/env bash
# Copyright 2026 The OpenEBS Authors.
# Licensed under the Apache License, Version 2.0.
set -euo pipefail
cd "$(dirname "$0")/.."
kubectl label namespace openebs pod-security.kubernetes.io/enforce=privileged --overwrite
helm upgrade --install openebs-nfs ./deploy/helm/charts --namespace openebs \
  --set fullnameOverride=openebs-nfs-provisioner \
  --set nfsStorageClass.name=openebs-rwx \
  --set nfsStorageClass.backendStorageClass=openebs-hostpath \
  --set nfsProvisioner.image.tag=ci --set nfsProvisioner.nfsServerAlpineImage.tag=ci \
  --set analytics.enabled=false --wait --timeout=5m
kubectl get storageclass openebs-rwx
