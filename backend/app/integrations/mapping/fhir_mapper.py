from __future__ import annotations

from app.integrations.mapping.terminology_mapper import TerminologyMapper


def _coding_text(resource: dict) -> str:
    code = resource.get("code") or resource.get("medicationCodeableConcept") or {}
    if isinstance(code, str):
        return code
    if code.get("text"):
        return str(code["text"])
    coding = code.get("coding") or []
    if coding:
        first = coding[0]
        return str(first.get("display") or first.get("code") or "")
    return ""


class FhirMappingService:
    def __init__(self) -> None:
        self.terminology = TerminologyMapper()

    def map_resource(self, resource: dict) -> dict | None:
        resource_type = resource.get("resourceType")
        if resource_type == "Patient":
            return self._patient(resource)
        if resource_type == "AllergyIntolerance":
            text = _coding_text(resource)
            return {
                "record_type": "allergy",
                "mapped_payload": self.terminology.allergy(text),
                "confidence": 0.75,
            }
        if resource_type == "Condition":
            text = _coding_text(resource)
            return {
                "record_type": "condition",
                "mapped_payload": self.terminology.condition(text),
                "confidence": 0.75,
            }
        if resource_type in {"MedicationStatement", "MedicationRequest"}:
            text = _coding_text(resource)
            return {
                "record_type": "medication_request"
                if resource_type == "MedicationRequest"
                else "current_medication",
                "mapped_payload": self.terminology.medication(text),
                "confidence": 0.75,
            }
        if resource_type == "Observation":
            return {
                "record_type": "observation",
                "mapped_payload": {
                    "code": _coding_text(resource),
                    "value": resource.get("valueQuantity") or resource.get("valueString"),
                    "status": resource.get("status"),
                },
                "confidence": 0.65,
            }
        if resource_type in {"DiagnosticReport", "DocumentReference"}:
            return {
                "record_type": "document",
                "mapped_payload": {
                    "title": resource.get("description") or resource.get("status") or resource_type,
                    "resource_type": resource_type,
                },
                "confidence": 0.6,
            }
        return None

    def _patient(self, resource: dict) -> dict:
        names = resource.get("name") or []
        name = "Paciente FHIR"
        if names:
            first = names[0]
            family = first.get("family") or ""
            given = " ".join(first.get("given") or [])
            name = f"{given} {family}".strip() or name
        identifiers = [
            {
                "identifier_type": item.get("type", {}).get("text")
                or item.get("system")
                or "external_system_id",
                "identifier_value": item.get("value"),
                "issuing_system": item.get("system"),
            }
            for item in resource.get("identifier") or []
            if item.get("value")
        ]
        return {
            "record_type": "patient",
            "mapped_payload": {
                "name": name,
                "birth_date": resource.get("birthDate"),
                "identifiers": identifiers,
            },
            "confidence": 0.8,
        }
