from __future__ import annotations

import hashlib
import json
import sys
import uuid
from pathlib import Path


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("usage: stamp_cyclonedx_serial.py LOCKFILE SBOM")

    lockfile = Path(sys.argv[1])
    sbom_path = Path(sys.argv[2])
    sbom = json.loads(sbom_path.read_text(encoding="utf-8"))
    if sbom.get("bomFormat") != "CycloneDX" or not sbom.get("specVersion"):
        raise SystemExit("expected a CycloneDX JSON SBOM")

    lock_digest = hashlib.sha256(lockfile.read_bytes()).hexdigest()
    identity = f"prescripta-sbom:{lockfile.name}:sha256:{lock_digest}"
    sbom["serialNumber"] = f"urn:uuid:{uuid.uuid5(uuid.NAMESPACE_URL, identity)}"
    sbom_path.write_text(
        json.dumps(sbom, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
