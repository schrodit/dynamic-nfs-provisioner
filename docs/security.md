# Controller and NFS server security

The controller runs as UID/GID 10001, drops Linux capabilities, disables privilege escalation, uses a read-only root filesystem, and sets the RuntimeDefault seccomp profile. Configure its settings through `podSecurityContext` and `nfsProvisioner.securityContext`.

Kernel NFS server pods require privileged containers and a Linux host kernel with NFS server support. Their shared filesystem and recovery state must remain writable. They do not need Kubernetes API credentials; newly created server pods disable service-account token automounting.

When using Pod Security Admission, prepare the namespace receiving server pods before provisioning. For a dedicated namespace, an administrator can run:

```sh
kubectl create namespace nfs-servers
kubectl label namespace nfs-servers pod-security.kubernetes.io/enforce=privileged --overwrite
helm upgrade --install nfs ./deploy/helm/charts -n openebs --create-namespace \
  --set nfsProvisioner.nfsServerNamespace=nfs-servers
```

An administrator-managed admission exemption is another option. If servers share the controller namespace, that namespace must permit privileged server pods too. The chart does not change namespace admission labels automatically.

PodSecurityPolicy resources have been removed. `rbac.pspEnabled=true` now fails with migration guidance. The old `nfsProvisioner.privileged` setting never controlled generated server privileges; `false` now fails rather than implying an unprivileged NFS server mode. Controller privileges are configured independently.

Controller RBAC is limited to node and StorageClass reads, namespace reads used by analytics, PV/PVC/Service and Deployment lifecycle operations, events, and Lease leader election. It no longer grants access to secrets, node proxy, pod exec, CRDs, or unrelated workloads. External RBAC installations must include `coordination.k8s.io/leases` access in the controller namespace.

Image references support an optional digest at `nfsProvisioner.image.digest` and `nfsProvisioner.nfsServerAlpineImage.digest`. A digest overrides the corresponding tag. Existing servers keep their configured image until explicitly upgraded.

The maintenance update preserves NFS export and file-ownership behavior. Use `PERMITTED` or a custom export configuration when restricting clients. Changes to root squashing or ownership semantics require a separate workload migration.
