#!/usr/bin/env python3
# Copyright 2026 The OpenEBS Authors.
# Licensed under the Apache License, Version 2.0.
"""Package candidate files locally; never build, push, tag, or publish a release."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path, help="New or empty artifact directory")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    chart = root / "deploy/helm/charts"
    metadata = dict(re.findall(r"^(version|appVersion):\s*(\S+)\s*$", (chart / "Chart.yaml").read_text(), re.M))
    version = metadata["version"]
    if version != metadata["appVersion"] or not re.fullmatch(r"\d+\.\d+\.\d+(?:-[a-zA-Z0-9.-]+)?", version):
        parser.error("Chart version and appVersion must match and use semantic versioning")
    raw = root / "deploy/kubectl/openebs-nfs-provisioner.yaml"
    images = [f"ghcr.io/schrodit/{name}:{version}" for name in ("provisioner-nfs", "nfs-server-alpine")]
    if any(image not in raw.read_text() for image in images):
        parser.error("Raw manifest images do not match the candidate version")
    output = args.output.resolve()
    if output.exists() and any(output.iterdir()):
        parser.error("Output directory must be empty; existing artifacts are never overwritten")
    subprocess.run(["helm", "lint", str(chart)], check=True)
    output.mkdir(parents=True, exist_ok=True)
    subprocess.run(["helm", "package", str(chart), "--destination", str(output)], check=True)
    shutil.copy2(raw, output / raw.name)
    shutil.copy2(root / "CHANGELOG.md", output / "CHANGELOG.md")
    rendered = subprocess.check_output(["helm", "template", "nfs", str(chart), "-n", "openebs"])
    (output / "helm-rendered.yaml").write_bytes(rendered)
    manifest = {"version": version, "sourceCommit": subprocess.check_output(
        ["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip(),
        "workingTreeDirty": bool(subprocess.check_output(["git", "-C", str(root), "status", "--porcelain"])),
        "goVersion": (root / ".go-version").read_text().strip(), "intendedImages": images,
        "published": False, "qualification": "Runtime qualification is recorded separately in CI artifacts; packaging is not qualification",
        "clusterTargets": ["1.35.9", "1.36.5", "1.37.1"], "runtimeArchitectureTargets": ["amd64", "arm64"],
        "buildOnlyArchitectures": ["arm/v7", "ppc64le"]}
    (output / "release-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    (output / "SHA256SUMS").write_text("".join(
        f"{hashlib.sha256(file.read_bytes()).hexdigest()}  {file.name}\n" for file in sorted(output.iterdir()) if file.is_file()))
    print(f"Prepared {version} in {output}; nothing was published")


if __name__ == "__main__":
    main()
