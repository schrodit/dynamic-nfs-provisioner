#!/usr/bin/env python3
# Copyright 2026 The OpenEBS Authors.
# Licensed under the Apache License, Version 2.0.
"""Seed and verify disposable 0.11.0 upgrade fixtures using an explicit context."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

CONTENT = "dynamic-nfs-upgrade-fixture-v1\n"
POLICIES = ("Delete", "Retain")


class Fixtures:
    def __init__(self, args):
        self.args = args
        self.namespace = "nfs-upgrade"
        self.servers = "nfs-upgrade-servers"

    def kubectl(self, *args, data=None):
        return subprocess.check_output(
            ["kubectl", "--context", self.args.context, "--request-timeout=30s", *args],
            input=None if data is None else json.dumps(data).encode(),
        ).decode()

    def get(self, *args):
        return json.loads(self.kubectl("get", *args, "-o", "json"))

    def apply(self, obj):
        self.kubectl("apply", "-f", "-", data=obj)

    def pods(self, policy):
        return self.get("pods", "-n", self.namespace, "-l", f"fixture={policy.lower()}")["items"]

    def seed(self):
        for ns in (self.namespace, self.servers):
            self.apply({"apiVersion": "v1", "kind": "Namespace", "metadata": {
                "name": ns, "labels": {"pod-security.kubernetes.io/enforce": "privileged"}}})
        subprocess.run([
            "helm", "upgrade", "--install", "nfs-upgrade", "nfs-provisioner",
            "--repo", self.args.repo, "--version", "0.11.0",
            "--kube-context", self.args.context, "-n", self.namespace,
            "--set", "nfsStorageClass.enabled=false", "--set", "analytics.enabled=false",
            "--set", f"nfsProvisioner.enableGarbageCollection={self.args.gc}",
            "--set", f"nfsProvisioner.nfsServerNamespace={self.servers}",
            "--wait", "--timeout", "5m",
        ], check=True)
        deployment = self.get("deployments", "-n", self.namespace)["items"][0]
        # Chart 0.11.0 omits the GC variable when false; set it explicitly for this baseline case.
        self.kubectl("set", "env", "-n", self.namespace, "deployment/" + deployment["metadata"]["name"],
            "OPENEBS_IO_NFS_SERVER_GARBAGE_COLLECTION_ENABLED=" + self.args.gc)
        self.kubectl("rollout", "status", "-n", self.namespace,
            "deployment/" + deployment["metadata"]["name"], "--timeout=5m")
        self.apply({"apiVersion": "v1", "kind": "ServiceAccount", "metadata": {
            "name": deployment["spec"]["template"]["spec"]["serviceAccountName"],
            "namespace": self.servers}})
        for policy in POLICIES:
            name = "nfs-upgrade-" + policy.lower()
            self.apply({"apiVersion": "storage.k8s.io/v1", "kind": "StorageClass",
                "metadata": {"name": name, "annotations": {"cas.openebs.io/config":
                    f'- name: BackendStorageClass\n  value: "{self.args.backend}"\n'}},
                "provisioner": "openebs.io/nfsrwx", "reclaimPolicy": policy,
                "mountOptions": ["nfsvers=4.1"]})
            self.apply({"apiVersion": "v1", "kind": "PersistentVolumeClaim",
                "metadata": {"name": name, "namespace": self.namespace}, "spec": {
                    "storageClassName": name, "accessModes": ["ReadWriteMany"],
                    "resources": {"requests": {"storage": "1Gi"}}}})
            self.apply({"apiVersion": "apps/v1", "kind": "Deployment", "metadata": {
                "name": name, "namespace": self.namespace}, "spec": {"replicas": 2,
                "selector": {"matchLabels": {"fixture": policy.lower()}}, "template": {
                    "metadata": {"labels": {"fixture": policy.lower()}}, "spec": {
                        "affinity": {"podAntiAffinity": {"preferredDuringSchedulingIgnoredDuringExecution": [
                            {"weight": 100, "podAffinityTerm": {"topologyKey": "kubernetes.io/hostname",
                                "labelSelector": {"matchLabels": {"fixture": policy.lower()}}}}]}},
                        "containers": [{"name": "client", "image": "busybox:1.37.0", "command": ["sleep", "86400"],
                            "volumeMounts": [{"name": "data", "mountPath": "/data"}]}],
                        "volumes": [{"name": "data", "persistentVolumeClaim": {"claimName": name}}]}}}})
            self.kubectl("rollout", "status", "-n", self.namespace, "deployment/" + name, "--timeout=5m")
            pod = self.pods(policy)[0]["metadata"]["name"]
            self.kubectl("exec", "-n", self.namespace, pod, "--", "sh", "-c",
                "printf 'dynamic-nfs-upgrade-fixture-v1\\n' > /data/proof; "
                "chown 1234:2345 /data/proof && chmod 640 /data/proof && sync")
        self.snapshot()

    def snapshot(self):
        state = {"context": self.args.context, "gc": self.args.gc, "claims": {}}
        for policy in POLICIES:
            name = "nfs-upgrade-" + policy.lower()
            pvc = self.get("pvc", "-n", self.namespace, name)
            pv = self.get("pv", pvc["spec"]["volumeName"])
            server = self.get("deployment", "-n", self.servers, "nfs-" + pv["metadata"]["name"])
            backend = self.get("pvc", "-n", self.servers, "nfs-" + pv["metadata"]["name"])
            state["claims"][policy] = {"pvc": pvc, "pv": pv, "server": server, "backend": backend}
        state["helmValues"] = subprocess.check_output([
            "helm", "get", "values", "nfs-upgrade", "-n", self.namespace,
            "--kube-context", self.args.context, "-a", "-o", "json"]).decode()
        self.args.state.write_text(json.dumps(state, indent=2) + "\n")

    def verify(self):
        state = json.loads(self.args.state.read_text())
        if state["context"] != self.args.context:
            raise RuntimeError("Snapshot belongs to a different Kubernetes context")
        for policy, expected in state["claims"].items():
            pv_name = expected["pv"]["metadata"]["name"]
            for resource, namespace, original in (
                ("pvc", self.namespace, expected["pvc"]), ("pv", None, expected["pv"]),
                ("pvc", self.servers, expected["backend"]), ("deployment", self.servers, expected["server"]),
            ):
                args = [resource, original["metadata"]["name"]]
                if namespace:
                    args += ["-n", namespace]
                current = self.get(*args)
                if current["metadata"]["uid"] != original["metadata"]["uid"]:
                    raise RuntimeError(f"Resource replaced: {resource}/{original['metadata']['name']}")
            current_pv = self.get("pv", pv_name)
            if current_pv["spec"]["nfs"] != expected["pv"]["spec"]["nfs"]:
                raise RuntimeError(f"NFS endpoint changed for {pv_name}")
            if current_pv["spec"]["persistentVolumeReclaimPolicy"] != policy:
                raise RuntimeError(f"Reclaim policy changed for {pv_name}")
            pods = self.pods(policy)
            if len(pods) != 2:
                raise RuntimeError("Expected two RWX clients")
            for pod in pods:
                name = pod["metadata"]["name"]
                checksum = self.kubectl("exec", "-n", self.namespace, name, "--", "sha256sum", "/data/proof").split()[0]
                permissions = self.kubectl("exec", "-n", self.namespace, name, "--", "stat", "-c", "%u:%g:%a", "/data/proof").strip()
                if checksum != hashlib.sha256(CONTENT.encode()).hexdigest() or permissions != "1234:2345:640":
                    raise RuntimeError(f"Data or ownership changed on {name}")
        print("Upgrade fixtures preserve identities, endpoints, policies, content, and ownership")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("seed", "snapshot", "verify"))
    parser.add_argument("--context", required=True, help="Explicit disposable cluster context")
    parser.add_argument("--state", type=Path, default=Path("/tmp/nfs-upgrade-state.json"))
    parser.add_argument("--backend", default="openebs-hostpath")
    parser.add_argument("--gc", choices=("true", "false"), default="true")
    parser.add_argument("--repo", default="https://openebs.github.io/dynamic-nfs-provisioner")
    args = parser.parse_args()
    getattr(Fixtures(args), args.action)()


if __name__ == "__main__":
    main()
