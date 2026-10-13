#!/usr/bin/env python3
# Copyright 2026 The OpenEBS Authors.
# Licensed under the Apache License, Version 2.0.
"""Seed and verify disposable 0.11.0 upgrade fixtures using an explicit context."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import subprocess
import tarfile
import tempfile
import threading
import time

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
            timeout=420,
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
        # The old GitHub Pages repository no longer exists; use the exact release chart revision.
        repo_root = Path(__file__).resolve().parents[2]
        archive = subprocess.check_output([
            "git", "-C", str(repo_root), "archive", "077394ced96d0368e9e3e412d03d0c881bb64e2f",
            "deploy/helm/charts"])
        with tempfile.TemporaryDirectory(prefix="nfs-baseline-chart-") as directory:
            with tarfile.open(fileobj=io.BytesIO(archive)) as chart_archive:
                chart_archive.extractall(directory, filter="data")
            subprocess.run([
                "helm", "upgrade", "--install", "nfs-upgrade", str(Path(directory) / "deploy/helm/charts"),
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
            "deployment/" + deployment["metadata"]["name"], "--timeout=5m", "--request-timeout=5m")
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
                "strategy": {"type": "Recreate"},
                "selector": {"matchLabels": {"fixture": policy.lower()}}, "template": {
                    "metadata": {"labels": {"fixture": policy.lower()}}, "spec": {
                        "affinity": {"podAntiAffinity": {"requiredDuringSchedulingIgnoredDuringExecution": [
                            {"topologyKey": "kubernetes.io/hostname",
                             "labelSelector": {"matchLabels": {"fixture": policy.lower()}}}]}},
                        "containers": [{"name": "client", "image": "busybox:1.37.0", "command": ["sleep", "86400"],
                            "volumeMounts": [{"name": "data", "mountPath": "/data"}]}],
                        "volumes": [{"name": "data", "persistentVolumeClaim": {"claimName": name}}]}}}})
            self.kubectl("rollout", "status", "-n", self.namespace, "deployment/" + name, "--timeout=5m", "--request-timeout=5m")
            pod = self.pods(policy)[0]["metadata"]["name"]
            self.kubectl("exec", "-n", self.namespace, pod, "--", "sh", "-c",
                "printf 'dynamic-nfs-upgrade-fixture-v1\\n' > /data/proof && "
                "chown 1234:2345 /data/proof && chmod 640 /data/proof && sync")
        self.snapshot()

    def snapshot(self):
        state = {"context": self.args.context, "gc": self.args.gc, "claims": {},
                 "controller": self.get("deployments", "-n", self.namespace)["items"][0]["metadata"]["name"]}
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
        state = self.state()
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
                if sorted(current["metadata"].get("finalizers", [])) != sorted(original["metadata"].get("finalizers", [])):
                    raise RuntimeError(f"Finalizers changed: {resource}/{original['metadata']['name']}")
                if resource == "pvc" and current["spec"]["volumeName"] != original["spec"]["volumeName"]:
                    raise RuntimeError("PVC binding changed")
                if resource == "deployment" and not self.args.allow_server_image_change:
                    before = original["spec"]["template"]["spec"]["containers"]
                    after = current["spec"]["template"]["spec"]["containers"]
                    if [(c["name"], c["image"]) for c in before] != [(c["name"], c["image"]) for c in after]:
                        raise RuntimeError("Controller upgrade changed an existing server image")
            current_pv = self.get("pv", pv_name)
            if current_pv["spec"]["nfs"] != expected["pv"]["spec"]["nfs"]:
                raise RuntimeError(f"NFS endpoint changed for {pv_name}")
            if current_pv["spec"]["persistentVolumeReclaimPolicy"] != policy:
                raise RuntimeError(f"Reclaim policy changed for {pv_name}")
            if current_pv["spec"]["claimRef"]["uid"] != expected["pv"]["spec"]["claimRef"]["uid"]:
                raise RuntimeError("PV claim identity changed")
            pods = self.pods(policy)
            if len(pods) != 2:
                raise RuntimeError("Expected two RWX clients")
            if len({pod["spec"]["nodeName"] for pod in pods}) != 2:
                raise RuntimeError("RWX clients must run on different nodes")
            for pod in pods:
                name = pod["metadata"]["name"]
                checksum = self.kubectl("exec", "-n", self.namespace, name, "--", "sha256sum", "/data/proof").split()[0]
                permissions = self.kubectl("exec", "-n", self.namespace, name, "--", "stat", "-c", "%u:%g:%a", "/data/proof").strip()
                if checksum != hashlib.sha256(CONTENT.encode()).hexdigest() or permissions != "1234:2345:640":
                    raise RuntimeError(f"Data or ownership changed on {name}")
        print("Upgrade fixtures preserve identities, endpoints, policies, content, and ownership")

    def state(self):
        state = json.loads(self.args.state.read_text())
        if state["context"] != self.args.context or state["gc"] != self.args.gc:
            raise RuntimeError("Snapshot context/GC mode differs from this invocation")
        return state

    def rollout(self, namespace, deployment, restart=False):
        if restart:
            self.kubectl("rollout", "restart", "-n", namespace, "deployment/" + deployment)
        self.kubectl("rollout", "status", "-n", namespace, "deployment/" + deployment,
                     "--timeout=5m", "--request-timeout=5m")

    def upgrade_controller(self):
        state = self.state()
        chart = Path(__file__).resolve().parents[2] / "deploy/helm/charts"
        subprocess.run(["helm", "upgrade", "nfs-upgrade", str(chart), "--kube-context", self.args.context,
            "-n", self.namespace, "--reset-then-reuse-values", "--wait", "--timeout", "5m",
            "--set", "nfsProvisioner.image.repository=openebs/provisioner-nfs", "--set", "nfsProvisioner.image.tag=ci",
            "--set", "nfsProvisioner.nfsServerAlpineImage.repository=openebs/nfs-server-alpine",
            "--set", "nfsProvisioner.nfsServerAlpineImage.tag=ci"], check=True)
        self.check_configuration(state)
        self.verify()

    def check_configuration(self, state):
        controller = self.get("deployment", "-n", self.namespace, state["controller"])
        env = {item["name"]: item.get("value") for item in controller["spec"]["template"]["spec"]["containers"][0]["env"]}
        if env.get("OPENEBS_IO_NFS_SERVER_GARBAGE_COLLECTION_ENABLED") != self.args.gc:
            raise RuntimeError("GC configuration changed")
        if env.get("OPENEBS_IO_NFS_SERVER_NS") != self.servers:
            raise RuntimeError("Custom server namespace changed")

    def rollback_controller(self):
        state = self.state()
        subprocess.run(["helm", "rollback", "nfs-upgrade", "1", "--kube-context", self.args.context,
            "-n", self.namespace, "--wait", "--timeout", "5m"], check=True)
        # Restore the deliberately patched baseline false value (the old chart omits it).
        self.kubectl("set", "env", "-n", self.namespace, "deployment/" + state["controller"],
                     "OPENEBS_IO_NFS_SERVER_GARBAGE_COLLECTION_ENABLED=" + self.args.gc)
        self.rollout(self.namespace, state["controller"])
        self.check_configuration(state)
        self.verify()

    def restart_clients(self):
        self.state()
        for policy in POLICIES:
            self.rollout(self.namespace, "nfs-upgrade-" + policy.lower(), restart=True)
        self.verify()

    def server_cycle(self):
        """Measure successful read gaps during one server upgrade and rollback."""
        state = self.state()
        expected = state["claims"]["Retain"]["server"]
        server = expected["metadata"]["name"]
        original = next(c["image"] for c in expected["spec"]["template"]["spec"]["containers"] if c["name"] == "nfs-server")
        script = Path(__file__).resolve().parents[2] / "docs/tutorial/upgrade-nfs-server.sh"
        records = []
        for stage, image in (("upgrade", "openebs/nfs-server-alpine:ci"), ("rollback", original)):
            samples = []
            ready = threading.Event()
            pod = self.pods("Retain")[0]["metadata"]["name"]
            probe = subprocess.Popen(["kubectl", "--context", self.args.context, "exec", "-n", self.namespace,
                pod, "--", "sh", "-c", "i=0; while [ $i -lt 600 ]; do printf probe > /data/io-probe && sync && "
                "cat /data/proof >/dev/null && echo OK; i=$((i+1)); sleep 1; done"],
                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)

            def read_samples():
                for line in probe.stdout:
                    if line.strip() == "OK":
                        samples.append(time.monotonic())
                        ready.set()

            reader = threading.Thread(target=read_samples, daemon=True)
            reader.start()
            try:
                if not ready.wait(30):
                    raise RuntimeError("I/O probe did not start")
                start = time.monotonic()
                subprocess.run(["bash", str(script), "-c", self.args.context, "-n", self.servers,
                    "-d", server, "--image", image], check=True, timeout=420)
                # Require a successful client read after rollout, including NFS grace/recovery time.
                deadline = time.monotonic() + 180
                rollout_end = time.monotonic()
                while not samples or samples[-1] < rollout_end:
                    if time.monotonic() > deadline:
                        raise RuntimeError("Client I/O did not reconnect after server rollout")
                    time.sleep(1)
                records.append({"stage": stage, "rollout_seconds": rollout_end - start,
                    "max_successful_read_gap_seconds": max(b - a for a, b in zip(samples, samples[1:])),
                    "sampling_interval_seconds": 1})
                self.args.allow_server_image_change = stage == "upgrade"
                self.verify()
            finally:
                probe.terminate()
                try:
                    probe.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    probe.kill()
                    probe.wait()
                reader.join(timeout=5)
                self.args.state.with_suffix(".io.json").write_text(json.dumps(records, indent=2) + "\n")

    def verify_reclaim(self):
        state = self.state()
        # Only the fixture's application resources are deleted. Retained PVs/backends are never deleted.
        for policy in POLICIES:
            name = "nfs-upgrade-" + policy.lower()
            self.kubectl("delete", "deployment", "-n", self.namespace, name, "--wait=true", "--timeout=5m", "--request-timeout=5m")
            self.kubectl("delete", "pvc", "-n", self.namespace, name, "--wait=true", "--timeout=5m", "--request-timeout=5m")
        deleted = state["claims"]["Delete"]
        for resource, ns, obj in (("pv", None, deleted["pv"]), ("pvc", self.servers, deleted["backend"]),
                                  ("deployment", self.servers, deleted["server"])):
            args = ["wait", "--for=delete", resource + "/" + obj["metadata"]["name"], "--timeout=5m", "--request-timeout=5m"]
            if ns:
                args += ["-n", ns]
            self.kubectl(*args)
        retained = state["claims"]["Retain"]
        self.kubectl("wait", "--for=jsonpath={.status.phase}=Released", "pv/" + retained["pv"]["metadata"]["name"],
                     "--timeout=5m", "--request-timeout=5m")
        pv = self.get("pv", retained["pv"]["metadata"]["name"])
        if pv["status"]["phase"] != "Released" or pv["metadata"]["uid"] != retained["pv"]["metadata"]["uid"]:
            raise RuntimeError("Retain PV was not preserved")
        for resource, obj in (("pvc", retained["backend"]), ("deployment", retained["server"])):
            if self.get(resource, "-n", self.servers, obj["metadata"]["name"])["metadata"]["uid"] != obj["metadata"]["uid"]:
                raise RuntimeError("Retain backend/server was replaced")
        checksum = self.kubectl("exec", "-n", self.servers, "deployment/" + retained["server"]["metadata"]["name"],
            "--", "sha256sum", "/nfsshare/proof").split()[0]
        if checksum != hashlib.sha256(CONTENT.encode()).hexdigest():
            raise RuntimeError("Retained data changed after deleting its application claim")

    def verify_gc(self):
        state = self.state()
        orphan = "nfs-upgrade-orphan"
        self.apply({"apiVersion": "v1", "kind": "PersistentVolumeClaim", "metadata": {
            "name": orphan, "namespace": self.servers, "labels": {"openebs.io/cas-type": "nfs-kernel",
                "nfs.openebs.io/nfs-pvc-name": "missing-fixture", "nfs.openebs.io/nfs-pvc-namespace": self.namespace,
                "nfs.openebs.io/nfs-pvc-uid": "missing-fixture"}}, "spec": {"storageClassName": self.args.backend,
                "accessModes": ["ReadWriteOnce"], "resources": {"requests": {"storage": "1Mi"}}}})
        self.check_configuration(state)
        self.rollout(self.namespace, state["controller"], restart=True)
        if self.args.gc == "true":
            self.kubectl("wait", "--for=delete", "pvc/" + orphan, "-n", self.servers,
                         "--timeout=6m", "--request-timeout=6m")
        else:
            time.sleep(20)
            self.get("pvc", "-n", self.servers, orphan)
        retained = state["claims"]["Retain"]["backend"]
        if self.get("pvc", "-n", self.servers, retained["metadata"]["name"])["metadata"]["uid"] != retained["metadata"]["uid"]:
            raise RuntimeError("GC deleted the retained backend")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("seed", "snapshot", "verify", "upgrade-controller", "rollback-controller",
                                           "restart-clients", "server-cycle", "verify-reclaim", "verify-gc"))
    parser.add_argument("--context", required=True, help="Explicit disposable cluster context")
    parser.add_argument("--state", type=Path, default=Path("/tmp/nfs-upgrade-state.json"))
    parser.add_argument("--backend", default="openebs-hostpath")
    parser.add_argument("--gc", choices=("true", "false"), default="true")
    parser.add_argument("--allow-server-image-change", action="store_true")
    args = parser.parse_args()
    getattr(Fixtures(args), args.action.replace("-", "_"))()


if __name__ == "__main__":
    main()
