# Integration tests

The primary integration suite uses Ginkgo v2. Its CLI is managed by the Go `tool` directive, so `go tool ginkgo` uses the same version as the imported test library.

Use the Go release in `.go-version`, Helm 4, kubectl, and a disposable Linux Kubernetes cluster. Its nodes need NFS client utilities and kernel NFS server support. The test suite provisions and deletes test storage; use the dedicated fixtures rather than an application cluster.

```sh
export KUBECONFIG=/path/to/disposable-cluster/config
./tests/install-localpv.sh
./tests/install-nfs-provisioner.sh
make sanity-test
```

The setup scripts install LocalPV 4.6.0 and the local NFS chart, using the locally built `openebs/provisioner-nfs:ci` and `openebs/nfs-server-alpine:ci` images. Load both into every cluster node first. They configure the `openebs-hostpath` backend and `openebs-rwx` NFS StorageClasses without editing tracked manifests.

Run unit tests and chart regressions with `make test`; compile integration tests without using a cluster with `go test ./tests -run '^$'`. Use `go tool ginkgo --dry-run ./tests` to inspect the registered specs. Dry runs do not verify cluster behavior.

CI covers Kubernetes 1.35.9, 1.36.5, and 1.37.1 on amd64 and arm64. The dependent steps within each integration scenario use ordered Ginkgo containers. Exec calls and the overall suite have bounded timeouts.

Upgrade fixtures are documented in [upgrade/README.md](upgrade/README.md). For cloud clusters, use current kubeconfig exec authentication plugins; the removed legacy in-process GCP plugin is not used.
