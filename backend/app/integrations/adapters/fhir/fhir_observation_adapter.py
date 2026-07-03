from __future__ import annotations

from app.integrations.mapping.fhir_mapper import FhirMappingService


class FhirObservationAdapter:
    def __init__(self, resources: list[dict]) -> None:
        self.resources = resources
        self.mapper = FhirMappingService()

    def get_observations(self) -> list[dict]:
        return [
            resource
            for resource in self.resources
            if resource.get("resourceType") == "Observation"
        ]

    def normalize_observations(self) -> list[dict]:
        return [
            mapped["mapped_payload"]
            for resource in self.get_observations()
            if (mapped := self.mapper.map_resource(resource))
        ]
