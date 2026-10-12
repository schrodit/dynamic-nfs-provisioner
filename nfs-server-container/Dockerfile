# Copyright 2020 The OpenEBS Authors.
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

FROM alpine:3.24.2@sha256:294b683cb724975bec92580e1e685676bd4b50bda910ddb8c51d4cabeaec77e6
#LABEL maintainer "Steven Iveson <steve@iveson.eu>"
#LABEL source "https://github.com/sjiveson/nfs-server-alpine"
#LABEL branch "master"
ARG RELEASE_TAG=ci
ARG GIT_COMMIT=unknown
LABEL org.opencontainers.image.title="nfs-server-alpine" \
      org.opencontainers.image.version=$RELEASE_TAG \
      org.opencontainers.image.revision=$GIT_COMMIT \
      org.opencontainers.image.source="https://github.com/schrodit/dynamic-nfs-provisioner"

RUN apk add --no-cache --update --verbose nfs-utils rpcbind bash iproute2 coreutils && \
    rm -rf /var/cache/apk /tmp /sbin/halt /sbin/poweroff /sbin/reboot && \
    mkdir -p /var/lib/nfs/rpc_pipefs /var/lib/nfs/v4recovery && \
    echo "rpc_pipefs    /var/lib/nfs/rpc_pipefs rpc_pipefs      defaults        0       0" >> /etc/fstab && \
    echo "nfsd  /proc/fs/nfsd   nfsd    defaults        0       0" >> /etc/fstab

COPY exports /etc/
COPY nfsd.sh /usr/bin/nfsd.sh
COPY .bashrc /root/.bashrc

RUN chmod +x /usr/bin/nfsd.sh

ENTRYPOINT ["/usr/bin/nfsd.sh"]
