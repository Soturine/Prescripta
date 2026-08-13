from __future__ import annotations

import time
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import (
    AIInteractionModel,
    EvidenceSourceModel,
    PatientClinicalTimelineEventModel,
    PatientModel,
    ResearchStudyModel,
    TerminologyConceptModel,
    TerminologyReleaseModel,
    UserModel,
)
from app.schemas.ai_task_schema import AIInteractionReviewRequest, AIRequestSchema
from app.schemas.research_schema import AnalysisPlanCreate, CohortDefinitionCreate
from app.services.ai_settings import AISettingsService
from app.services.audit_service import AuditService
from app.services.bounded_numeric_scanner import (
    NumericScanBudgetExceeded,
    scan_ascii_numbers,
)
from app.services.canonical_json import canonical_sha256, json_compatible
from app.services.cohort_dsl import CohortDSLValidationError, CohortDSLValidator
from app.services.research_analysis_service import ResearchAnalysisService
from app.services.research_service import ResearchService

TASK_TEMPLATE_VERSIONS = {
    "clinical_decision_explanation": "clinical-explanation-v1",
    "research_question_structuring": "research-question-v1",
    "protocol_completeness_review": "protocol-completeness-v1",
    "study_protocol_draft": "study-protocol-draft-v2",
    "concept_set_suggestion": "concept-set-suggestion-v2",
    "cohort_drafting": "cohort-draft-v1",
    "analysis_plan_draft": "analysis-plan-draft-v1",
    "results_explanation": "results-explanation-v1",
    "cohort_draft": "cohort-draft-v1",
    "evidence_summary": "evidence-summary-v1",
    "evidence_extraction": "evidence-extraction-v2",
    "evidence_synthesis": "evidence-synthesis-v2",
    "patient_journey_summary": "patient-journey-v1",
    "data_quality_explanation": "data-quality-explanation-v1",
    "comparative_analysis_interpretation": "comparative-interpretation-v2",
    "causal_methods_checklist": "causal-methods-checklist-v2",
}
KNOWN_PROVIDERS = {"fallback", "openai", "gemini", "ollama", "openai_compatible"}
OUTPUT_CONTRACTS = {
    "research_question_structuring": {
        "required": {"proposal", "unresolved_questions", "status"},
        "allowed": {"proposal", "unresolved_questions", "status"},
    },
    "cohort_draft": {
        "required": {"definition", "unresolved_questions", "status"},
        "allowed": {"definition", "unresolved_questions", "status"},
    },
    "cohort_drafting": {
        "required": {"definition", "unresolved_questions", "status"},
        "allowed": {"definition", "unresolved_questions", "status"},
    },
    "analysis_plan_draft": {
        "required": {"plan", "unresolved_questions", "status"},
        "allowed": {"plan", "unresolved_questions", "status"},
    },
    "evidence_summary": {
        "required": {"claims", "status", "source_ids"},
        "allowed": {"claims", "status", "source_ids"},
    },
    "patient_journey_summary": {
        "required": {"summary_items", "missing_context", "source_event_ids", "status"},
        "allowed": {"summary_items", "missing_context", "source_event_ids", "status"},
    },
    "concept_set_suggestion": {
        "required": {"suggestions", "unresolved_questions", "status"},
        "allowed": {"suggestions", "unresolved_questions", "status"},
    },
    "evidence_extraction": {
        "required": {"claims", "status", "source_ids"},
        "allowed": {"claims", "status", "source_ids"},
    },
    "evidence_synthesis": {
        "required": {"claims", "status", "source_ids", "gaps"},
        "allowed": {"claims", "status", "source_ids", "gaps"},
    },
    "comparative_analysis_interpretation": {
        "required": {"narrative_items", "numeric_refs", "limitations", "status"},
        "allowed": {"narrative_items", "numeric_refs", "limitations", "status"},
    },
    "causal_methods_checklist": {
        "required": {"assumptions", "missing_questions", "status"},
        "allowed": {"assumptions", "missing_questions", "status"},
    },
}
DEFAULT_OUTPUT_CONTRACT = {
    "required": {"summary_items", "unresolved_questions", "status"},
    "allowed": {"summary_items", "unresolved_questions", "status"},
}


class AITaskError(ValueError):
    pass


