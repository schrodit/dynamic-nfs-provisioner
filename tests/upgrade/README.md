# Upgrade fixtures

Use a disposable Linux Kubernetes cluster with NFS client utilities on its nodes and a working backend StorageClass. The harness requires an explicit context and never switches the global kubectl context.

```sh
python3 tests/upgrade/fixtures.py seed --context DISPOSABLE_CONTEXT --gc true
python3 tests/upgrade/fixtures.py verify --context DISPOSABLE_CONTEXT
```

The seed requires full Git history and Python 3.12+. It installs chart 0.11.0 from immutable revision `077394ced96d0368e9e3e412d03d0c881bb64e2f` because the old Helm repository now returns 404. It provisions Delete and Retain volumes in `nfs-upgrade`, and places their servers in `nfs-upgrade-servers`. It records PV/PVC/server identities, image references, NFS endpoints, Helm values, content checksums, and ownership. Two clients share each volume on two distinct nodes (required pod anti-affinity).

The complete disposable-cluster sequence is:

```sh
# Keep --gc consistent with the seed and use a separate state file per cluster.
python3 tests/upgrade/fixtures.py upgrade-controller --context DISPOSABLE_CONTEXT
python3 tests/upgrade/fixtures.py restart-clients --context DISPOSABLE_CONTEXT
python3 tests/upgrade/fixtures.py rollback-controller --context DISPOSABLE_CONTEXT
python3 tests/upgrade/fixtures.py upgrade-controller --context DISPOSABLE_CONTEXT
python3 tests/upgrade/fixtures.py server-cycle --context DISPOSABLE_CONTEXT
python3 tests/upgrade/fixtures.py restart-clients --context DISPOSABLE_CONTEXT
python3 tests/upgrade/fixtures.py verify-reclaim --context DISPOSABLE_CONTEXT
python3 tests/upgrade/fixtures.py verify-gc --context DISPOSABLE_CONTEXT
```

`upgrade-controller` preserves explicit values while applying the new chart defaults and loaded CI images. `verify` checks existing server images, finalizers, bindings, resource identities, cross-node clients, data, and ownership. `server-cycle` upgrades and restores one Retain server, recording rollout durations and the largest successful read/write sample gap in a sibling `.io.json` file. The one-second sampling interval is not a precise outage measurement. Failed rollouts leave resources available for inspection; they do not trigger destructive cleanup.

`verify-reclaim` **deletes only the fixture application deployments and their PVCs**, then checks Delete cleanup and Retain data. `verify-gc` creates a labelled orphan fixture backend, restarts the controller to trigger initial GC, and verifies that the retained backend survives. These actions are intended exclusively for disposable clusters. They never delete the retained PV/backend/server to recover from an error.

The `.github/workflows/upgrade-checks.yml` matrix runs this sequence for all three cluster versions, both native architectures, and both GC modes. It uses a fresh cluster with only LocalPV installed; running two independent NFS controllers against the same claims would invalidate the test. After a manual controller or server image change, rerun `verify` against the original state file. Repeat every command with `--gc false` in a fresh disposable cluster. Preserve the state file between checks; `snapshot` intentionally replaces it. No automatic cleanup deletes retained storage.

Legacy Ansible coverage is mapped as follows:

| Scenario | Replacement |
| --- | --- |
| Operator install from chart/master/release | Helm fresh-install and release upgrade workflows |
| Busybox provisioning and RWX writes | `tests/sanity_test.go`, multiple-server tests, upgrade fixtures |
| Checksum after application pod restart | Upgrade fixtures plus restart verification in the release gate |
| Deprovision application and storage | Reclaim-policy, backend-Retain, garbage-collector tests |
| E2E result CR reporting | CI logs and test artifacts; no runtime dependency on an E2E CRD |

Runtime verification is required before claiming these replacements cover the legacy runner.
