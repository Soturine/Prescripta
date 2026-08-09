#!/usr/bin/env python3
"""Validate the stable product gallery and release-scoped visual evidence."""

from __future__ import annotations

import hashlib
import json
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
ASSETS_ROOT = ROOT / "docs" / "assets"
MAX_BYTES = {".png": 2_000_000, ".gif": 5_000_000}
CURRENT_STEMS = {
    "prescripta-overview",
    "dashboard",
    "dashboard-en-US",
    "patient-workspace",
    "prescription-check",
    "clinical-decision",
    "pharmacy-review",
    "research-workspace",
    "cohort-attrition",
    "audit",
    "mobile",
}


def dimensions(data: bytes, suffix: str) -> tuple[int, int]:
    if suffix == ".png" and data.startswith(b"\x89PNG\r\n\x1a\n"):
        return struct.unpack(">II", data[16:24])
    if suffix == ".gif" and data[:6] in {b"GIF87a", b"GIF89a"}:
        return struct.unpack("<HH", data[6:10])
    raise ValueError("invalid image signature")


def validate_gallery(
    directory: Path,
    *,
    expected_version: str | None,
    required: set[str] | None,
) -> tuple[list[str], str, int]:
    errors: list[str] = []
    manifest_path = directory / "manifest.json"
    if not directory.is_dir():
        return [f"Asset directory missing: {directory.relative_to(ROOT)}"], "", 0
    if not manifest_path.is_file():
        return [f"Asset manifest missing: {manifest_path.relative_to(ROOT)}"], "", 0
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        return [f"Invalid asset manifest {manifest_path.relative_to(ROOT)}: {exc}"], "", 0

    manifest_version = str(manifest.get("version", ""))
    if expected_version is not None and manifest_version != expected_version:
        errors.append(
            f"Manifest {directory.name} is {manifest_version!r}; expected {expected_version!r}."
        )
    entries = {
        entry.get("file"): entry
        for entry in manifest.get("assets", [])
        if isinstance(entry, dict) and isinstance(entry.get("file"), str)
    }
    actual = {
        path.name
        for path in directory.iterdir()
        if path.is_file() and path.suffix.lower() in MAX_BYTES
    }
    expected = required if required is not None else actual
    for name in sorted(expected):
        asset = directory / name
        if not asset.is_file():
            errors.append(f"Required asset missing: {directory.name}/{name}")
            continue
        data = asset.read_bytes()
        suffix = asset.suffix.lower()
        if not data:
            errors.append(f"Empty asset: {directory.name}/{name}")
            continue
        if len(data) > MAX_BYTES[suffix]:
            errors.append(f"Asset exceeds {MAX_BYTES[suffix]} bytes: {directory.name}/{name}")
        try:
            width, height = dimensions(data, suffix)
        except ValueError as exc:
            errors.append(f"{directory.name}/{name}: {exc}")
            continue
        if width < 320 or height < 400:
            errors.append(f"Insufficient dimensions in {directory.name}/{name}: {width}x{height}")
        entry = entries.get(name)
        if entry is None:
            errors.append(f"Asset missing from manifest: {directory.name}/{name}")
            continue
        for field, value in {
            "bytes": len(data),
            "width": width,
            "height": height,
            "sha256": hashlib.sha256(data).hexdigest(),
        }.items():
            if entry.get(field) != value:
                errors.append(f"Manifest mismatch in {directory.name}/{name}.{field}")

    extras = set(entries) - expected
    missing_entries = actual - set(entries)
    if extras:
        errors.append(f"Unexpected manifest entries in {directory.name}: {', '.join(sorted(extras))}")
    if missing_entries:
        errors.append(
            f"Unmanifested assets in {directory.name}: {', '.join(sorted(missing_entries))}"
        )
    return errors, manifest_version, len(expected)


current_manifest = json.loads(
    (ASSETS_ROOT / "current" / "manifest.json").read_text(encoding="utf-8")
)
current_version = str(current_manifest.get("version", ""))
current_required = {
    f"{stem}-v{current_version}{'.gif' if stem == 'prescripta-overview' else '.png'}"
    for stem in CURRENT_STEMS
}
errors, _, current_count = validate_gallery(
    ASSETS_ROOT / "current",
    expected_version=None,
    required=current_required,
)

release_dir = ASSETS_ROOT / f"v{VERSION}"
release_errors, _, release_count = validate_gallery(
    release_dir,
    expected_version=VERSION,
    required=None,
)
errors.extend(release_errors)
for path in release_dir.glob("*.*") if release_dir.is_dir() else []:
    if path.suffix.lower() in MAX_BYTES and f"-v{VERSION}" not in path.stem:
        errors.append(f"Release asset lacks version suffix: {path.name}")

if errors:
    print("\n".join(errors))
    sys.exit(1)
print(
    f"Assets OK: stable gallery v{current_version} ({current_count}) and "
    f"release v{VERSION} ({release_count})."
)
