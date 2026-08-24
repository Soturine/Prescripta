from __future__ import annotations

import base64
import json
import re
from typing import Any

from app.integrations.mapping.fhir_mapper import FhirMappingService
from app.services.canonical_json import canonical_sha256

FHIR_TARGET = "FHIR R4 JSON subset"
FHIR_IMPORTER_VERSION = "fhir-r4-subset-v1"
SUPPORTED_RESOURCES = frozenset(
    {
        "Patient",
        "AllergyIntolerance",
        "Condition",
        "MedicationStatement",
        "MedicationRequest",
        "Observation",
        "DiagnosticReport",
        "DocumentReference",
    }
)
_ID = re.compile(r"^[A-Za-z0-9\-.]{1,64}$")
_RELATIVE_REFERENCE = re.compile(r"^([A-Za-z][A-Za-z0-9]+)/([A-Za-z0-9\-.]{1,64})$")


class FhirBundleValidationError(ValueError):
    pass


class FhirBundleImporter:
    source_type = "fhir_bundle"
    max_bytes = 1_000_000
    max_entries = 200
    max_nodes = 20_000
    max_depth = 32
    max_attachment_bytes = 262_144

    def __init__(self) -> None:
        self.mapper = FhirMappingService()

    def import_bundle(self, bundle: dict) -> list[dict]:
        bundle_hash, resources, reference_states = self.validate_bundle(bundle)
        records: list[dict] = []
        for resource in resources:
            mapped = self.mapper.map_resource(resource)
            if not mapped:
                continue
            resource_key = f"{resource['resourceType']}/{resource['id']}"
            mapped_payload = mapped["mapped_payload"] | {
                "_lineage": {
                    "source_format": FHIR_TARGET,
                    "importer_version": FHIR_IMPORTER_VERSION,
                    "bundle_hash": bundle_hash,
                    "resource_key": resource_key,
                    "reference_states": reference_states.get(resource_key, []),
                    "semantic_roundtrip": "source_resource_preserved",
                }
            }
            records.append(
                {
                    "record_type": mapped["record_type"],
                    "source_payload": resource,
                    "mapped_payload": mapped_payload,
                    "confidence": mapped["confidence"],
                }
            )
        return records

    def validate_bundle(self, bundle: dict) -> tuple[str, list[dict], dict[str, list[dict]]]:
        if not isinstance(bundle, dict) or bundle.get("resourceType") != "Bundle":
            raise FhirBundleValidationError("Payload deve ser um Bundle FHIR R4 JSON.")
        if bundle.get("type") != "collection":
            raise FhirBundleValidationError("Somente Bundle.type=collection é suportado.")
        encoded = json.dumps(bundle, ensure_ascii=False, separators=(",", ":")).encode()
        if len(encoded) > self.max_bytes:
            raise FhirBundleValidationError("Bundle excede o limite de bytes.")
        self._validate_tree(bundle)
        entries = bundle.get("entry")
        if not isinstance(entries, list) or not entries or len(entries) > self.max_entries:
            raise FhirBundleValidationError("Bundle deve conter entre 1 e 200 entries.")

        resources: list[dict] = []
        identities: set[str] = set()
        for entry in entries:
            resource = entry.get("resource") if isinstance(entry, dict) else None
            if not isinstance(resource, dict):
                raise FhirBundleValidationError("Entry sem resource JSON válido.")
            resource_type = resource.get("resourceType")
            resource_id = resource.get("id")
            if resource_type not in SUPPORTED_RESOURCES:
                raise FhirBundleValidationError(f"Resource não suportado: {resource_type!s}.")
            if not isinstance(resource_id, str) or not _ID.fullmatch(resource_id):
                raise FhirBundleValidationError("Resource sem id FHIR válido.")
            identity = f"{resource_type}/{resource_id}"
            if identity in identities:
                raise FhirBundleValidationError("Resource duplicado no Bundle.")
            identities.add(identity)
            self._validate_minimum_fields(resource)
            resources.append(resource)

        states: dict[str, list[dict]] = {}
        for resource in resources:
            key = f"{resource['resourceType']}/{resource['id']}"
            states[key] = self._reference_states(resource, identities)
        return canonical_sha256(bundle), resources, states

    def export_preserved_bundle(self, records: list[dict]) -> dict:
        """Rebuild a collection from preserved sources; no inverse mapping is claimed."""
        return {
            "resourceType": "Bundle",
            "type": "collection",
            "entry": [{"resource": record["source_payload"]} for record in records],
        }

    def _validate_tree(self, value: Any) -> None:
        nodes = 0
        stack = [(value, 0)]
        while stack:
            item, depth = stack.pop()
            nodes += 1
            if nodes > self.max_nodes or depth > self.max_depth:
                raise FhirBundleValidationError("Bundle excede budget estrutural.")
            if isinstance(item, dict):
                attachment_data = item.get("data") if "contentType" in item else None
                if isinstance(attachment_data, str):
                    try:
                        decoded = base64.b64decode(attachment_data, validate=True)
                    except ValueError as exc:
                        raise FhirBundleValidationError("Attachment base64 inválido.") from exc
                    if len(decoded) > self.max_attachment_bytes:
                        raise FhirBundleValidationError("Attachment excede o limite de bytes.")
                stack.extend((child, depth + 1) for child in item.values())
            elif isinstance(item, list):
                stack.extend((child, depth + 1) for child in item)

    @staticmethod
    def _validate_minimum_fields(resource: dict) -> None:
        resource_type = resource["resourceType"]
        if resource_type in {"AllergyIntolerance", "Condition", "Observation"} and not resource.get(
            "code"
        ):
            raise FhirBundleValidationError(f"{resource_type} exige code.")
        if resource_type in {"MedicationStatement", "MedicationRequest"} and not (
            resource.get("medicationCodeableConcept") or resource.get("medicationReference")
        ):
            raise FhirBundleValidationError(f"{resource_type} exige medication[x].")
        if resource_type in {
            "AllergyIntolerance",
            "MedicationStatement",
            "MedicationRequest",
            "Observation",
            "DiagnosticReport",
        } and not resource.get("status"):
            raise FhirBundleValidationError(f"{resource_type} exige status.")

    @staticmethod
    def _reference_states(resource: dict, identities: set[str]) -> list[dict]:
        states: list[dict] = []
        stack: list[Any] = [resource]
        while stack:
            item = stack.pop()
            if isinstance(item, dict):
                reference = item.get("reference")
                if isinstance(reference, str):
                    matched = _RELATIVE_REFERENCE.fullmatch(reference)
                    if matched and reference in identities:
                        state = "resolved_in_bundle"
                    elif matched:
                        state = "unresolved_local"
                    else:
                        state = "external_unsupported_no_fetch"
                    states.append({"reference": reference, "state": state})
                stack.extend(item.values())
            elif isinstance(item, list):
                stack.extend(item)
        return states
