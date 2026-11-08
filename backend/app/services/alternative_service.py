from __future__ import annotations

from typing import Any

from app.domain.alert import PrescriptionStatus
from app.domain.medication import Medication
from app.domain.patient import Patient
from app.domain.prescription import PrescriptionInput
from app.repositories.medication_repository import MedicationRepository
from app.services.clinical_decision_orchestrator import ClinicalDecisionOrchestrator
from app.services.normalizer import normalize_text

MAX_OPTIONS = 4
# Ordem transparente de similaridade demonstrativa; empate desfeito por nome e id.
SIMILARITY_RANK = {"alternative_group": 0, "therapeutic_action": 1, "related": 2}
REVIEW_STATUS = "candidate_for_human_review"
DOSE_NOT_EVALUATED = "not_evaluated_for_alternative"


class AlternativeService:
    """Lista candidatos para revisão humana; nunca seleciona nem libera uma substituição.

    Cada candidato passa pelo mesmo orquestrador da checagem principal (dose, psicotrópicos,
    política do prescritor, cobertura), mas SEM herdar a dose do medicamento original: aplicar
    "500 mg do medicamento A" ao medicamento B não tem significado clínico. O orquestrador roda em
    modo `include_dose=False`: checagens dependentes de dose são puladas e a dose vira dado ausente
    (`insufficient_data`), e o status exibido nunca é `liberado`.
    """

    def __init__(self, repository: MedicationRepository, orchestrator=None) -> None:
        self.repository = repository
        self.orchestrator = orchestrator or ClinicalDecisionOrchestrator(repository.db)

    def evaluated_options(
        self,
        patient: Patient,
        medication: Medication,
        prescription: PrescriptionInput,
        *,
        should_include: bool,
        user: Any = None,
        functional_profile: Any | None = None,
        missing_context: list[str] | None = None,
    ) -> list[dict]:
        if not should_include:
            return []
        options: list[dict] = []
        for record, kind in self._ranked_candidates(medication)[:MAX_OPTIONS]:
            candidate = Medication.from_record(record)
            evaluation = self.orchestrator.evaluate(
                patient=patient,
                medication=candidate,
                prescription=prescription,
                user=user,
                functional_profile=functional_profile,
                missing_context=list(missing_context or []),
                rag_evidence=[],
                include_dose=False,
            )
            envelope = evaluation.envelope
            status = (
                PrescriptionStatus.BLOCKED
                if envelope.legacy_status == PrescriptionStatus.BLOCKED
                else PrescriptionStatus.ATTENTION
            )
            screening_alerts = [
                finding.to_legacy_alert().to_dict()
                for finding in envelope.findings
                if finding.module != "dose_intelligence"
            ]
            options.append(
                {
                    "medication_id": candidate.id,
                    "name": candidate.brand_name,
                    "active_ingredient": candidate.active_ingredient,
                    "therapeutic_class": candidate.therapeutic_class,
                    "similarity_reason": self._similarity_reason(kind),
                    "similarity_kind": kind,
                    "status": status.value,
                    "review_status": REVIEW_STATUS,
                    "decision_status": envelope.decision_status.value,
                    "coverage_status": envelope.coverage.status.value,
                    "dose_assessment": DOSE_NOT_EVALUATED,
                    "risk_level": envelope.highest_severity.value,
                    "top_alerts": screening_alerts[:3],
                    "observation": (
                        "Candidato para avaliação profissional; não é recomendação nem "
                        "substituição automática. A dose desta alternativa não foi avaliada."
                    ),
                }
            )
        return options

    def _ranked_candidates(self, medication: Medication) -> list[tuple[Any, str]]:
        current_id = medication.id
        group = normalize_text(medication.alternative_group or medication.therapeutic_class)
        action = normalize_text(medication.therapeutic_action or "")
        related = {normalize_text(item) for item in (medication.related_medications or [])}
        ranked: list[tuple[int, str, int, Any, str]] = []
        # Catálogo inteiro: list() pagina em 50 e descartava alternativas silenciosamente (NEW-04).
        for record in self.repository.iter_all():
            if record.id == current_id:
                continue
            record_group = normalize_text(record.alternative_group or record.therapeutic_class)
            if group and record_group == group:
                kind = "alternative_group"
            elif action and normalize_text(record.therapeutic_action or "") == action:
                kind = "therapeutic_action"
            elif normalize_text(record.active_ingredient) in related:
                kind = "related"
            else:
                continue
            ranked.append(
                (SIMILARITY_RANK[kind], normalize_text(record.brand_name), record.id, record, kind)
            )
        ranked.sort(key=lambda item: item[:3])
        return [(item[3], item[4]) for item in ranked]

    def _similarity_reason(self, kind: str) -> str:
        return {
            "alternative_group": "Mesmo grupo alternativo demonstrativo.",
            "therapeutic_action": "Ação/finalidade terapêutica semelhante.",
            "related": "Relacionamento demonstrativo cadastrado.",
        }[kind]
