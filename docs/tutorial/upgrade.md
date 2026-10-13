# Upgrade and rollback

The 0.12.0-rc.1 candidate is unpublished and runtime qualification is pending. Use a disposable cluster to run [the upgrade fixtures](../../tests/upgrade/README.md) before upgrading application storage. Packaging or passing unit tests alone does not establish upgrade safety.

## Controller upgrade

Save `helm get values RELEASE -n CONTROLLER_NAMESPACE -o yaml`, `helm history`, and the PV/PVC/backend/server resource identities and image references. Back up volume data through your existing backup procedure. Keep the provisioner identity `openebs.io/nfsrwx`, existing StorageClass names, and server namespace unchanged.

Review saved values: remove `rbac.pspEnabled=true` and use Pod Security Admission; `nfsProvisioner.privileged=false` is rejected because kernel servers require privileges. Prepare the server namespace, including a custom namespace, according to [security.md](../security.md). External RBAC must permit Lease leader election. The controller gets new security defaults while existing servers keep their pod settings and images.

Build/load candidate images or supply qualified image references. Preview the rendered chart with your values, then upgrade using the new defaults plus your previous explicit settings:

```sh
helm upgrade RELEASE ./deploy/helm/charts --kube-context CONTEXT \
  -n CONTROLLER_NAMESPACE --reset-then-reuse-values \
  --set nfsProvisioner.image.repository=YOUR_CONTROLLER_REPOSITORY \
  --set nfsProvisioner.image.tag=YOUR_CANDIDATE_TAG \
  --set nfsProvisioner.nfsServerAlpineImage.repository=YOUR_SERVER_REPOSITORY \
  --set nfsProvisioner.nfsServerAlpineImage.tag=YOUR_CANDIDATE_TAG \
  --wait --timeout=5m
```

For immutable references, set the corresponding `image.digest` fields; a digest takes precedence over a tag. Preserve any image registry prefix settings as well. [Helm's value merge behavior](https://docs.helm.sh/docs/helm/helm_upgrade/) is why this guide uses `--reset-then-reuse-values` rather than carrying all old chart defaults into the upgrade.

The chart now passes GC=false explicitly; chart 0.11.0 omitted it and the controller used GC=true. Check the actual environment before upgrading installations that set false. The update retains legacy finalizer behavior with `AddFinalizer(false)` and does not intentionally rewrite existing persistent metadata. Compare identities, finalizers, bindings, endpoints, policies, and data after the upgrade. These properties still require runtime qualification.

Raw-manifest installations should apply the local manifest with available, reviewed image references. Do not run a Helm-managed controller alongside a separate raw controller watching the same claims.

## Server image upgrade

Upgrade one server separately. Record its full old reference, monitor application reads/writes, and allow for NFS grace time, image pull time, and client recovery. The script requires Bash, Python 3, and kubectl. It targets the named `nfs-server` container, preserves registry ports when changing tags, and waits for each rollout before the next server.

```sh
# Preview one deployment in its actual server namespace:
bash docs/tutorial/upgrade-nfs-server.sh -c CONTEXT -n SERVER_NAMESPACE \
  -d SERVER_DEPLOYMENT --dry-run --image YOUR_SERVER_REPOSITORY@sha256:YOUR_DIGEST
# Apply the same reviewed change by removing --dry-run.
```

A positional tag changes the current repository's tag. `--image` sets a complete reference, including a digest. Omit `-d` only after qualifying one server; the script then updates labelled servers sequentially. Rollout timeout defaults to five minutes and can be changed with `-t 10m`. Failed patches or rollouts stop the batch with a nonzero exit status. A failed rollout leaves that deployment at the attempted image so its state can be inspected or rolled back explicitly.

## Rollback boundary

Use `helm rollback RELEASE PREVIOUS_REVISION --kube-context CONTEXT -n CONTROLLER_NAMESPACE --wait --timeout=5m` to restore the controller. If the old chart omitted GC=false, explicitly restore the intended environment afterward and wait for rollout. Avoid running old and new controllers simultaneously while testing Lease migration.

Restore a server using the same updater with `--image ORIGINAL_FULL_REFERENCE`, its actual namespace, and one deployment. Controller rollback does not roll back server images. Validate client reconnection, checksums, ownership, Retain state, and finalizers after both rollbacks. Changes made independently by hooks, operators, or administrators require their own rollback procedure.

Do not delete retained PVs, backend PVCs, or server deployments to recover from an upgrade failure. Rollback to 0.11.0 is a test target, not a verified production guarantee until the cluster gate passes. The gate records rollout duration and the largest interval between successful client I/O samples at one-second resolution; this is an observed recovery measure, not a precise outage guarantee.
