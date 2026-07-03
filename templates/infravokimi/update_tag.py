#!/usr/bin/env python3
"""
update_image_tag.py
-------------------
Update Docker image tags in Kubernetes Deployment YAML manifests.
Modes
-----
Single service:
    python update_image_tag.py --service auth-service --tag stable

All services:
    python update_image_tag.py --service all --tag stable

"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from ruamel.yaml import YAML


yaml = YAML(typ="rt")  
yaml.preserve_quotes = True
yaml.width = 10_000
yaml.indent(mapping=2, sequence=4, offset=2)


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

MANIFEST_DIRS: list[str] = [
    "base/backend",
    "base/frontend",
    "base/jobs",
]


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="update_image_tag",
        description="Update Docker image tags in Kubernetes workload manifests.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    mode = parser.add_mutually_exclusive_group(required=True)

    mode.add_argument(
        "--service",
        metavar="SERVICE_NAME",
        help="Update single service manifest",
    )


    parser.add_argument(
        "--tag",
        required=True,
        metavar="IMAGE_TAG",
        help="New Docker image tag",
    )

    return parser


# ---------------------------------------------------------------------------
# YAML I/O (FIXED)
# ---------------------------------------------------------------------------

def load_yaml(path: Path) -> list[Any]:
    try:
        with path.open("r", encoding="utf-8") as fh:
            data = yaml.load_all(fh)
            return list(data)

    except Exception as exc:
        raise ValueError(f"Malformed YAML in '{path}': {exc}") from exc


def save_yaml(path: Path, data: list[Any]) -> None:
    try:
        with path.open("w", encoding="utf-8") as fh:
            yaml.dump_all(data, fh)

    except OSError as exc:
        raise OSError(f"Cannot write '{path}': {exc}") from exc


# ---------------------------------------------------------------------------
# Kubernetes validation
# ---------------------------------------------------------------------------

def is_supported_k8s_workload(manifest: dict[str, Any]) -> bool:
    kind = manifest.get("kind")
    api_version = str(manifest.get("apiVersion", ""))

    return (
        (kind == "Deployment" and api_version.startswith("apps/"))
        or (kind == "Job" and api_version.startswith("batch/"))
    )


def extract_container_image(manifest: dict[str, Any], path: Path) -> str:
    try:
        containers = manifest["spec"]["template"]["spec"]["containers"]

    except (KeyError, TypeError) as exc:
        raise ValueError(
            f"Unexpected manifest structure in '{path}' — "
            f"spec.template.spec.containers not found: {exc}"
        ) from exc

    if not containers:
        raise ValueError(f"No containers defined in '{path}'.")

    image = containers[0].get("image")

    if not image:
        raise ValueError(f"Missing image in '{path}'.")

    return image


# ---------------------------------------------------------------------------
# Image replacement (safe & correct)
# ---------------------------------------------------------------------------

def replace_image_tag(image: str, new_tag: str) -> str:
    # handle digest images: repo@sha256:...
    if "@" in image:
        base = image.split("@")[0]
        return f"{base}:{new_tag}"

    # split registry/repo:tag
    if ":" in image:
        left, right = image.rsplit(":", 1)

        # if right contains slash → it's probably port (e.g. :5000)
        if "/" in right:
            return f"{image}:{new_tag}"

        return f"{left}:{new_tag}"

    return f"{image}:{new_tag}"


# ---------------------------------------------------------------------------
# Core logic
# ---------------------------------------------------------------------------

def update_manifest(path: Path, new_tag: str) -> bool:
    documents = load_yaml(path)

    if not documents:
        print(f"  [skip] '{path}' — empty YAML file.")
        return False

    manifest = documents[0]

    if not isinstance(manifest, dict):
        print(f"  [skip] '{path}' — invalid manifest.")
        return False

    if not is_supported_k8s_workload(manifest):
        print(f"  [skip] '{path}' — not supported workload.")
        return False

    old_image = extract_container_image(manifest, path)
    new_image = replace_image_tag(old_image, new_tag)

    if old_image == new_image:
        print(f"  [skip] '{path}' — already up to date.")
        return False


    manifest["spec"]["template"]["spec"]["containers"][0]["image"] = new_image

    save_yaml(path, documents)

    print(f"  [ok] '{path}'")
    print(f"       {old_image}")
    print(f"       → {new_image}")

    return True


# ---------------------------------------------------------------------------
# Service discovery
# ---------------------------------------------------------------------------

def find_manifest(service_name: str) -> Path:
    for directory in MANIFEST_DIRS:
        for ext in (".yaml", ".yml"):
            candidate = Path(directory) / f"{service_name}{ext}"
            if candidate.is_file():
                return candidate

    raise FileNotFoundError(f"Service '{service_name}' not found.")


def run_single_service(service_name: str, new_tag: str) -> None:
    print(f"[mode] single-service")
    print(f"[service] {service_name}")
    print(f"[tag] {new_tag}\n")

    path = find_manifest(service_name)
    update_manifest(path, new_tag)

    print("\n[done]")


def collect_manifests() -> list[Path]:
    paths: list[Path] = []

    for directory in MANIFEST_DIRS:
        dir_path = Path(directory)

        if not dir_path.exists():
            print(f"[warn] missing directory: {dir_path}")
            continue

        for pattern in ("*.yaml", "*.yml"):
            paths.extend(dir_path.glob(pattern))

    return sorted(paths)


def run_all_services(new_tag: str) -> None:
    print(f"[mode] all-services")
    print(f"[tag] {new_tag}\n")

    manifests = collect_manifests()

    if not manifests:
        print("[error] no yaml files found")
        sys.exit(1)

    updated = skipped = failed = 0

    for path in manifests:
        try:
            changed = update_manifest(path, new_tag)

            if changed:
                updated += 1
            else:
                skipped += 1

        except Exception as exc:
            print(f"  [fail] '{path}' — {exc}")
            failed += 1

    print(f"\n[done] updated={updated} skipped={skipped} failed={failed}")

    if failed:
        sys.exit(1)


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def main() -> None:
    parser = build_arg_parser()
    args = parser.parse_args()

    if args.service == "all":
        run_all_services(args.tag)
    else:
        run_single_service(args.service, args.tag)


if __name__ == "__main__":
    main()
