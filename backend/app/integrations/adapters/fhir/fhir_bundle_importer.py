from __future__ import annotations

from app.integrations.mapping.fhir_mapper import FhirMappingService


class FhirBundleImporter:
    source_type = "fhir_bundle"

    def __init__(self) -> None:
        self.mapper = FhirMappingService()

    def import_bundle(self, bundle: dict) -> list[dict]:
        records: list[dict] = []
        for entry in bundle.get("entry") or []:
            resource = entry.get("resource") or {}
            mapped = self.mapper.map_resource(resource)
            if not mapped:
                continue
            records.append(
                {
                    "record_type": mapped["record_type"],
                    "source_payload": resource,
                    "mapped_payload": mapped["mapped_payload"],
                    "confidence": mapped["confidence"],
                }
            )
        return records
