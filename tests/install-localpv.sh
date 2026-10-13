#!/usr/bin/env bash
# Copyright 2026 The OpenEBS Authors.
# Licensed under the Apache License, Version 2.0.
set -euo pipefail
# This fixture is for a disposable integration cluster.
helm upgrade --install openebs-localpv localpv-provisioner \
  --repo https://openebs.github.io/dynamic-localpv-provisioner \
  --version 4.6.0 --namespace openebs --create-namespace \
  --set localpv.basePath=/tmp/openebs --set hostpathClass.basePath=/tmp/openebs \
  --set analytics.enabled=false --wait --timeout=5m
kubectl get storageclass openebs-hostpath
