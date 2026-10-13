# Copyright 2026 The OpenEBS Authors.
# Licensed under the Apache License, Version 2.0.
"""Exercise updater safety and kubectl failure propagation without a cluster."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[2] / "docs/tutorial/upgrade-nfs-server.sh"
MOCK = '''#!/usr/bin/env python3
import json, os, sys
with open(os.environ["CALLS"], "a") as log:
    log.write(json.dumps(sys.argv[1:]) + "\\n")
args = sys.argv[1:]
if "get" in args:
    if "json" in args:
        print(json.dumps({"metadata": {"labels": {"openebs.io/nfs-server": "true"}},
            "spec": {"template": {"spec": {"containers": [
                {"name": "sidecar", "image": "unused:1"},
                {"name": "nfs-server", "image": os.environ["OLD_IMAGE"]}]}}}}))
    else:
        print("server-one\\nserver-two")
if os.environ.get("FAIL_COMMAND") in args:
    sys.exit(42)
'''


class UpgradeScriptTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        mock = root / "kubectl"
        mock.write_text(MOCK)
        mock.chmod(0o755)
        self.calls = root / "calls.jsonl"
        self.env = dict(os.environ, PATH=str(root) + os.pathsep + os.environ["PATH"],
                        CALLS=str(self.calls), OLD_IMAGE="registry:5000/team/nfs@sha256:" + "a" * 64)

    def run_script(self, *args):
        return subprocess.run(["bash", str(SCRIPT), *args], env=self.env, capture_output=True, text=True)

    def commands(self):
        return [json.loads(line) for line in self.calls.read_text().splitlines()]

    def test_custom_namespace_registry_port_and_named_container(self):
        result = self.run_script("-n", "custom", "-c", "disposable", "-d", "server-one", "candidate")
        self.assertEqual(result.returncode, 0, result.stderr)
        calls = self.commands()
        self.assertTrue(all("custom" in call and "disposable" in call for call in calls))
        patch = next(call for call in calls if "patch" in call)
        container = json.loads(patch[patch.index("-p") + 1])["spec"]["template"]["spec"]["containers"][0]
        self.assertEqual(container, {"name": "nfs-server", "image": "registry:5000/team/nfs:candidate"})
        self.assertIn("--timeout=5m", calls[-1])

    def test_preview_does_not_mutate_any_server(self):
        result = self.run_script("--dry-run", "next")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(all("get" in call for call in self.commands()))
        self.assertIn("server-two", result.stdout)

    def test_restore_full_image(self):
        image = "ghcr.io/team/nfs@sha256:" + "b" * 64
        result = self.run_script("-d", "server-one", "--image", image)
        self.assertEqual(result.returncode, 0, result.stderr)
        patch = next(call for call in self.commands() if "patch" in call)
        self.assertEqual(json.loads(patch[-1])["spec"]["template"]["spec"]["containers"][0]["image"], image)

    def test_failed_patch_stops_batch(self):
        self.env["FAIL_COMMAND"] = "patch"
        result = self.run_script("next")
        self.assertEqual(result.returncode, 42)
        self.assertFalse(any("rollout" in call for call in self.commands()))
        self.assertNotIn("server-two", result.stdout)

    def test_rollout_failure_is_reported(self):
        self.env["FAIL_COMMAND"] = "rollout"
        self.assertEqual(self.run_script("-d", "server-one", "next").returncode, 42)

    def test_invalid_arguments_never_call_kubectl(self):
        for args in [(), ("-n",), ("--unknown",), ("bad tag",),
                     ("--image", "repo:tag", "other"), ("-t", "0s", "next")]:
            with self.subTest(args=args):
                self.assertNotEqual(self.run_script(*args).returncode, 0)
        self.assertFalse(self.calls.exists())


if __name__ == "__main__":
    unittest.main()
