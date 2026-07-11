from __future__ import annotations


class MockHospitalAdapter:
    source_system = "mock_hospital"

    def import_demo(self) -> dict:
        return {
            "patient": {
                "name": "Paciente Mock",
                "birth_date": "1988-04-12",
                "identifiers": [
                    {
                        "type": "hospital_record_number",
                        "value": "MOCK-12345",
                        "system": "mock_hospital",
                    }
                ],
            },
            "allergies": ["dipirona"],
            "conditions": ["problema nos rins"],
            "current_medications": ["sertralina"],
            "observations": [{"name": "creatinina", "value": "pendente de revisao"}],
            "documents": [{"title": "Resumo clinico mock"}],
        }
