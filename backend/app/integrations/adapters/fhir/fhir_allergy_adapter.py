from __future__ import annotations

from app.integrations.mapping.fhir_mapper import FhirMappingService


class FhirAllergyAdapter:
    def __init__(self, resources: list[dict]) -> None:
        self.resources = resources
        self.mapper = FhirMappingService()

    def get_allergies(self) -> list[dict]:
        return [
            resource
            for resource in self.resources
            if resource.get("resourceType") == "AllergyIntolerance"
        ]

    def normalize_allergies(self) -> list[dict]:
        return [
            mapped["mapped_payload"]
            for resource in self.get_allergies()
            if (mapped := self.mapper.map_resource(resource))
        ]
