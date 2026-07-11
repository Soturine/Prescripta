from __future__ import annotations

from app.integrations.mapping.fhir_mapper import FhirMappingService


class FhirPatientAdapter:
    def __init__(self, resource: dict) -> None:
        self.resource = resource
        self.mapper = FhirMappingService()

    def get_patient(self) -> dict:
        mapped = self.mapper.map_resource(self.resource) or {}
        return mapped.get("mapped_payload", {})

    def get_patient_identifiers(self) -> list[dict]:
        return self.get_patient().get("identifiers", [])

    def normalize_patient(self) -> dict:
        return self.get_patient()
