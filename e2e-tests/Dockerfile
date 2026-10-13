# Copyright 2026 The OpenEBS Authors.
# Licensed under the Apache License, Version 2.0.
# Compatibility runner; the Go integration suite is the primary CI runner.
FROM python:3.14-slim-trixie@sha256:a2b82f3c48559aa0a8446d9af49826b6e2b2016f4cd2afabfe6013ec53729170
ARG KUBECTL_VERSION=v1.37.1
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates curl netcat-openbsd iproute2 jq sshpass bc git openssh-client \
    && rm -rf /var/lib/apt/lists/*
COPY e2e-tests/requirements.txt e2e-tests/collections.yml /tmp/
RUN pip install --no-cache-dir -r /tmp/requirements.txt \
    && ansible-galaxy collection install -r /tmp/collections.yml
RUN curl --fail --location --silent --show-error \
      "https://dl.k8s.io/release/${KUBECTL_VERSION}/bin/linux/amd64/kubectl" -o /tmp/kubectl \
    && curl --fail --location --silent --show-error \
      "https://dl.k8s.io/release/${KUBECTL_VERSION}/bin/linux/amd64/kubectl.sha256" -o /tmp/kubectl.sha256 \
    && cd /tmp && echo "$(cat kubectl.sha256)  kubectl" | sha256sum --check \
    && install -m 0755 /tmp/kubectl /usr/local/bin/kubectl \
    && rm /tmp/kubectl /tmp/kubectl.sha256 \
    && mkdir -p /etc/ansible /ansible \
    && printf '[local]\n127.0.0.1 ansible_connection=local\n' > /etc/ansible/hosts \
    && touch /mnt/parameters.yml
COPY e2e-tests /e2e-tests
WORKDIR /
