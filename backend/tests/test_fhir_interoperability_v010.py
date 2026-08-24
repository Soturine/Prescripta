from __future__ import annotations

import base64

import pytest
from fastapi.testclient import TestClient

from app.domain.user import UserRole
from app.integrations.adapters.fhir.fhir_bundle_importer import (
    FHIR_TARGET,
    FhirBundleImporter,
    FhirBundleValidationError,
)
from app.services.canonical_json import canonical_sha256


def _bundle() -> dict:
    return {
        "resourceType": "Bundle",
        "type": "collection",
        "entry": [
            {"resource": {"resourceType": "Patient", "id": "patient-1"}},
            {
                "resource": {
                    "resourceType": "Condition",
                    "id": "condition-1",
                    "subject": {"reference": "Patient/patient-1"},
                    "code": {
                        "text": "Synthetic condition",
                        "coding": [
                            {
                                "system": "http://snomed.info/sct",
                                "version": "demo-version",
                                "code": "123",
                                "display": "Synthetic condition",
                            }
                        ],
                    },
                }
            },
        ],
    }


def test_fhir_r4_subset_preserves_coding_lineage_and_semantic_source_roundtrip() -> None:
    importer = FhirBundleImporter()
    bundle = _bundle()
    records = importer.import_bundle(bundle)
    condition = records[1]
    assert condition["mapped_payload"]["source_codings"][0]["system"].endswith("/sct")
    lineage = condition["mapped_payload"]["_lineage"]
    assert lineage["source_format"] == FHIR_TARGET
    assert lineage["reference_states"] == [
        {"reference": "Patient/patient-1", "state": "resolved_in_bundle"}
    ]
    exported = importer.export_preserved_bundle(records)
    assert canonical_sha256(exported) == canonical_sha256(bundle)


@pytest.mark.parametrize(
    "mutate",
    [
        lambda bundle: bundle.update(type="transaction"),
        lambda bundle: bundle["entry"].append(bundle["entry"][0]),
        lambda bundle: bundle["entry"][0]["resource"].update(resourceType="Practitioner"),
    ],
)
def test_fhir_subset_rejects_unsupported_or_ambiguous_bundles(mutate) -> None:
    bundle = _bundle()
    mutate(bundle)
    with pytest.raises(FhirBundleValidationError):
        FhirBundleImporter().import_bundle(bundle)


def test_fhir_subset_rejects_oversized_attachment() -> None:
    bundle = _bundle()
    bundle["entry"].append(
        {
            "resource": {
                "resourceType": "DocumentReference",
                "id": "document-1",
                "status": "current",
                "content": [
                    {
                        "attachment": {
                            "contentType": "application/octet-stream",
                            "data": base64.b64encode(b"x" * 262_145).decode(),
                        }
                    }
                ],
            }
        }
    )
    with pytest.raises(FhirBundleValidationError, match="Attachment"):
        FhirBundleImporter().import_bundle(bundle)


def test_fhir_import_is_idempotent_and_rejects_key_reuse(
    client: TestClient, create_test_user, auth_headers
) -> None:
    email = "fhir-idempotency@example.test"
    create_test_user(email=email, password="Admin@12345", role=UserRole.FARMACEUTICO)
    headers = auth_headers(email, "Admin@12345")
    payload = {
        "consent_confirmed": True,
        "purpose": "synthetic interoperability test",
        "authorized_by": "Synthetic Patient",
        "source_system": "fhir-v010-test",
        "idempotency_key": "fhir-idempotency-1",
        "bundle": _bundle(),
    }
    first = client.post("/api/integrations/fhir/import-bundle", headers=headers, json=payload)
    second = client.post("/api/integrations/fhir/import-bundle", headers=headers, json=payload)
    assert first.status_code == second.status_code == 200
    assert first.json()["id"] == second.json()["id"]

    payload["bundle"]["entry"][0]["resource"]["id"] = "patient-2"
    conflict = client.post("/api/integrations/fhir/import-bundle", headers=headers, json=payload)
    assert conflict.status_code == 400
    assert "Idempotency key" in conflict.json()["detail"]
