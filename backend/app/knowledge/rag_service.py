from __future__ import annotations

from app.domain.medication import Medication
from app.domain.patient import Patient
from app.domain.prescription import PrescriptionInput
from app.knowledge.retriever import EDUCATIONAL_NOTICE, retrieve


class ClinicalRAGService:
    def retrieve_for_prescription(
        self,
        patient: Patient,
        medication: Medication,
        prescription: PrescriptionInput,
    ) -> list[dict]:
        terms = [
            medication.brand_name,
            medication.active_ingredient,
            *(medication.commercial_aliases or []),
            medication.therapeutic_class,
            *(medication.therapeutic_classes or []),
            medication.therapeutic_action or "",
            medication.alternative_group or "",
            medication.source_jurisdiction,
            medication.evidence_source_type,
            medication.validation_status,
            *(medication.organs_involved or []),
            *(medication.metabolism_organs or []),
            *(medication.elimination_organs or []),
            *(medication.relevant_adverse_effects or []),
            patient.renal_condition or "",
            patient.hepatic_condition or "",
            patient.cardiac_condition or "",
            patient.gastrointestinal_history or "",
            prescription.indication or "",
            "dose acumulada",
            "duração",
        ]
        hits = [hit.to_dict() for hit in retrieve(terms)]
        if hits:
            return hits
        return [
            {
                "source": "fallback",
                "excerpt": "Nenhum trecho específico foi encontrado na base interna demonstrativa.",
                "score": 0,
                "matched_terms": [],
                "educational_notice": EDUCATIONAL_NOTICE,
                "jurisdiction": "BR",
                "source_name": "Base interna demonstrativa",
                "source_url": None,
                "evidence_type": "demo_seed",
                "validation_status": "demo",
                "active_ingredient": medication.active_ingredient,
                "commercial_names": medication.commercial_aliases or [medication.brand_name],
                "extracted_sections": [],
                "retrieved_at": None,
                "version": "v0.5.0-demo",
            }
        ]
