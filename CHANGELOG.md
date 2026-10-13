0.12.0-rc.1 / Prepared 2026-10-13 — unpublished
================================================

* Update Go to 1.27.2, public Kubernetes clients to 0.37.1, and external-provisioner to 13.1.0. Remove Maya, Kubernetes monorepo dependencies, and legacy staging/protobuf overrides. Patch reachable Go vulnerabilities.
* Preserve provisioner identity, configuration precedence, resource names, export behavior, and legacy finalizer defaults. Use namespace-scoped Lease leader election.
* Pin Alpine 3.24.2 and the Go builder; produce static binaries for four architectures. Remove third-party glibc. Kernel image runtime qualification remains pending.
* Remove PodSecurityPolicy. **Migration:** `rbac.pspEnabled=true` and `nfsProvisioner.privileged=false` are rejected; configure privileged admission for kernel server namespaces. Harden the controller and reduce RBAC. Newly generated server pods disable API-token automounting.
* Fix Helm GC=false omission and preserve UID/GID zero values. Add schema validation and immutable image digest overrides. Review intended GC behavior before upgrading an old chart that omitted false.
* Migrate to Ginkgo v2 and current Python/Ansible tooling. Add fresh-install, cross-node persistence, upgrade, rollback, GC, reclamation, and I/O recovery gates for Kubernetes 1.35–1.37 on amd64/arm64.
* Fix namespace handling and failure propagation in the server updater; add preview, explicit context, full-image rollback, and bounded waits.
* Prepare fork-specific candidate references under `ghcr.io/schrodit`. Publishing is disabled; candidate images are not claimed to exist. arm/v7 and ppc64le are build targets without runtime qualification. See [validation](docs/update-validation.md) and [migration](docs/tutorial/upgrade.md).

0.11.0 / 2023-12-08
========================
* add support for specifying mountOptions to default StorageClass ([#164](https://github.com/openebs/dynamic-nfs-provisioner/pull/164),[@pentago](https://github.com/farcaller) [@dsharma-dc](https://github.com/dsharma-dc))
* update documentation on backend storage prerequisite ([#165](https://github.com/openebs/dynamic-nfs-provisioner/pull/165),[@matthew-williams](https://github.com/matthew-williams) [@dsharma-dc](https://github.com/dsharma-dc))
* update google analytics to use GA4 ([#174](https://github.com/openebs/dynamic-nfs-provisioner/pull/174),[@Abhinandan-Purkait](https://github.com/Abhinandan-Purkait))
* add a toggle to allow/disallow garbage collection for the backend PVC ([#167](https://github.com/openebs/dynamic-nfs-provisioner/pull/167),[@njuptlzf](https://github.com/njuptlzf))

0.10.0 / 2023-02-09
========================
* add original PVC context to the nfs server deployment labels ([#151](https://github.com/openebs/dynamic-nfs-provisioner/pull/151),[@farcaller](https://github.com/farcaller))
* fix config generation logic -- prefer SC config over PVC config ([@niladrih](https://github.com/niladrih))

0.9.0 / 2022-01-03
========================
* support for changing shared filesystem ownership and mode ([#125](https://github.com/openebs/dynamic-nfs-provisioner/pull/125),[@niladrih](https://github.com/niladrih))

0.8.0 / 2021-11-09
========================
* send install analytic event for nfs-provisioner ([#109](https://github.com/openebs/dynamic-nfs-provisioner/pull/109),[@mynktl](https://github.com/mynktl))
* support to configure *ImagePullSecret* for nfs-server pods ([#114](https://github.com/openebs/dynamic-nfs-provisioner/pull/114),[@g-linville](https://github.com/g-linville))
* hooks support for nfs-provisioner, to add custom annotations/finalizers on nfs resources ([#93](https://github.com/openebs/dynamic-nfs-provisioner/pull/93),[@mynktl](https://github.com/mynktl))


0.7.1 / 2021-09-16
========================
* added installation analytic event for nfs-provisioner ([#110](https://github.com/openebs/dynamic-nfs-provisioner/pull/110),[@mynktl](https://github.com/mynktl))


0.7.0 / 2021-09-14
========================
* support to configure resource request and limit for NFS server resources ([#92](https://github.com/openebs/dynamic-nfs-provisioner/pull/92),[@mittachaitu](https://github.com/mittachaitu))
* added GHCR repository for docker images [provisioner-nfs](https://github.com/openebs/dynamic-nfs-provisioner/pkgs/container/provisioner-nfs) and [nfs-server-alpine](https://github.com/openebs/dynamic-nfs-provisioner/pkgs/container/nfs-server-alpine) ([#101](https://github.com/openebs/dynamic-nfs-provisioner/pull/101),[@niladrih](https://github.com/niladrih))


0.6.1 / 2021-08-30
========================
* support to configure resource request and limit for NFS server resources ([#92](https://github.com/openebs/dynamic-nfs-provisioner/pull/92),[@mittachaitu](https://github.com/mittachaitu))


0.6.0 / 2021-08-16
========================
* added garbage-collector to remove stale NFS resources ([#80](https://github.com/openebs/dynamic-nfs-provisioner/pull/80),[@mynktl](https://github.com/mynktl))
* support to configure timeout for Backed PVC binding ([#84](https://github.com/openebs/dynamic-nfs-provisioner/pull/84),[@mynktl](https://github.com/mynktl))


0.5.0 / 2021-07-16
========================
* adding metrics for nfs-provisioner ([#51](https://github.com/openebs/dynamic-nfs-provisioner/pull/51),[@mynktl](https://github.com/mynktl))
* support to access nfs-share volume by non-root application ([#52](https://github.com/openebs/dynamic-nfs-provisioner/pull/52),[@mittachaitu](https://github.com/mittachaitu))
* support to provision nfs resources in user provided namespace ([#58](https://github.com/openebs/dynamic-nfs-provisioner/pull/58),[@mynktl](https://github.com/mynktl))
* support to specify node affinity rules of NFS Server ([#59](https://github.com/openebs/dynamic-nfs-provisioner/pull/59),[@mittachaitu](https://github.com/mittachaitu))
