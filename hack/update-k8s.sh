#!/usr/bin/env bash

#Copyright 2020 The OpenEBS Authors
#
#Licensed under the Apache License, Version 2.0 (the "License");
#you may not use this file except in compliance with the License.
#You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
#Unless required by applicable law or agreed to in writing, software
#distributed under the License is distributed on an "AS IS" BASIS,
#WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#See the License for the specific language governing permissions and
#limitations under the License.
#

# Align public Kubernetes clients; the Kubernetes monorepo is not a Go dependency.
set -euo pipefail
version=${1:-}
version=${version#v}
if [[ ! $version =~ ^1\.[0-9]+\.[0-9]+$ ]]; then
  echo "Usage: bash hack/update-k8s.sh 1.MINOR.PATCH" >&2
  exit 1
fi
module_version="v0.${version#1.}"
go get "k8s.io/api@${module_version}" "k8s.io/apimachinery@${module_version}" "k8s.io/client-go@${module_version}"
go mod tidy
