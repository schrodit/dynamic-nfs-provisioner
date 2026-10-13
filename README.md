# Dynamic NFS Volume Provisioner

[![Build](https://github.com/schrodit/dynamic-nfs-provisioner/actions/workflows/build.yml/badge.svg)](https://github.com/schrodit/dynamic-nfs-provisioner/actions/workflows/build.yml)

This fork updates the OpenEBS Dynamic NFS PV provisioner. It creates a kernel NFS server and a backend PVC for each shared volume, so pods on different Linux nodes can use ReadWriteMany storage. The provisioner identity remains `openebs.io/nfsrwx`.

Version **0.12.0-rc.1 is prepared in source and has not been published**. Candidate chart and manifest defaults point to intended `ghcr.io/schrodit` images. Build and load local images or override both image references before installing. The [validation record](docs/update-validation.md) distinguishes passing local checks from pending runtime gates.

## Compatibility targets

| Candidate | Kubernetes targets | Architecture targets | Qualification |
| --- | --- | --- | --- |
| 0.12.0-rc.1 | 1.35.9, 1.36.5, 1.37.1 | Linux amd64 and arm64 | Runtime validation pending |
| 0.12.0-rc.1 | Same cluster targets | arm/v7 and ppc64le | Static cross-build verified; image builds and runtime unqualified |

Older upstream versions and their historical compatibility claims are recorded in [CHANGELOG.md](CHANGELOG.md). They do not establish this candidate's support range. Native expansion, NFS server high availability, and a CSI conversion are outside this maintenance update.

## Install and operate

Start with the [quickstart](docs/intro.md), [chart values](deploy/helm/charts/README.md), and [security requirements](docs/security.md). Linux nodes need NFS client utilities; server nodes need kernel NFS support and an admission policy permitting privileged server pods.

Use the [upgrade guide](docs/tutorial/upgrade.md) to update the controller and server images separately. Existing servers keep their images during controller upgrades. Server restarts interrupt client I/O; qualify reconnection and rollback in a disposable cluster before updating application volumes.

Other guides cover [WordPress](docs/workload/wordpress.md), [volume resizing](docs/tutorial/nfs-volume-resize.md), [node affinity](docs/tutorial/node-affinity.md), and [hooks](docs/tutorial/nfs-hook.md). See [development](develop/developer.md), [release preparation](RELEASE.md), and the [six-phase update plan](docs/update-plan.md).

This project is licensed under [Apache 2.0](LICENSE). Contributions follow [CONTRIBUTING.md](CONTRIBUTING.md) and the [Code of Conduct](CODE_OF_CONDUCT.md). NFS server image inspiration: [sjiveson/nfs-server-alpine](https://github.com/sjiveson/nfs-server-alpine).
