# NFS provisioner chart

Chart and application version **0.12.0-rc.1** are prepared but unpublished. Default images point to intended GHCR repositories for this fork. Override both repositories/tags with available images for development. See the [quickstart](../../../docs/intro.md) and [security requirements](../../../docs/security.md).

```sh
helm lint ./deploy/helm/charts
helm template nfs ./deploy/helm/charts -n openebs
python3 hack/prepare-release.py artifacts
# Install the local chart or the resulting .tgz after supplying available images.
```

The chart installs the controller and an optional NFS StorageClass. Install the backend provisioner separately. Kernel servers are created dynamically per volume and need a namespace that permits privileged pods. The controller runs without root and does not need privileged admission when placed in a separate namespace.

| Value | Default / purpose |
| --- | --- |
| `nfsProvisioner.image.repository` | `ghcr.io/schrodit/provisioner-nfs` |
| `nfsProvisioner.nfsServerAlpineImage.repository` | `ghcr.io/schrodit/nfs-server-alpine` |
| Both image `.tag` fields | Chart appVersion when empty |
| Both image `.digest` fields | Empty; a digest overrides the tag |
| Both image `.registry` fields | Optional prefix ending in `/`; normally leave empty when repository includes registry |
| `nfsProvisioner.enableLeaderElection` | true; uses coordination Leases |
| `nfsProvisioner.enableGarbageCollection` | true; false is now passed explicitly |
| `nfsProvisioner.nfsServerNamespace` | Controller namespace unless specified |
| `podSecurityContext` | Controller UID/GID 10001, nonroot, RuntimeDefault seccomp |
| `nfsProvisioner.securityContext` | Controller drops capabilities, disables escalation, uses read-only root filesystem |
| `rbac.create`, `serviceAccount.create` | true; external RBAC needs Lease permissions |
| `rbac.pspEnabled` | false; true fails with migration guidance |
| `nfsProvisioner.privileged` | Deprecated, must be true; kernel servers require privilege |
| `nfsStorageClass.name` | `openebs-kernel-nfs` |
| `nfsStorageClass.backendStorageClass` | Empty; select your backend explicitly |
| `nfsStorageClass.reclaimPolicy` | Delete; configure Retain when needed |
| `nfsStorageClass.mountOptions` | Empty array |
| `nfsStorageClass.filePermissions` | Optional UID/GID/mode; zero is accepted |
| `analytics.enabled` | true; can be disabled |

Additional placement, resources, hook, lease/grace, and export settings are documented in [values.yaml](values.yaml). The schema rejects invalid flags, image references, and deprecated values. Existing generated servers keep their image until explicitly updated.

For upgrades, use the new chart defaults and previous explicit values as described in [the upgrade guide](../../../docs/tutorial/upgrade.md). The old standalone chart repository is unavailable; this fork uses local packages and does not maintain a published Helm repository yet.
