from __future__ import annotations

from app.integrations.mapping.internal_mapper import InternalMapper


class GenericJsonImporter:
    source_type = "generic_json"

    def __init__(self) -> None:
        self.mapper = InternalMapper()

    def import_payload(self, payload: dict) -> list[dict]:
        records: list[dict] = []
        patient = payload.get("patient")
        if isinstance(patient, dict):
            mapped_patient = self.mapper.patient(patient)
            mapped_patient["identifiers"] = self.mapper.identifiers(patient)
            records.append(
                {
                    "record_type": "patient",
                    "source_payload": patient,
                    "mapped_payload": mapped_patient,
                    "confidence": 0.75,
                }
            )
        for record_type, key, mapper in [
            ("allergy", "allergies", self.mapper.allergies),
            ("condition", "conditions", self.mapper.conditions),
            ("current_medication", "current_medications", self.mapper.medications),
        ]:
            for mapped in mapper(payload.get(key) or []):
                records.append(
                    {
                        "record_type": record_type,
                        "source_payload": {"value": mapped["original_value"]},
                        "mapped_payload": mapped,
                        "confidence": mapped["confidence"],
                    }
                )
        for key in ("observations", "documents"):
            for item in payload.get(key) or []:
                records.append(
                    {
                        "record_type": key[:-1],
                        "source_payload": item if isinstance(item, dict) else {"value": item},
                        "mapped_payload": item if isinstance(item, dict) else {"value": item},
                        "confidence": 0.55,
                    }
                )
        medication_request = payload.get("medication_request")
        if isinstance(medication_request, dict):
            name = medication_request.get("name") or medication_request.get("medication")
            mapped = self.mapper.medications([name])[0] if name else medication_request
            records.append(
                {
                    "record_type": "medication_request",
                    "source_payload": medication_request,
                    "mapped_payload": mapped,
                    "confidence": mapped.get("confidence", 0.55)
                    if isinstance(mapped, dict)
                    else 0.55,
                }
            )
        return records
