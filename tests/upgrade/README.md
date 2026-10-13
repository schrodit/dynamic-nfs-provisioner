# Upgrade fixtures

Use a disposable Linux Kubernetes cluster with NFS client utilities on its nodes and a working backend StorageClass. The harness requires an explicit context and never switches the global kubectl context.

```sh
python3 tests/upgrade/fixtures.py seed --context DISPOSABLE_CONTEXT --gc true
python3 tests/upgrade/fixtures.py verify --context DISPOSABLE_CONTEXT
```

The seed requires full Git history and Python 3.12+. It installs chart 0.11.0 from immutable revision `077394ced96d0368e9e3e412d03d0c881bb64e2f` because the old Helm repository now returns 404. It provisions Delete and Retain volumes in `nfs-upgrade`, and places their servers in `nfs-upgrade-servers`. It records PV/PVC/server identities, image references, NFS endpoints, Helm values, content checksums, and ownership. Two clients share each volume with a preference for different nodes.

After upgrading the controller or a server image, rerun `verify` against the original state file. Repeat with `--gc false` in a fresh disposable cluster. Preserve the state file between checks; `snapshot` intentionally replaces it. No automatic cleanup deletes retained storage.

Legacy Ansible coverage is mapped as follows:

| Scenario | Replacement |
| --- | --- |
| Operator install from chart/master/release | Helm fresh-install and release upgrade workflows |
| Busybox provisioning and RWX writes | `tests/sanity_test.go`, multiple-server tests, upgrade fixtures |
| Checksum after application pod restart | Upgrade fixtures plus restart verification in the release gate |
| Deprovision application and storage | Reclaim-policy, backend-Retain, garbage-collector tests |
| E2E result CR reporting | CI logs and test artifacts; no runtime dependency on an E2E CRD |

Runtime verification is required before claiming these replacements cover the legacy runner.
