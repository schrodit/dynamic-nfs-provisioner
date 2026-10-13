# Repository update plan

Prepared: 2026-10-12. Status: all six implementation phases prepared; local validation recorded in update-validation.md. Linux image/cluster qualification remains pending. No release is published.

Bring the provisioner onto supported dependencies, images, and Kubernetes versions while preserving existing volume data and configuration behavior. Deliver the work as six reviewable changes, with validation attached to each change.

## Proposed targets

| Component | Current baseline | Proposed target |
| --- | --- | --- |
| Go | Module 1.19; builder/CI 1.19.13 | Go 1.27.2, used consistently in local tooling, CI, and Docker builds |
| Kubernetes clusters | CI tests only 1.27.3 | Latest patch releases of 1.35, 1.36, and 1.37 |
| Kubernetes Go modules | Replacement rules force 0.20.2; Kubernetes internals at 1.17.3 | Aligned 0.37.1 modules, required by external-provisioner 13.1.0; older cluster compatibility remains a runtime test gate |
| External provisioner library | v7.0.1 | v13.1.0, with Lease leader election and legacy finalizer behavior retained |
| Production image bases | Alpine 3.12 and 3.14 | Alpine 3.24.x, with pinned image digests |
| Integration tests | Ginkgo v1 and an older Ansible/Python stack | Ginkgo v2 and an updated Go integration suite |

