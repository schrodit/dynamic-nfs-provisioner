#!/usr/bin/env bash
# Copyright 2026 The OpenEBS Authors.
# Licensed under the Apache License, Version 2.0.
set -uo pipefail

output=${1:?Usage: capture-baseline.sh OUTPUT_DIRECTORY}
mkdir -p "$output"
output=$(cd "$output" && pwd)
cd "$(dirname "$0")/.."
failed=0
capture() {
  local name=$1
  shift
  if "$@" > "$output/$name.log" 2>&1; then
    printf '%s: passed\n' "$name"
  else
    printf '%s: failed (see %s/%s.log)\n' "$name" "$output" "$name"
    failed=1
  fi
}
capture toolchain go version
capture modules go list -m all
capture modules-verify go mod verify
capture unit-tests go test ./cmd/... ./pkg/... ./provisioner/...
capture build go build -o "$output/provisioner-nfs" ./cmd/provisioner-nfs
capture helm-lint helm lint deploy/helm/charts
capture helm-render helm template baseline deploy/helm/charts
if command -v govulncheck >/dev/null; then
  capture vulnerabilities govulncheck ./cmd/... ./pkg/... ./provisioner/...
else
  printf 'vulnerabilities: unavailable (install govulncheck)\n'
fi
if docker info >/dev/null 2>&1; then
  capture provisioner-image docker build -f buildscripts/provisioner-nfs/provisioner-nfs.Dockerfile .
  capture nfs-image docker build nfs-server-container
else
  printf 'image builds: unavailable (Docker daemon is not running)\n'
fi
exit "$failed"
