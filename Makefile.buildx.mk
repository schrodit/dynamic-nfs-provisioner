# Copyright 2020 The OpenEBS Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# default list of platforms for which multiarch image is built
ifeq (${PLATFORMS}, )
	export PLATFORMS="linux/amd64,linux/arm64,linux/arm/v7,linux/ppc64le"
endif

# Cache by default; pushing requires IMG_RESULT=push.
IMG_RESULT ?= cache
ifeq (${IMG_RESULT}, load)
	export PUSH_ARG="--load"
	# if load is specified, image will be built only for the build machine architecture.
	export PLATFORMS="linux/$(shell go env GOARCH)"
else ifeq (${IMG_RESULT}, cache)
	# if cache is specified, image will only be available in the build cache, it won't be pushed or loaded
	# therefore no PUSH_ARG will be specified
else
	export PUSH_ARG="--push"
endif

.PHONY: buildx-builder
buildx-builder:
	@docker buildx inspect container-builder >/dev/null 2>&1 || docker buildx create --name container-builder --driver docker-container

.PHONY: docker.buildx.provisioner-nfs
docker.buildx.provisioner-nfs: buildx-builder
	@docker buildx build --builder container-builder --platform ${PLATFORMS} \
		-t "$(PROVISIONER_NFS_IMAGE_TAG)" ${DBUILD_ARGS} -f $(PWD)/buildscripts/$(PROVISIONER_NFS)/$(PROVISIONER_NFS).Dockerfile \
		. ${PUSH_ARG}
	@echo "--> Build docker image: $(PROVISIONER_NFS_IMAGE_TAG)"
	@echo

.PHONY: buildx.push.provisioner-nfs
buildx.push.provisioner-nfs:
	BUILDX=true DIMAGE=${IMAGE_ORG}/provisioner-nfs ./buildscripts/push.sh

.PHONY: docker.buildx.nfs-server
docker.buildx.nfs-server: buildx-builder
	@cd nfs-server-container && \
		docker buildx build --builder container-builder --platform ${PLATFORMS} -t "$(NFS_SERVER_IMAGE_TAG)" ${DBUILD_ARGS} . ${PUSH_ARG}
	@echo "--> Build docker image: $(NFS_SERVER_IMAGE_TAG)"
	@echo

.PHONY: buildx.push.nfs-server
buildx.push.nfs-server:
	BUILDX=true DIMAGE=${IMAGE_ORG}/nfs-server-alpine ./buildscripts/push.sh
