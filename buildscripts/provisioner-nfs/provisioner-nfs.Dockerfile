# Copyright 2026 The OpenEBS Authors.
# Licensed under the Apache License, Version 2.0.
FROM --platform=$BUILDPLATFORM golang:1.27.2-alpine3.24@sha256:f92b6ef800e499660581efdabdf25d9d817a9d124eaf900924f0504e7e27e12d AS build
ARG TARGETOS
ARG TARGETARCH
ARG TARGETVARIANT
ARG NFSSERVERIMG
ARG RELEASE_TAG=ci
ARG GIT_COMMIT=unknown
ENV CGO_ENABLED=0 GOTOOLCHAIN=local
WORKDIR /src
RUN apk add --no-cache bash git
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN XC_OS="$TARGETOS" XC_ARCH="$TARGETARCH" GOARM="${TARGETVARIANT#v}" \
    RELEASE_TAG="$RELEASE_TAG" GIT_COMMIT="$GIT_COMMIT" NFSSERVERIMG="$NFSSERVERIMG" \
    PNAME=provisioner-nfs CTLNAME=provisioner-nfs bash buildscripts/build.sh

FROM alpine:3.24.2@sha256:294b683cb724975bec92580e1e685676bd4b50bda910ddb8c51d4cabeaec77e6
RUN apk add --no-cache ca-certificates procps-ng
ARG DBUILD_DATE
ARG DBUILD_REPO_URL=https://github.com/schrodit/dynamic-nfs-provisioner
ARG DBUILD_SITE_URL=https://github.com/schrodit/dynamic-nfs-provisioner
ARG RELEASE_TAG=ci
ARG GIT_COMMIT=unknown
LABEL org.opencontainers.image.title="provisioner-nfs" \
      org.opencontainers.image.description="Dynamic NFS PV provisioner" \
      org.opencontainers.image.created=$DBUILD_DATE \
      org.opencontainers.image.source=$DBUILD_REPO_URL \
      org.opencontainers.image.url=$DBUILD_SITE_URL \
      org.opencontainers.image.version=$RELEASE_TAG \
      org.opencontainers.image.revision=$GIT_COMMIT
COPY --from=build /src/bin/provisioner-nfs/provisioner-nfs /usr/local/bin/provisioner-nfs
ENTRYPOINT ["/usr/local/bin/provisioner-nfs"]
