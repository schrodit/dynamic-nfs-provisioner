#!/usr/bin/env bash
# Copyright 2026 The OpenEBS Authors.
# Licensed under the Apache License, Version 2.0.
set -euo pipefail
cd "$(dirname "$0")/.."
# One invocation produces a valid coverage profile and propagates package failures.
go test -mod=readonly -coverprofile=coverage.txt -covermode=atomic ./cmd/... ./pkg/... ./provisioner/... ./tests/chart
