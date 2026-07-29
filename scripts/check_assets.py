#!/usr/bin/env python3
"""Valida a vitrine visual corrente e seu manifesto criptográfico."""

from __future__ import annotations

import hashlib
import json
import struct
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VERSION = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
ASSET_DIR = ROOT / "docs" / "assets" / "current"
REQUIRED = {
    f"prescripta-overview-v{VERSION}.gif",
    f"dashboard-v{VERSION}.png",
    f"patient-workspace-v{VERSION}.png",
    f"prescription-check-v{VERSION}.png",
    f"clinical-decision-v{VERSION}.png",
    f"pharmacy-review-v{VERSION}.png",
    f"audit-v{VERSION}.png",
    f"mobile-v{VERSION}.png",
}
MAX_BYTES = {".png": 2_000_000, ".gif": 5_000_000}


def dimensions(data: bytes, suffix: str) -> tuple[int, int]:
    if suffix == ".png" and data.startswith(b"\x89PNG\r\n\x1a\n"):
        return struct.unpack(">II", data[16:24])
    if suffix == ".gif" and data[:6] in {b"GIF87a", b"GIF89a"}:
        return struct.unpack("<HH", data[6:10])
    raise ValueError("assinatura de imagem inválida")


errors: list[str] = []
manifest_path = ASSET_DIR / "manifest.json"
if not ASSET_DIR.is_dir():
    errors.append("Diretório docs/assets/current ausente.")
if not manifest_path.is_file():
    errors.append("Manifesto docs/assets/current/manifest.json ausente.")

manifest: dict = {}
if manifest_path.is_file():
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        errors.append(f"Manifesto inválido: {exc}")

if manifest and manifest.get("version") != VERSION:
    errors.append(f"Versão do manifesto é {manifest.get('version')!r}; esperado {VERSION!r}.")

entries = {entry.get("file"): entry for entry in manifest.get("assets", []) if isinstance(entry, dict)}
for name in sorted(REQUIRED):
    asset = ASSET_DIR / name
    if not asset.is_file():
        errors.append(f"Asset obrigatório ausente: {name}")
        continue
    data = asset.read_bytes()
    suffix = asset.suffix.lower()
    if not data:
        errors.append(f"Asset vazio: {name}")
        continue
    if len(data) > MAX_BYTES[suffix]:
        errors.append(f"Asset excede o limite de {MAX_BYTES[suffix]} bytes: {name}")
    try:
        width, height = dimensions(data, suffix)
    except ValueError as exc:
        errors.append(f"{name}: {exc}")
        continue
    if width < 320 or height < 400:
        errors.append(f"Dimensão insuficiente em {name}: {width}x{height}")
    entry = entries.get(name)
    if entry is None:
        errors.append(f"Asset sem entrada no manifesto: {name}")
        continue
    expected = {
        "bytes": len(data),
        "width": width,
        "height": height,
        "sha256": hashlib.sha256(data).hexdigest(),
    }
    for field, value in expected.items():
        if entry.get(field) != value:
            errors.append(f"Manifesto divergente em {name}.{field}")

unexpected_entries = set(entries) - REQUIRED
if unexpected_entries:
    errors.append(f"Entradas inesperadas no manifesto: {', '.join(sorted(unexpected_entries))}")

if errors:
    print("\n".join(errors))
    sys.exit(1)
print(f"Assets v{VERSION} OK: {len(REQUIRED)} arquivos e manifesto íntegro.")