class AITaskRouter:
    def __init__(self, db: Session) -> None:
        self.db = db

    def execute(self, request: AIRequestSchema, actor: UserModel) -> AIInteractionModel:
        self._authorize_context(request, actor)
        configured = AISettingsService(self.db).runtime_config()
        provider = self._provider_for(request, configured.provider)
        if request.allowed_models and configured.model not in request.allowed_models:
            if provider != "fallback":
                raise AITaskError("Modelo configurado não pertence à allowlist da tarefa.")
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
            usage_metadata={
                "raw_prompt_persisted": False,
                "cost_available": False,
                "max_output_tokens": request.max_output_tokens,
                "cost_budget_usd": request.cost_budget_usd,
                "policy_version": request.policy_version,
                "source_grounding_required": request.source_grounding_required,
            },
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
                "policy_version": request.policy_version,
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
        if payload.decision == "accepted_as_draft":
            try:
                created = self._accept_as_draft(interaction, actor)
            except ValueError as exc:
                raise AITaskError(f"Proposta não pôde criar draft: {exc}") from exc
            interaction.usage_metadata = {
                **interaction.usage_metadata,
                "accepted_draft": created,
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
        if request.patient_id:
            patient = self.db.get(PatientModel, request.patient_id)
            if patient is None or patient.institution_id != actor.institution_id:
                raise AITaskError("Paciente fora do escopo autorizado.")
            synthetic_journey = (
                request.task_type == "patient_journey_summary"
                and request.data_classification == "synthetic"
                and request.study_id
                and self._synthetic_journey_sources(request.patient_id, actor.institution_id)
            )
            if not synthetic_journey and request.data_classification not in {
                "sensitive",
                "restricted",
            }:
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
        if request.preferred_provider and request.preferred_provider not in requested:
            raise AITaskError("Provider preferido negado pela policy da tarefa.")
        if request.data_classification in {"sensitive", "restricted"} or request.local_only:
            permitted = requested & {"fallback", "ollama"}
            if configured_provider == "ollama" and "ollama" in permitted:
                return "ollama"
            if "fallback" in permitted:
                return "fallback"
            raise AITaskError("Policy exige provider local para a classificação informada.")
        if request.preferred_provider == "fallback":
            return "fallback"
        if configured_provider in requested:
            return configured_provider
        if "fallback" in requested:
            return "fallback"
        raise AITaskError("Provider configurado não é permitido e fallback está desabilitado.")

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
            "policy_version": request.policy_version,
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
        if request.task_type in {"cohort_draft", "cohort_drafting"}:
            return {
                "definition": request.input.get("definition")
                or {"all": [{"criterion": "age", "operator": "gte", "value": 18}]},
                "unresolved_questions": ["Confirmar concept sets e fontes."],
                "status": "proposal_only_not_executed",
            }
        if request.task_type == "analysis_plan_draft":
            return {
                "plan": request.input.get("plan") or {},
                "unresolved_questions": ["Confirmar métodos, variáveis e outputs."],
                "status": "proposal_only_not_executed",
            }
        if request.task_type == "evidence_summary":
            return {
                "claims": [],
                "status": "insufficient_source_support",
                "source_ids": request.source_ids,
            }
        if request.task_type == "concept_set_suggestion":
            return {
                "suggestions": [],
                "unresolved_questions": [
                    "Nenhum conceito é proposto sem lookup terminológico canônico."
                ],
                "status": "proposal_only_not_executed",
            }
        if request.task_type == "evidence_extraction":
            return {
                "claims": [],
                "status": "insufficient_source_support",
                "source_ids": request.source_ids,
            }
        if request.task_type == "evidence_synthesis":
            return {
                "claims": [],
                "gaps": ["Extrações suportadas insuficientes para síntese."],
                "status": "insufficient_source_support",
                "source_ids": request.source_ids,
            }
        if request.task_type == "comparative_analysis_interpretation":
            return {
                "narrative_items": [],
                "numeric_refs": request.input.get("numeric_refs", []),
                "limitations": [
                    "Fallback não interpreta estimativas; revisão humana necessária."
                ],
                "status": "proposal_only_not_executed",
            }
        if request.task_type == "causal_methods_checklist":
            return {
                "assumptions": request.input.get("assumptions", {}),
                "missing_questions": ["Revisão metodológica humana necessária."],
                "status": "proposal_only_not_executed",
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
        v2_tasks = {
            "study_protocol_draft",
            "concept_set_suggestion",
            "evidence_extraction",
            "evidence_synthesis",
            "comparative_analysis_interpretation",
            "causal_methods_checklist",
        }
        if request.schema_version != "v1" and not (
            request.schema_version == "v2" and request.task_type in v2_tasks
        ):
            raise AITaskError("Versão de schema não suportada para a tarefa de IA.")
        contract = OUTPUT_CONTRACTS.get(request.task_type, DEFAULT_OUTPUT_CONTRACT)
        keys = set(output)
        missing = contract["required"] - keys
        unsupported = keys - contract["allowed"]
        if missing:
            raise AITaskError(
                "Saída de IA omitiu campos obrigatórios: " + ", ".join(sorted(missing)) + "."
            )
        if unsupported:
            raise AITaskError(
                "Saída de IA contém campos não suportados: " + ", ".join(sorted(unsupported)) + "."
            )
        status = output.get("status")
        if not isinstance(status, str) or not status:
            raise AITaskError("Saída de IA contém status inválido.")
        if request.task_type in {"cohort_draft", "cohort_drafting"}:
            definition = output.get("definition")
            try:
                CohortDSLValidator(self.db, actor.institution_id).validate(definition)
            except CohortDSLValidationError as exc:
                raise AITaskError(f"Saída de IA contém cohort DSL inválida: {exc}") from exc
        if request.task_type == "analysis_plan_draft":
            try:
                AnalysisPlanCreate.model_validate(output.get("plan"))
            except ValueError as exc:
                raise AITaskError("Saída de IA contém plano de análise inválido.") from exc
        if request.task_type in {"evidence_summary", "evidence_extraction", "evidence_synthesis"}:
            allowed = set(request.source_ids)
            claims = output.get("claims")
            if not isinstance(claims, list):
                raise AITaskError("Resumo de evidência sem lista de claims válida.")
            if output.get("source_ids") != request.source_ids:
                raise AITaskError("Resumo de evidência alterou as fontes autorizadas.")
            for claim in claims:
                if not isinstance(claim, dict) or claim.get("source_id") not in allowed:
                    raise AITaskError("Resumo de evidência contém source_id não autorizado.")
                if request.task_type == "evidence_extraction" and (
                    not claim.get("locator")
                    or claim.get("support_status") not in {"supported", "not_found"}
                ):
                    raise AITaskError("Extração exige locator e support_status.")
        if request.task_type == "concept_set_suggestion":
            for suggestion in output.get("suggestions", []):
                if not isinstance(suggestion, dict) or not suggestion.get("concept_id"):
                    raise AITaskError("Sugestão de conceito sem concept_id canônico.")
                concept = self.db.get(TerminologyConceptModel, suggestion["concept_id"])
                release = (
                    self.db.get(TerminologyReleaseModel, concept.release_id)
                    if concept
                    else None
                )
                if (
                    concept is None
                    or release is None
                    or concept.institution_id != actor.institution_id
                    or release.institution_id != actor.institution_id
                    or concept.invalid_reason is not None
                    or release.status not in {"active", "imported"}
                ):
                    raise AITaskError("unsupported_concept")
        if request.task_type == "comparative_analysis_interpretation":
            expected_refs = request.input.get("numeric_refs", [])
            if output.get("numeric_refs") != expected_refs:
                raise AITaskError("Interpretação alterou numeric refs determinísticos.")
            allowed_numbers = {str(item) for item in expected_refs}
            try:
                narrative_numbers = {
                    token
                    for item in output.get("narrative_items", [])
                    for token in scan_ascii_numbers(str(item))
                }
            except NumericScanBudgetExceeded as exc:
                raise AITaskError("InterpretaÃ§Ã£o excedeu o budget numÃ©rico.") from exc
            if narrative_numbers - allowed_numbers:
                raise AITaskError("Interpretação contém número não fornecido pelo backend.")
        if request.task_type == "patient_journey_summary":
            source_event_ids = output.get("source_event_ids", [])
            if not isinstance(source_event_ids, list):
                raise AITaskError("Resumo de jornada sem eventos-fonte válidos.")
            allowed_event_ids = {
                str(item.get("event_ref") or item.get("id"))
                for item in request.input.get("events", [])
                if isinstance(item, dict)
            }
            if not set(map(str, source_event_ids)) <= allowed_event_ids:
                raise AITaskError("Resumo de jornada citou evento fora do contexto autorizado.")
        if request.task_type == "results_explanation":
            allowed_numbers = self._numbers(request.input)
            if not self._numbers(output) <= allowed_numbers:
                raise AITaskError("Explicação de resultados inventou valor numérico.")
        return json_compatible(output)

    def _accept_as_draft(self, interaction: AIInteractionModel, actor: UserModel) -> dict:
        if interaction.task_type in {"cohort_draft", "cohort_drafting"}:
            version = ResearchService(self.db).create_cohort_version(
                interaction.study_id or "",
                CohortDefinitionCreate(
                    name=f"Copilot draft {interaction.id[:8]}",
                    definition=interaction.output_payload["definition"],
                ),
                actor,
            )
            return {
                "resource_type": "cohort_definition_version",
                "id": version.id,
                "status": "draft",
            }
        if interaction.task_type == "analysis_plan_draft":
            plan = ResearchAnalysisService(self.db).create_plan(
                interaction.study_id or "",
                AnalysisPlanCreate.model_validate(interaction.output_payload["plan"]),
                actor,
            )
            return {"resource_type": "analysis_plan", "id": plan.id, "status": "draft"}
        return {"resource_type": "ai_proposal", "id": interaction.id, "status": "draft"}

    def _synthetic_journey_sources(self, patient_id: int, institution_id: str) -> bool:
        events = list(
            self.db.scalars(
                select(PatientClinicalTimelineEventModel).where(
                    PatientClinicalTimelineEventModel.patient_id == patient_id,
                    PatientClinicalTimelineEventModel.institution_id == institution_id,
                )
            )
        )
        return bool(events) and all(
            event.source_type == "synthetic_fixture"
            and (event.provenance or {}).get("demo_only") is True
            for event in events
        )

    @staticmethod
    def _numbers(value: Any) -> set[str]:
        found: set[str] = set()
        if isinstance(value, bool):
            return found
        if isinstance(value, (int, float)):
            found.add(str(value))
        elif isinstance(value, str):
            try:
                found.update(scan_ascii_numbers(value))
            except NumericScanBudgetExceeded as exc:
                raise AITaskError("ConteÃºdo excedeu o budget numÃ©rico.") from exc
        elif isinstance(value, dict):
            for item in value.values():
                found |= AITaskRouter._numbers(item)
        elif isinstance(value, list):
            for item in value:
                found |= AITaskRouter._numbers(item)
        return found
