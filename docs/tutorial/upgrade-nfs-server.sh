#!/bin/bash

# Copyright 2021 The OpenEBS Authors. All rights reserved.
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
#

set -euo pipefail

usage() {
    cat <<'HELP'
Usage: upgrade-nfs-server.sh [options] IMAGE_TAG
       upgrade-nfs-server.sh [options] --image REPOSITORY:TAG_OR_DIGEST
  -n NAMESPACE   Server namespace (default: openebs)
  -d DEPLOYMENT  Update one server; omit to update labelled servers sequentially
  -c CONTEXT     Explicit kubectl context (otherwise the current context)
  -t TIMEOUT     Rollout timeout (default: 5m)
  --dry-run      Show changes without patching or restarting servers
  --image IMAGE  Full image reference, also used to restore a previous image
  -h, --help     Show this help
HELP
}
fail() { printf 'ERROR: %s\n' "$*" >&2; exit 1; }
namespace=openebs
deployment=
context=
timeout=5m
image=
tag=
preview=false
while [ "$#" -gt 0 ]; do
    case "$1" in
        -h|--help) usage; exit 0 ;;
        --dry-run) preview=true; shift ;;
        -n|-d|-c|-t|--image)
            [ "$#" -ge 2 ] && [ -n "$2" ] || fail "Missing value for $1"
            case "$1" in
                -n) namespace=$2 ;; -d) deployment=$2 ;; -c) context=$2 ;;
                -t) timeout=$2 ;; --image) image=$2 ;;
            esac
            shift 2 ;;
        -*) fail "Unknown option: $1" ;;
        *) [ -z "$tag" ] || fail 'Only one image tag is allowed'; tag=$1; shift ;;
    esac
done
[ -n "$image" ] || [ -n "$tag" ] || fail 'An image tag or --image is required'
[ -z "$image" ] || [ -z "$tag" ] || fail 'Use either a tag or --image'
[[ "$namespace" =~ ^[a-z0-9]([-a-z0-9]*[a-z0-9])?$ ]] || fail 'Invalid namespace'
[[ -z "$deployment" || "$deployment" =~ ^[a-z0-9]([-a-z0-9.]*[a-z0-9])?$ ]] || fail 'Invalid deployment name'
[[ "$timeout" =~ ^[1-9][0-9]*[smh]$ ]] || fail 'Timeout must be a positive duration such as 5m'
[[ -z "$tag" || "$tag" =~ ^[a-zA-Z0-9_][a-zA-Z0-9_.-]{0,127}$ ]] || fail 'Invalid image tag'
[[ -z "$image" || "$image" =~ ^[a-zA-Z0-9][a-zA-Z0-9_./:@-]*$ ]] || fail 'Invalid image reference'
command -v python3 >/dev/null || fail 'python3 is required'
kube=(kubectl --request-timeout=30s)
if [ -n "$context" ]; then kube+=(--context "$context"); fi
if [ -n "$deployment" ]; then
    deployments=$deployment
else
    deployments=$("${kube[@]}" get deployment -n "$namespace" -l openebs.io/nfs-server \
        -o 'jsonpath={range .items[*]}{.metadata.name}{"\n"}{end}')
fi
[ -n "$deployments" ] || fail "No NFS server deployments found in $namespace"
while IFS= read -r name; do
    [ -n "$name" ] || continue
    object=$("${kube[@]}" get deployment -n "$namespace" "$name" -o json)
    existing=$(python3 - "$object" <<'PYTHON'
import json, sys
obj = json.loads(sys.argv[1])
if "openebs.io/nfs-server" not in obj["metadata"].get("labels", {}):
    sys.exit("Refusing to modify an unlabelled NFS deployment")
containers = [c for c in obj["spec"]["template"]["spec"]["containers"] if c["name"] == "nfs-server"]
if len(containers) != 1:
    sys.exit("Expected exactly one nfs-server container")
print(containers[0]["image"])
PYTHON
    )
    target=$image
    if [ -z "$target" ]; then
        repository=${existing%%@*}
        # Strip a tag only from the last path component, preserving registry ports.
        if [[ "${repository##*/}" == *:* ]]; then repository=${repository%:*}; fi
        target=$repository:$tag
    fi
    printf '%s/%s: %s -> %s\n' "$namespace" "$name" "$existing" "$target"
    if [ "$preview" = true ] || [ "$existing" = "$target" ]; then continue; fi
    patch=$(python3 - "$target" <<'PYTHON'
import json, sys
print(json.dumps({"spec": {"template": {"spec": {"containers": [
    {"name": "nfs-server", "image": sys.argv[1]}]}}}}))
PYTHON
    )
    "${kube[@]}" patch deployment -n "$namespace" "$name" --type=strategic -p "$patch"
    "${kube[@]}" rollout status -n "$namespace" "deployment/$name" \
        --timeout="$timeout" --request-timeout="$timeout"
done <<< "$deployments"
