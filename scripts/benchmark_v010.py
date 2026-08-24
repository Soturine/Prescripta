#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path
from time import perf_counter

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.integrations.adapters.fhir.fhir_bundle_importer import (
    FhirBundleImporter,
)
from app.services.bounded_numeric_scanner import scan_numbers_in_value
from app.services.evidence_acquisition_service import (
    EvidenceAcquisitionService,
)

BUDGETS_MS = {"numeric_scan": 250, "fhir_import": 500, "evidence_dedupe": 300}


def timed(operation, iterations: int) -> float:
    started = perf_counter()
    for _ in range(iterations):
        operation()
    return round((perf_counter() - started) * 1000, 3)


def main() -> int:
    numeric_payload = [{"text": f"RR {index / 10:.1f}"} for index in range(500)]
    bundle = {
        "resourceType": "Bundle",
        "type": "collection",
        "entry": [
            {"resource": {"resourceType": "Patient", "id": f"patient-{index}"}}
            for index in range(100)
        ],
    }
    evidence = [
        {
            "provider": "crossref",
            "title": f"Synthetic title {index}",
            "year": "2026",
            "authors": ["Synthetic Author"],
            "journal": "Synthetic Journal",
            "doi": f"10.1000/{index}",
            "pmid": None,
            "pmcid": None,
            "openalex_id": None,
        }
        for index in range(500)
    ]
    results = {
        "numeric_scan": timed(lambda: scan_numbers_in_value(numeric_payload), 10),
        "fhir_import": timed(lambda: FhirBundleImporter().import_bundle(bundle), 10),
        "evidence_dedupe": timed(lambda: EvidenceAcquisitionService.deduplicate(evidence), 10),
    }
    regressions = [name for name, elapsed in results.items() if elapsed > BUDGETS_MS[name]]
    print(
        json.dumps(
            {
                "schema": "prescripta-benchmark-v1",
                "workload": "bounded_synthetic_demo",
                "iterations": 10,
                "elapsed_ms": results,
                "budgets_ms": BUDGETS_MS,
                "regressions": regressions,
                "async_decision": "not_needed_by_benchmark",
            },
            sort_keys=True,
        )
    )
    return 1 if regressions else 0


if __name__ == "__main__":
    raise SystemExit(main())
