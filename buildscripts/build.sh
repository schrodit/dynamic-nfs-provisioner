#!/usr/bin/env bash
# Copyright 2026 The OpenEBS Authors.
# Licensed under the Apache License, Version 2.0.
set -euo pipefail
cd "$(dirname "$0")/.."
name=${PNAME:-provisioner-nfs}
command_name=${CTLNAME:-provisioner-nfs}
# Respect explicit cross-compilation targets instead of overriding them with uname.
export CGO_ENABLED=0
export GOOS=${XC_OS:-$(go env GOOS)}
export GOARCH=${XC_ARCH:-$(go env GOARCH)}
version=${RELEASE_TAG:-ci}
version=${version#v}
commit=${GIT_COMMIT:-$(git rev-parse HEAD 2>/dev/null || printf unknown)}
server_image=${NFSSERVERIMG:-openebs/nfs-server-alpine:${version}}
destination="bin/${name}/${GOOS}_${GOARCH}/${command_name}"
mkdir -p "$(dirname "$destination")"
go build -mod=readonly -trimpath -tags "${GO_BUILD_TAGS:-}" -ldflags \
  "-s -w -X github.com/openebs/dynamic-nfs-provisioner/provisioner.NFSServerDefaultImage=${server_image} -X github.com/openebs/dynamic-nfs-provisioner/pkg/version.Version=${version} -X github.com/openebs/dynamic-nfs-provisioner/pkg/version.GitCommit=${commit}" \
  -o "$destination" "./cmd/${command_name}"
cp "$destination" "bin/${name}/${command_name}"
printf 'Built %s for %s/%s (%s)\n' "$destination" "$GOOS" "$GOARCH" "$version"