These are selected update targets, not verified application compatibility claims. Exact versions and local evidence are recorded in update-validation.md; recheck patch releases before future publication. Go, Kubernetes, and Alpine targets follow their official [release history](https://go.dev/doc/devel/release), [supported Kubernetes releases](https://kubernetes.io/releases/), and [Alpine support table](https://alpinelinux.org/releases/).

Keep the `openebs.io/nfsrwx` provisioner identity, existing annotation keys, resource labels/names, hook behavior, and Delete/Retain semantics compatible. Native volume expansion and a CSI redesign are separate workstreams.

## 1. Establish the baseline and upgrade fixtures

- [x] Capture resolved dependency versions, unit-test results, image build results, and vulnerability reports. Separate existing failures from update regressions.
- [x] Explicitly configure Go in every CI job that builds or tests Go. Record any temporary baseline toolchain separately from the supported release target.
- [ ] Create disposable upgrade fixtures using release 0.11.0: Delete and Retain volumes, garbage collection enabled/disabled, a custom NFS namespace, and files with known content and ownership.
- [ ] Record the current Helm values, generated resources, image references, and PV/PVC state for those fixtures.
- [x] Inventory Ansible E2E scenarios and identify any coverage missing from the Go suite before replacing the old test stack.

Primary files: `.github/workflows/build.yml`, `.github/workflows/pull_request.yml`, `buildscripts/test.sh`, `tests/`, `e2e-tests/`.

Completion criteria: baseline results and repeatable fixtures exist; missing dependencies or unavailable cluster access are explicitly recorded. Baseline compilation, unit tests, module resolution, and vulnerability reachability were captured; live fixture execution remains pending.

## 2. Update Go dependencies and the controller

- [x] Replace the internal `k8s.io/kubernetes/pkg/apis/core/v1/helper` dependency with public APIs or a small local selector conversion. Preserve node-selector matching semantics with behavioral tests.
- [x] Inventory Maya imports and replace legacy environment, logging, version, configuration parsing, and API helpers incrementally. Preserve serialized configuration formats and annotation precedence. Remove Maya once those contracts have local replacements or maintained dependencies.
- [x] Update the Go module/toolchain baseline and select the external-provisioner/Kubernetes dependencies as a compatible set. Update major-version import paths and adjust changed controller APIs.
- [x] Remove the blanket Kubernetes staging replacements and the obsolete client-go declaration after their causes have been removed. Regenerate `go.mod` and `go.sum`; do not update indirect dependencies individually without a reason.
- [x] Remove the protobuf 1.25.0 replacement. Select a current compatible release and review `x/net`, `x/crypto`, gRPC, Prometheus, Cobra, YAML, and analytics dependencies with vulnerability scans.
- [x] Review changes to leader-election lock types, finalizers, provisioning retries, and deletion behavior. Include any required lease RBAC with the controller change so it can be deployed independently.

Primary files: `go.mod`, `go.sum`, `provisioner/`, `pkg/kubernetes/`, `cmd/provisioner-nfs/`, `buildscripts/build.sh`, deployment RBAC.

Completion criteria: module resolution and verification succeed without forced legacy versions; the binary builds on Go 1.27.2; unit tests and vet pass; meaningful concurrency tests pass with the race detector. Run `govulncheck` and triage findings by reachability. Protobuf versions before 1.33.0 are affected by [GO-2024-2611](https://pkg.go.dev/vuln/GO-2024-2611); that fixed version is a minimum for this advisory, not the final update target.

## 3. Update production images and build tooling

- [x] Update both provisioner Dockerfiles and the NFS server base to supported releases; pin their base-image digests.
- [x] Consolidate the two provisioner build paths around the same binary and runtime requirements. Validate a static Go build and remove the third-party glibc installation if it is unnecessary.
- [ ] Retain commands required by current health probes, or update probes together with runtime packages. Verify startup, metrics, certificate trust, shutdown, and image metadata.
- [x] Update Buildx/QEMU and remove the obsolete Buildx 0.5.1 pin. Fix builder detection in `Makefile.buildx.mk`, which currently compares the empty output of `grep -q` with `1`.
- [ ] Validate NFS utilities, export options, recovery directories, signal handling, grace/lease settings, ownership changes, and mount behavior against the newer image and host kernel.
- [ ] Build all currently advertised architectures. Require runtime smoke tests on amd64 and arm64; explicitly document whether arm/v7 and ppc64le remain supported.

Primary files: `buildscripts/provisioner-nfs/*Dockerfile`, `nfs-server-container/`, `Makefile.buildx.mk`, image workflows.

Completion criteria: provisioner and NFS server images build and run; clients can read/write over NFS and reconnect after a server restart without data loss; image scan results are reviewed. Produce candidate images without changing existing server Deployments.

## 4. Update Helm, manifests, and security configuration

- [x] Remove PodSecurityPolicy templates and their RBAC. Define explicit migration behavior for the old `rbac.pspEnabled` value so users receive a useful message. PSP has been removed since Kubernetes 1.25; changing its API version cannot restore it. See the [migration guide](https://kubernetes.io/docs/reference/using-api/deprecation-guide/#podsecuritypolicy).
- [x] Document Pod Security Admission requirements for the namespace receiving generated NFS server pods, including a custom server namespace. Keep controller security requirements separate from kernel NFS server requirements.
- [x] Replace the misleading privilege toggle with an accurate, documented contract. Generated NFS containers currently hard-code `privileged: true`; offer an unprivileged mode only if it actually works and is tested with kernel NFS.
- [x] Reduce wildcard RBAC to verified resource groups and verbs, including provisioning, hooks, garbage collection, and leader election. Keep Helm and raw manifests consistent.
- [x] Add values validation for important configuration, align controller/server image defaults, and use immutable candidate/release references instead of mutable `:ci` examples.
- [x] Preserve NFS export and ownership behavior during this update. Evaluate restrictions on permitted clients and root access separately, with migration guidance for existing workloads.

Primary files: `deploy/helm/charts/`, `deploy/kubectl/openebs-nfs-provisioner.yaml`, `provisioner/helper_kernel_nfs_server.go`.

Completion criteria: Helm lint and representative values renders pass; server-side validation and fresh installation pass across the proposed Kubernetes matrix; provisioning succeeds with reduced RBAC and documented admission settings.

## 5. Modernize CI and integration tests

- [x] Upgrade maintained GitHub Actions and pin reviewed revisions. Replace `::set-output` with `$GITHUB_OUTPUT`; remove floating `@latest` action references.
- [x] Update Helm, cluster tooling, Python used by chart-testing, and the OpenEBS LocalPV test fixture. Use kubectl versions compatible with the test clusters.
- [x] Migrate the Go integration suite and installed CLI together to Ginkgo v2; update flags and dependency versions consistently.
- [x] Make the Go suite the primary integration runner. Port any unique Ansible scenarios before retiring `e2e-tests/Dockerfile`, the Python 2-era dependencies, and unused image publishing jobs. If external consumers need that runner, migrate it to Python 3 and supported libraries instead.
- [ ] Test fresh installation on latest patch releases of Kubernetes 1.35, 1.36, and 1.37. Ensure code and chart changes both exercise deployment compatibility.
- [x] Add dependency/image vulnerability checks and a dependency-update mechanism with reviewable changes.

Primary files: `.github/workflows/`, `Makefile`, `buildscripts/test.sh`, `tests/install-localpv.sh`, `tests/`, `e2e-tests/`, `ct.yml`.

Completion criteria: CI runs unit, chart, image, and integration checks using explicit tool versions. Existing coverage passes for RWX persistence across nodes, multiple servers, Delete/Retain, garbage collection, file ownership, custom namespaces/images, hooks, resource limits, node affinity, and delayed binding.

## 6. Verify upgrades and prepare the release

- [x] Fix `docs/tutorial/upgrade-nfs-server.sh`: its existing-image lookup hard-codes namespace `openebs` despite accepting `-n`. Add argument validation, bounded rollout waits, and a preview mode. Custom-namespace selection and batch safety are regression-tested with mocked kubectl; live verification remains below.
- [ ] Upgrade the controller against the baseline fixtures and verify that existing server Deployments and backend volumes retain their identities and data. Inspect finalizer and garbage-collector behavior explicitly.
- [ ] Upgrade one NFS server image separately, measure the I/O interruption, and validate client reconnection and file contents before updating further servers.
- [ ] Test rollback with both the controller and server images. Inspect whether the new controller changes finalizers or persistent metadata that an old controller cannot safely handle; document any rollback boundary.
- [x] Update README compatibility claims, development prerequisites, install instructions, upgrade instructions, and release process. Verify publication URLs and registries for this fork.
- [x] Prepare a versioned chart, image references, changelog, and release candidate. Publish a supported range only after its tests pass.

Primary files: `docs/tutorial/upgrade-nfs-server.sh`, `docs/tutorial/upgrade.md`, `README.md`, `develop/developer.md`, `tests/README.md`, `RELEASE.md`, `CHANGELOG.md`, chart metadata, release workflows.

Completion criteria: fresh installs, upgrades from 0.11.0, and documented rollback paths pass; retained data survives; server restart downtime is recorded; candidate artifacts and release notes agree. Release validation must not delete retained PVs or backend PVCs to recover from a failure.

## Implementation order and release gates

Changes 1 through 6 have dedicated Conventional Commits. Checked items record completed source work or local validation; unchecked items require live cluster/image execution. Fixture and CI implementations for those unchecked gates are included. Publishing is disabled pending a separate release request.

The source changes followed phases 1 through 6. The next step is running the included image, fresh-install, and upgrade workflows on disposable Linux runners. Resolve any failures before declaring the support range or requesting publication.

The release is ready when:

- [x] The supported toolchain builds verified dependencies, unit tests/vet pass, and module files are reproducible.
- [ ] Candidate images run on advertised architectures and have reviewed vulnerability reports, with fixes applied where available and unresolved findings documented.
- [ ] Fresh installs and the full provisioning lifecycle pass on every advertised Kubernetes version.
- [ ] Upgrade tests preserve existing data, Retain semantics, configuration, and resource identities.
- [ ] Controller and server rollback behavior, downtime, deprecated values, and support limits are documented.

Defer CSI/native expansion, NFS server high availability, and changes to default export/ownership semantics until this maintenance release has a stable baseline.
