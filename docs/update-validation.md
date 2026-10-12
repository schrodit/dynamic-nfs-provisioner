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
