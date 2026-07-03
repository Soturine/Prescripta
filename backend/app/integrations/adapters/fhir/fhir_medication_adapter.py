from __future__ import annotations

from app.integrations.mapping.fhir_mapper import FhirMappingService


class FhirMedicationAdapter:
    def __init__(self, resources: list[dict]) -> None:
        self.resources = resources
        self.mapper = FhirMappingService()

    def get_current_medications(self) -> list[dict]:
        return [
            resource
            for resource in self.resources
            if resource.get("resourceType") == "MedicationStatement"
        ]

    def get_medication_history(self) -> list[dict]:
        return self.get_current_medications()

    def normalize_medications(self) -> list[dict]:
        return [
            mapped["mapped_payload"]
            for resource in self.get_current_medications()
            if (mapped := self.mapper.map_resource(resource))
        ]
