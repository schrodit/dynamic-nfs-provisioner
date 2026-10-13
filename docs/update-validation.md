# Update validation

This records evidence for the six phases in update-plan.md. Local execution uses temporary Go caches rather than modifying the user's global Go environment.

## Phase 1: baseline and fixtures

- Baseline dependency resolution: passed; 662 modules in the full module graph, including Kubernetes staging overrides at 0.20.2.
- Baseline unit tests: passed with Go 1.27.1 on macOS arm64 (`go test ./cmd/... ./pkg/... ./provisioner/...`). The existing provisioner tests take about 87 seconds.
- Helm lint: passed with local Helm 4.2.4. Rendering with PSP enabled reproduces the removed policy/v1beta1 resource.
- Repeatable baseline capture: `bash hack/capture-baseline.sh /tmp/nfs-baseline`.
- Upgrade fixtures: added an explicit-context harness for chart 0.11.0, Delete/Retain, both garbage-collection modes, custom server namespace, two RWX clients, identity checks, checksums, and file ownership. Python command-line parsing and Bash syntax checks pass.
- Environment limitation: Docker is installed but its daemon is not running; no kubectl current context is configured. Image builds, NFS mounts, and live upgrade checks have not run locally. These are release gates, not passing results.
- Legacy Ansible scenario mapping is in tests/upgrade/README.md; replacement runtime coverage will be required before retirement.

## Phase 2: dependencies and controller

- Baseline binary build and module verification passed. The baseline vulnerability scan found 32 reachable vulnerabilities across four modules.
- Selected Go 1.27.2, Kubernetes modules 0.37.1, external-provisioner 13.1.0, analytics 0.6.0, Prometheus 1.24.1, protobuf 1.36.12, and patched x/net 0.61.0. The resolved module graph shrank from 662 to 155 modules.
- Removed Maya, Kubernetes monorepo imports, staging replacement rules, the protobuf downgrade, and the old client-go declaration. Local configuration parsing retains annotation keys, whole-record precedence, duplicate handling, file-permission data, and environment behavior.
- Lease RBAC and an explicit election namespace accompany the controller upgrade. `AddFinalizer(false)` preserves the previous default rather than introducing new finalizers during this maintenance update.
- Unit tests, integration-suite compilation without cluster execution, vet, module verification, and targeted race tests pass. New behavioral tests cover node selectors, annotation precedence, and concurrent request tracking. The binary reports its version without requiring Maya or Git at runtime.
- `govulncheck` against production packages reports no vulnerabilities after patching x/net. This is a Go reachability scan; image scanning remains pending.
- Kubernetes 1.35–1.37 runtime compatibility, Lease failover, data retention, and rollback remain cluster release gates.

## Phase 3: production images and builds

- Verified Docker Hub manifest digests for Alpine 3.24.2 and Go 1.27.2/alpine3.24. Both indexes include amd64, arm64, arm/v7, and ppc64le. Production Dockerfiles pin those digests.
- Verified the Alpine 3.24 package index contains Bash, certificates, procps-ng, NFS utilities, rpcbind, iproute2, coreutils, and Git. Kernel NFS runtime behavior still requires Linux execution.
- Cross-built the actual provisioner binary for Linux amd64, arm64, arm/v7, and ppc64le with Go 1.27.2. `file` confirms all four are static ELF executables. Third-party glibc is removed; builds no longer copy binaries to the user's global GOPATH.
- Docker builds now share the static build script, explicit target OS/architecture, version metadata, and ARM variant normalization. Buildx creation is a recipe prerequisite, not a Makefile parse-time side effect. Default buildx output is cache; registry publication requires `IMG_RESULT=push`.
- Bash syntax checks, Make dry runs for local/multi-architecture builds, and whitespace validation pass. Image builds, amd64/arm64 container smoke tests, image vulnerability scanning, NFS mount/reconnect behavior, and restart downtime measurements remain pending because Docker is not running locally.

## Phase 4: deployment and security

- Removed PSP resources and their RBAC. Deprecated PSP and unprivileged-server values now fail with migration guidance; controller security settings are independent.
- Helm and raw manifests use explicit API groups/resources/verbs without secrets, node proxy, pod exec, CRDs, or wildcard privileges. Kernel server pods remain privileged and newly generated pods disable API token automounting.
- Added values schema validation and optional controller/server image digests. Default controller security runs without root, drops capabilities, disables escalation, uses RuntimeDefault seccomp, and makes its root filesystem read-only.
- Fixed a discovered chart regression: GC=false previously omitted the environment variable, restoring the controller's true default. False is now passed explicitly; baseline fixtures patch the 0.11.0 Deployment to exercise the intended disabled case. File-permission UID/GID zero values also render explicitly.
- Helm lint, default/custom-value rendering, schema rejection cases, digest precedence, reduced RBAC checks, and controller/server security regression tests pass. Existing server creation tests also pass.
- Server-side validation, actual admission behavior, and provisioning under reduced RBAC remain Linux cluster release gates.

## Phase 5: CI and integration tooling

- Pinned maintained GitHub Actions to upstream release commit SHAs, selected Helm 4.3.0 and Minikube 1.39.0, and configured Kubernetes 1.35.9/1.36.5/1.37.1 on amd64 and arm64. Shared checks cover code and chart changes, native runtime smoke tests, all four image build architectures, Go vulnerability scans, and Trivy image scans. Dependabot tracks Go, actions, Docker, and Python dependencies.
- Migrated to Ginkgo 2.33.1 with a managed Go tool directive and ordered scenario containers. Registered kubeconfig flags before test flag parsing, bounded exec operations, removed deprecated GCP authentication, and made coverage generation a single valid profile.
- LocalPV setup uses its verified 4.6.0 chart. NFS setup uses the local Helm chart and loaded CI images without editing source manifests. Integration tests support both the Helm and raw controller container names.
- Preserved the external Ansible runner using a pinned Python 3.14 image, ansible-core 2.21.5, kubernetes.core 6.6.0, kubernetes client 37.0.1, and checksummed kubectl 1.37.1. Updated removed modules and failure propagation. Both entry playbooks pass syntax checks; legacy variable-name warnings and runtime coverage remain for Linux execution.
- Verified that the old NFS Helm repository returns 404. Upgrade fixtures now extract the immutable 0.11.0 chart revision from full Git history instead of depending on that URL.
- Unit tests with coverage, vet, chart regressions, license checks, workflow actionlint, YAML parsing, shell syntax checks, integration compilation, and a Ginkgo dry run registering 132 specs pass locally. The dry run performs no cluster validation. The production vulnerability scan still reports no findings.
- Remote CI has not been dispatched or observed. Linux cluster/image checks remain pending; the workflow configuration itself does not establish support or release readiness.
