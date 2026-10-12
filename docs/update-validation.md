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
