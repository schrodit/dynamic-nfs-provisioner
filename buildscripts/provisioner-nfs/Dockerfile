# Copyright 2026 The OpenEBS Authors.
# Licensed under the Apache License, Version 2.0.
# Compatibility path for an already-built static Linux binary.
FROM alpine:3.24.2@sha256:294b683cb724975bec92580e1e685676bd4b50bda910ddb8c51d4cabeaec77e6
RUN apk add --no-cache ca-certificates procps-ng
ARG DBUILD_DATE
ARG DBUILD_REPO_URL=https://github.com/schrodit/dynamic-nfs-provisioner
ARG RELEASE_TAG=ci
ARG GIT_COMMIT=unknown
LABEL org.opencontainers.image.title="provisioner-nfs" \
      org.opencontainers.image.created=$DBUILD_DATE \
      org.opencontainers.image.source=$DBUILD_REPO_URL \
      org.opencontainers.image.version=$RELEASE_TAG \
      org.opencontainers.image.revision=$GIT_COMMIT
COPY provisioner-nfs /usr/local/bin/provisioner-nfs
ENTRYPOINT ["/usr/local/bin/provisioner-nfs"]
