# Release preparation

The current source candidate is **0.12.0-rc.1**. It has not been published. Workflows have read-only repository permissions: branch pushes run checks, and manual candidate workflows validate or upload CI artifacts. There are no image pushes, Git tags, GitHub releases, or Helm repository publications in these workflows.

## Candidate artifacts

Keep chart `version`, `appVersion`, raw manifest image tags, and `CHANGELOG.md` aligned. Run:

```sh
python3 hack/prepare-release.py artifacts
```

The output contains the chart package, raw and rendered manifests, changelog, provenance manifest, and SHA256SUMS. The tool refuses to overwrite a nonempty output directory. Intended image references are `ghcr.io/schrodit/provisioner-nfs:VERSION` and `ghcr.io/schrodit/nfs-server-alpine:VERSION`; they are not claimed to exist. The GitHub source is this fork, and no OpenEBS registry credentials are assumed.

Packaging does not create images or establish compatibility. The manifest records the source commit and whether the checkout contains uncommitted changes. Repackage from the clean final commit before distributing a candidate.

## Qualification gates

Run `Validate release candidate` manually on the exact candidate commit when hosted CI is available. It runs the shared checks before attaching candidate files as a CI artifact. Preserve the following evidence:

- Reproducible modules, unit/chart/script tests, vet, targeted race tests, and reachable Go vulnerability results.
- Both image builds for amd64, arm64, arm/v7, and ppc64le, plus image scan results. arm/v7 and ppc64le remain build targets without a runtime support claim.
- Fresh installs and the full Go suite on Kubernetes 1.35.9, 1.36.5, and 1.37.1, on native amd64 and arm64 runners.
- Upgrade from immutable chart 0.11.0, GC enabled/disabled, custom server namespace, resource/finalizer preservation, cross-node RWX data and ownership, client restarts, controller rollback, and server upgrade/rollback.
- Recorded server rollout durations and successful client I/O gaps. Delete cleanup and Retain data must survive the documented reclamation/GC checks without manually deleting retained resources.

Pending or failed runtime gates keep the candidate unqualified. Local evidence and limitations are in [docs/update-validation.md](docs/update-validation.md). Image scan failures require remediation or an explicitly reviewed exception before a release; they must not be silently ignored.

## Future publication

Publication is disabled for now. A later, separately authorized release task must enable a publisher for this fork, verify GHCR package ownership and access, push both versioned images, record their digests, and distribute the matching chart package. Verify that published artifacts resolve before updating installation examples or claiming a supported range. Do not publish mutable `latest` tags for a release candidate.

Use `v0.12.0-rc.1` for the candidate Git tag only when publishing is authorized. Promotion to a stable version requires a new matching source version and qualification evidence for that version. Consult [upgrade and rollback](docs/tutorial/upgrade.md) for migration boundaries; controller and server rollback are separate operations.
