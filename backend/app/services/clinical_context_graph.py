from __future__ import annotations

from app.domain.medication import Medication
from app.domain.patient import Patient
from app.domain.prescription import PrescriptionInput
from app.services.controlled_vocabulary import label_for_code


def build_clinical_context_graph(
    patient: Patient,
    medication: Medication,
    prescription: PrescriptionInput,
    alerts: list[dict],
    rag_evidence: list[dict] | None = None,
) -> dict:
    daily_total = prescription.daily_total_mg
    cumulative = daily_total * prescription.duration_days if prescription.duration_days else None
    nodes = [
        {"id": "patient", "label": patient.name, "type": "Paciente"},
        {"id": "medication", "label": medication.brand_name, "type": "Medicamento"},
        {"id": "dose", "label": f"{daily_total:g} mg/dia", "type": "Dose diária"},
        {
            "id": "duration",
            "label": str(prescription.duration_days or "não informada"),
            "type": "Duração",
        },
        {
            "id": "cumulative",
            "label": f"{cumulative:g} mg" if cumulative else "-",
            "type": "Dose acumulada",
        },
        {"id": "alerts", "label": f"{len(alerts)} alertas", "type": "Regras"},
        {"id": "rag", "label": f"{len(rag_evidence or [])} evidências", "type": "RAG interno"},
    ]
    patient_factors = [
        factor
        for factor in [
            label_for_code(patient.renal_condition),
            label_for_code(patient.hepatic_condition),
            label_for_code(patient.cardiac_condition),
            label_for_code(patient.gastrointestinal_history),
            "hipertensao" if patient.hypertension else None,
            "diabetes" if patient.diabetes else None,
        ]
        if factor
    ]
    medication_factors = [
        factor
        for factor in [
            "cautela renal" if medication.renal_caution else None,
            "cautela hepatica" if medication.hepatic_caution else None,
            "cautela cardiaca" if medication.cardiac_caution else None,
            "cautela gastrointestinal" if medication.gastrointestinal_caution else None,
            "cautela em idosos" if medication.elderly_caution else None,
            f"principio ativo: {medication.active_ingredient}",
            f"jurisdicao: {medication.source_jurisdiction}",
            *(medication.organs_involved or []),
        ]
        if factor
    ]
    edges = [
        {"from": "patient", "to": "medication", "label": "prescrição pretendida"},
        {"from": "medication", "to": "dose", "label": "dose informada"},
        {"from": "dose", "to": "cumulative", "label": "dose x frequência x duração"},
        {"from": "patient", "to": "alerts", "label": "perfil clínico avaliado"},
        {"from": "medication", "to": "alerts", "label": "metadados do medicamento"},
        {"from": "rag", "to": "alerts", "label": "contexto explicativo"},
    ]
    return {
        "nodes": nodes,
        "edges": edges,
        "patient_factors": patient_factors,
        "medication_factors": medication_factors,
    }
