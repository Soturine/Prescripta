"""PRE-09: a matriz de acesso documentada da CDS API deve refletir o código, não perfis antigos."""

from __future__ import annotations

import re
from pathlib import Path

from app.domain.user import PROFESSION_CAPABILITY_TEMPLATES, Capability

DOC = Path(__file__).resolve().parents[2] / "docs" / "interoperability" / "cds-api.md"


def test_cds_capability_matrix_matches_profession_templates() -> None:
    text = DOC.read_text(encoding="utf-8")
    block = re.search(
        r"<!-- cds-capability-matrix:start -->(.*?)<!-- cds-capability-matrix:end -->",
        text,
        re.S,
    )
    assert block, "bloco da matriz ausente em cds-api.md"
    documented = {
        row[0].strip(): row[1].strip() == "sim"
        for row in re.findall(r"^\| ([a-z_]+) \| (sim|não) \|$", block.group(1), re.M)
    }
    expected = {
        getattr(profession, "value", profession): Capability.PRESCRIPTION_CHECK in capabilities
        for profession, capabilities in PROFESSION_CAPABILITY_TEMPLATES.items()
    }
    assert documented == expected
