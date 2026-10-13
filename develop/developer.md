# Development

Use Go **1.27.2** from `.go-version`, Helm, Python 3.12+, Git, and Docker with Buildx. Linux cluster tests additionally require kernel NFS support and NFS clients on every node. Toolchain and dependency versions are shared by CI and the Docker builder.

```sh
go mod download
go mod verify
make provisioner-nfs
make test
# Build local images; no registry push:
make provisioner-nfs-image nfs-server-image
# Build all four image architectures into the Buildx cache:
make docker.buildx.provisioner-nfs docker.buildx.nfs-server
python3 -m unittest discover -s tests/upgrade -p 'test_*.py'
```

Binaries are written under `bin/provisioner-nfs/`; builds do not change global GOPATH contents. Set `XC_OS`, `XC_ARCH`, `GOARM`, `RELEASE_TAG`, and `GIT_COMMIT` for cross-builds and version metadata. Make supplies the matching server image; direct builds can set `NFSSERVERIMG` explicitly.

Run `go mod tidy`, `go mod verify`, and `go vet ./cmd/... ./pkg/... ./provisioner/... ./tests/...` after dependency changes. Keep public Kubernetes modules aligned using `hack/update-k8s.sh`; do not restore staging replacement rules or Kubernetes monorepo imports. Run production `govulncheck` separately from image vulnerability scans.

Use [tests/README.md](../tests/README.md) for fresh installation and the Ginkgo suite, and [upgrade fixtures](../tests/upgrade/README.md) for upgrade/rollback qualification. Fixture commands require an explicit disposable context; never run reclaim scenarios against application storage. CI tests the exact cluster targets in [README.md](../README.md).

Prepare candidate files with `python3 hack/prepare-release.py artifacts`. Publishing is disabled in repository workflows. Keep meaningful Conventional Commits and follow [CONTRIBUTING.md](../CONTRIBUTING.md) when submitting changes to this fork.
