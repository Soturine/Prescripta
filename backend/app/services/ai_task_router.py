from __future__ import annotations

import time
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.orm import Session

from app.database.models import (
    AIInteractionModel,
    EvidenceSourceModel,
    ResearchStudyModel,
    UserModel,
)
from app.schemas.ai_task_schema import AIInteractionReviewRequest, AIRequestSchema
from app.services.ai_settings import AISettingsService
from app.services.audit_service import AuditService
from app.services.canonical_json import canonical_sha256, json_compatible
from app.services.cohort_dsl import CohortDSLValidationError, CohortDSLValidator

TASK_TEMPLATE_VERSIONS = {
    "clinical_decision_explanation": "clinical-explanation-v1",
    "research_question_structuring": "research-question-v1",
    "cohort_draft": "cohort-draft-v1",
    "study_protocol_draft": "study-protocol-draft-v1",
    "evidence_summary": "evidence-summary-v1",
    "patient_journey_summary": "patient-journey-v1",
    "data_quality_explanation": "data-quality-explanation-v1",
}
KNOWN_PROVIDERS = {"fallback", "openai", "gemini", "ollama", "openai_compatible"}


class AITaskError(ValueError):
    pass


class AITaskRouter:
    def __init__(self, db: Session) -> None:
        self.db = db

    def execute(self, request: AIRequestSchema, actor: UserModel) -> AIInteractionModel:
        self._authorize_context(request, actor)
        configured = AISettingsService(self.db).runtime_config()
        provider = self._provider_for(request, configured.provider)
        started = time.monotonic()
        fallback_used = provider == "fallback"
        sanitized_error: str | None = None
        try:
            if provider == "fallback":
                output = self._fallback_output(request)
                model = "deterministic-template-v1"
            else:
                output = AISettingsService(self.db).complete_json(
                    system_instructions=self._system_instructions(request.task_type),
                    payload=self._minimized_payload(request),
                    purpose=request.purpose,
                    config=configured,
                )
                model = configured.model
        except Exception as exc:
            if request.data_classification in {"sensitive", "restricted"}:
                raise AITaskError(
                    "AI-unavailable: provider local autorizado indisponível."
                ) from exc
            output = self._fallback_output(request)
            provider = "fallback"
            model = "deterministic-template-v1"
            fallback_used = True
            sanitized_error = type(exc).__name__
        output = self._validate_output(request, output, actor)
        elapsed_ms = max(0, int((time.monotonic() - started) * 1000))
        interaction = AIInteractionModel(
            provider=provider,
            model=model,
            provider_model_identifier=f"{provider}:{model}" if model else provider,
            task_type=request.task_type,
            prompt_template_version=TASK_TEMPLATE_VERSIONS[request.task_type],
            structured_schema_version=request.schema_version,
            source_ids=request.source_ids,
            study_id=request.study_id,
            patient_id=request.patient_id,
            user_id=actor.id,
            institution_id=actor.institution_id,
            input_hash=canonical_sha256(self._minimized_payload(request)),
            output_hash=canonical_sha256(output),
            generated_at=datetime.now(UTC),
            latency_ms=elapsed_ms,
            status="generated",
            fallback_used=fallback_used,
            data_classification=request.data_classification,
            human_review_status="needs_review",
            sanitized_error_class=sanitized_error,
            usage_metadata={"raw_prompt_persisted": False, "cost_available": False},
            output_payload=output,
        )
        self.db.add(interaction)
        self.db.flush()
        AuditService(self.db).record_action(
            user=actor,
            action="ai.research.generate",
            resource_type="ai_interaction",
            resource_id=interaction.id,
            status="needs_review",
            details={
                "task_type": request.task_type,
                "provider": provider,
                "fallback_used": fallback_used,
                "data_classification": request.data_classification,
            },
        )
        return interaction

    def review(
        self,
        interaction_id: str,
        payload: AIInteractionReviewRequest,
        actor: UserModel,
    ) -> AIInteractionModel:
        interaction = self.db.get(AIInteractionModel, interaction_id)
        if interaction is None or interaction.institution_id != actor.institution_id:
            raise AITaskError("Interação de IA não encontrada.")
        if interaction.human_review_status != "needs_review":
            raise AITaskError("Interação de IA já revisada.")
        interaction.human_review_status = payload.decision
        interaction.status = payload.decision
        interaction.reviewed_by_user_id = actor.id
        interaction.reviewed_at = datetime.now(UTC)
        interaction.usage_metadata = {
            **(interaction.usage_metadata or {}),
            "review_note_hash": canonical_sha256(payload.note),
        }
        self.db.flush()
        AuditService(self.db).record_action(
            user=actor,
            action="ai.research.review",
            resource_type="ai_interaction",
            resource_id=interaction.id,
            status=payload.decision,
            details={"task_type": interaction.task_type},
        )
        return interaction

    def _authorize_context(self, request: AIRequestSchema, actor: UserModel) -> None:
        if request.study_id:
            study = self.db.get(ResearchStudyModel, request.study_id)
            if study is None or study.institution_id != actor.institution_id:
                raise AITaskError("Estudo não encontrado.")
        if request.patient_id and request.data_classification not in {"sensitive", "restricted"}:
            raise AITaskError("Dados de paciente exigem classificação sensitive/restricted.")
        for source_id in request.source_ids:
            source = self.db.get(EvidenceSourceModel, source_id)
            if source is None or source.institution_id != actor.institution_id:
                raise AITaskError("Fonte de evidência fora do escopo autorizado.")

    @staticmethod
    def _provider_for(request: AIRequestSchema, configured_provider: str) -> str:
        requested = set(request.allowed_providers or KNOWN_PROVIDERS)
        if requested - KNOWN_PROVIDERS:
            raise AITaskError("Provider não reconhecido na policy de IA.")
        if request.preferred_provider and request.preferred_provider not in KNOWN_PROVIDERS:
            raise AITaskError("Provider preferido inválido.")
        if request.data_classification in {"sensitive", "restricted"}:
            permitted = requested & {"fallback", "ollama"}
            if configured_provider == "ollama" and "ollama" in permitted:
                return "ollama"
            if "fallback" in permitted:
                return "fallback"
            raise AITaskError("Policy exige provider local para a classificação informada.")
        if request.preferred_provider and request.preferred_provider != configured_provider:
            if request.preferred_provider == "fallback" and "fallback" in requested:
                return "fallback"
        return configured_provider if configured_provider in requested else "fallback"

    @staticmethod
    def _system_instructions(task_type: str) -> str:
        return (
            "Retorne somente JSON válido. Você propõe um draft educacional; não execute "
            "coorte, não conte pacientes, não publique protocolo, não invente fonte ou código. "
            f"Task: {task_type}."
        )

    @staticmethod
    def _minimized_payload(request: AIRequestSchema) -> dict:
        serialized = json_compatible(request.input)
        if len(str(serialized)) > request.max_context:
            raise AITaskError("Contexto excede o limite autorizado.")
        return {
            "task_type": request.task_type,
            "purpose": request.purpose,
            "source_ids": request.source_ids,
            "input": serialized,
            "notice": "proposal_only_not_executed",
        }

    def _fallback_output(self, request: AIRequestSchema) -> dict:
        if request.task_type == "research_question_structuring":
            return {
                "proposal": {
                    "question": str(request.input.get("question") or "")[:1000],
                    "population": request.input.get("population"),
                    "exposure": request.input.get("exposure"),
                    "outcome": request.input.get("outcome"),
                },
                "unresolved_questions": [
                    "Confirmar conceitos terminológicos e janela temporal com revisão humana."
                ],
                "status": "proposal_only_not_executed",
            }
        if request.task_type == "cohort_draft":
            return {
                "definition": request.input.get("definition")
                or {"all": [{"criterion": "age", "operator": "gte", "value": 18}]},
                "unresolved_questions": ["Confirmar concept sets e fontes."],
                "status": "proposal_only_not_executed",
            }
        if request.task_type == "evidence_summary":
            return {
                "claims": [],
                "status": "insufficient_source_support",
                "source_ids": request.source_ids,
            }
        if request.task_type == "patient_journey_summary":
            return {
                "summary_items": [],
                "missing_context": ["Fallback não compõe narrativa clínica."],
                "source_event_ids": [],
                "status": "needs_review",
            }
        return {
            "summary_items": [],
            "unresolved_questions": ["Revisão humana necessária."],
            "status": "proposal_only_not_executed",
        }

    def _validate_output(
        self,
        request: AIRequestSchema,
        output: Any,
        actor: UserModel,
    ) -> dict:
        if not isinstance(output, dict):
            raise AITaskError("Saída de IA não atende ao schema estruturado.")
        if request.task_type == "cohort_draft":
            definition = output.get("definition")
            try:
                CohortDSLValidator(self.db, actor.institution_id).validate(definition)
            except CohortDSLValidationError as exc:
                raise AITaskError(f"Saída de IA contém cohort DSL inválida: {exc}") from exc
        if request.task_type == "evidence_summary":
            allowed = set(request.source_ids)
            for claim in output.get("claims", []):
                if not isinstance(claim, dict) or claim.get("source_id") not in allowed:
                    raise AITaskError("Resumo de evidência contém source_id não autorizado.")
        if request.task_type == "patient_journey_summary":
            if not isinstance(output.get("source_event_ids", []), list):
                raise AITaskError("Resumo de jornada sem eventos-fonte válidos.")
        return json_compatible(output)
