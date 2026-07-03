from __future__ import annotations

from app.integrations.mapping.terminology_mapper import TerminologyMapper


class InternalMapper:
    def __init__(self) -> None:
        self.terminology = TerminologyMapper()

    def patient(self, payload: dict) -> dict:
        return {
            "name": payload.get("name") or payload.get("full_name") or "Paciente externo",
            "birth_date": payload.get("birth_date") or payload.get("birthDate"),
            "phone": payload.get("phone"),
            "email": payload.get("email"),
            "mother_name": payload.get("mother_name"),
            "source": "external_pending_review",
        }

    def identifiers(self, payload: dict) -> list[dict]:
        identifiers = payload.get("identifiers") or payload.get("identifier") or []
        if isinstance(identifiers, dict):
            identifiers = [identifiers]
        mapped: list[dict] = []
        for identifier in identifiers:
            identifier_type = (
                identifier.get("type") or identifier.get("system") or "external_system_id"
            )
            value = identifier.get("value")
            if value:
                mapped.append(
                    {
                        "identifier_type": str(identifier_type),
                        "identifier_value": str(value),
                        "issuing_system": identifier.get("system"),
                    }
                )
        return mapped

    def medications(self, values: list[dict | str]) -> list[dict]:
        mapped: list[dict] = []
        for item in values:
            name = item if isinstance(item, str) else item.get("name") or item.get("medication")
            if name:
                mapped.append(self.terminology.medication(str(name)))
        return mapped

    def allergies(self, values: list[dict | str]) -> list[dict]:
        mapped: list[dict] = []
        for item in values:
            name = item if isinstance(item, str) else item.get("name") or item.get("substance")
            if name:
                mapped.append(self.terminology.allergy(str(name)))
        return mapped

    def conditions(self, values: list[dict | str]) -> list[dict]:
        mapped: list[dict] = []
        for item in values:
            name = item if isinstance(item, str) else item.get("name") or item.get("condition")
            if name:
                mapped.append(self.terminology.condition(str(name)))
        return mapped
