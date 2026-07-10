from __future__ import annotations

import time
from typing import Any

from sqlalchemy.orm import Session

from app.reports.schemas import (
    ReportEvidenceBundle,
    ReportNarrativeComposition,
    ReportNarrativeSchema,
)
from app.reports.templates import PROMPT_VERSIONS, prompt_for_report_type
from app.services.ai_settings import AIConfigurationError, AISettingsService

RESERVED_AI_OUTPUT_FIELDS = {
    "risk_level",
    "status",
    "blocked",
    "block",
    "severity",
    "dose",
    "daily_dose",
    "accumulated_dose",
    "duration",
    "rules_fired",
    "rule_id",
    "source",
    "sources",
    "source_id",
    "jurisdiction",
    "validation_status",
    "final_decision",
}


class AIReportComposer:
    def __init__(self, db: Session) -> None:
        self.db = db

    def compose(self, bundle: ReportEvidenceBundle) -> ReportNarrativeComposition:
        ai_service = AISettingsService(self.db)
        config = ai_service.runtime_config()
        prompt_version = PROMPT_VERSIONS.get(bundle.report_type, "report_generic_v0.8.0")
        start = time.perf_counter()
        if bundle.ai_context.allow_external_ai:
            try:
                raw = ai_service.complete_json(
                    system_instructions=prompt_for_report_type(bundle.report_type),
                    payload={
                        "prompt_version": prompt_version,
                        "evidence_bundle_hash": bundle.hash(),
                        "report_evidence_bundle": self._ai_safe_bundle(bundle),
                    },
                    purpose=f"report_{bundle.report_type}",
                    config=config,
                )
                self._assert_no_reserved_fields(raw)
                narrative = ReportNarrativeSchema.model_validate(raw)
                self._assert_valid_sources(bundle, narrative)
                return ReportNarrativeComposition(
                    narrative=narrative,
                    provider=config.provider,
                    model=config.model,
                    prompt_version=prompt_version,
                    ai_used=True,
                    fallback_used=False,
                    status="ai_generated",
                    response_time_ms=self._elapsed_ms(start),
                )
            except Exception as exc:  # pragma: no cover - defensive provider fallback
                fallback = self._fallback_narrative(
                    bundle,
                    warning=(
                        "Narrativa externa indisponivel ou invalida; "
                        "fallback deterministico acionado."
                    ),
                )
                return ReportNarrativeComposition(
                    narrative=fallback,
                    provider=config.provider,
                    model=config.model,
                    prompt_version=prompt_version,
                    ai_used=False,
                    fallback_used=True,
                    status="fallback_after_ai_error",
                    response_time_ms=self._elapsed_ms(start),
                    error_summary=self._safe_error(exc),
                )

        fallback = self._fallback_narrative(
            bundle,
            warning="Chamadas externas de IA desabilitadas ou provider fallback ativo.",
        )
        return ReportNarrativeComposition(
            narrative=fallback,
            provider=config.provider,
            model=config.model,
            prompt_version=prompt_version,
            ai_used=False,
            fallback_used=True,
            status="fallback",
            response_time_ms=self._elapsed_ms(start),
        )

    def _fallback_narrative(
        self,
        bundle: ReportEvidenceBundle,
        *,
        warning: str,
    ) -> ReportNarrativeSchema:
        if bundle.prescription_result is not None:
            prescription = bundle.prescription_result
            alert_count = len(prescription.alerts)
            missing = bundle.patient_context.missing_data if bundle.patient_context else []
            guidance_parts = [
                (
                    "Siga a orientacao do profissional responsavel e nao altere dose "
                    "por conta propria."
                ),
            ]
            if prescription.alerts:
                guidance_parts.append(
                    "Ha cuidados registrados para esta prescricao; confirme sinais "
                    "de alerta e monitoramento."
                )
            if any("activity" in alert.code.lower() for alert in prescription.alerts):
                guidance_parts.append(
                    "Evite dirigir, operar maquinas ou trabalhar em altura ate saber "
                    "como seu corpo reage."
                )
            if bundle.metadata.get("patient_counseling"):
                guidance_parts.extend(
                    bundle.metadata["patient_counseling"].get("orientation_points", [])[:3]
                )
            return ReportNarrativeSchema(
                executive_summary=(
                    f"Checagem registrada para {prescription.medication_name}: "
                    f"status {prescription.status}, risco {prescription.risk_level}, "
                    f"{alert_count} alerta(s)."
                ),
                professional_explanation=(
                    "A conclusao foi produzida por regras deterministicas do Prescripta. "
                    "A narrativa apenas organiza os achados ja registrados no bundle."
                ),
                patient_guidance=" ".join(guidance_parts),
                evidence_summary=(
                    "Evidencias usadas: "
                    + ", ".join(source.source_id for source in bundle.sources)
                    if bundle.sources
                    else "Nao ha fonte adicional cadastrada no bundle."
                ),
                missing_data_note=(
                    "Dados faltantes: " + ", ".join(missing)
                    if missing
                    else "Nao foram identificados dados faltantes principais."
                ),
                functional_context_note=self._functional_note(bundle),
                safety_counseling_summary=self._safety_summary(bundle),
                limitations_note=(
                    "Analise demonstrativa: nao substitui bula validada, protocolo local "
                    "ou avaliacao profissional."
                ),
                human_review_note=(
                    "Revisao humana necessaria."
                    if prescription.status != "liberado" or prescription.risk_level != "baixo"
                    else "Sem bloqueio pelas regras cadastradas; manter decisao profissional."
                ),
                source_note=self._source_note(bundle),
                confidence=0.62,
                requires_human_review=(
                    prescription.status != "liberado" or prescription.risk_level != "baixo"
                ),
                warnings=[warning],
                cited_source_ids=[source.source_id for source in bundle.sources],
            )
        if bundle.reconciliation_result is not None:
            summary = bundle.reconciliation_result.get("summary", {})
            return ReportNarrativeSchema(
                executive_summary=(
                    f"Reconciliação clinica do lote #{bundle.metadata.get('batch_id')}: "
                    f"{summary.get('total', 0)} item(ns) avaliados."
                ),
                reconciliation_summary=(
                    "Itens novos, duplicados, conflitos e decisoes foram mantidos conforme "
                    "a reconciliacao registrada. A IA nao altera aceitacao ou rejeicao."
                ),
                limitations_note="Importacao assistida depende de revisao humana e consentimento.",
                human_review_note="Conflitos e pendencias exigem revisor responsavel.",
                source_note=self._source_note(bundle),
                confidence=0.6,
                requires_human_review=True,
                warnings=[warning],
                cited_source_ids=[source.source_id for source in bundle.sources],
            )
        if bundle.audit_result is not None:
            return ReportNarrativeSchema(
                executive_summary=(
                    "Relatorio de auditoria com "
                    f"{bundle.audit_result.get('total_events', 0)} evento(s)."
                ),
                professional_explanation=(
                    "Eventos foram listados conforme filtros aplicados, preservando metadados "
                    "necessarios e omitindo segredos."
                ),
                limitations_note=(
                    "Auditoria reflete os eventos registrados ate a geracao do relatorio."
                ),
                human_review_note="Eventos criticos devem ser revisados por perfil autorizado.",
                source_note="Fonte: trilha de auditoria interna do Prescripta.",
                confidence=0.7,
                requires_human_review=False,
                warnings=[warning],
            )
        return ReportNarrativeSchema(
            executive_summary="Relatorio gerado a partir de bundle controlado.",
            limitations_note="Sem dados clinicos suficientes para narrativa detalhada.",
            warnings=[warning],
        )

    def _functional_note(self, bundle: ReportEvidenceBundle) -> str:
        profile = bundle.patient_context.functional_profile if bundle.patient_context else []
        if not profile:
            return "Perfil funcional ausente ou incompleto."
        return "Perfil funcional considerado: " + ", ".join(profile) + "."

    def _safety_summary(self, bundle: ReportEvidenceBundle) -> str:
        counseling = bundle.metadata.get("patient_counseling") if bundle.metadata else None
        if not counseling:
            return "Resumo pratico de seguranca nao disponivel para este bundle."
        points = counseling.get("orientation_points", [])
        red_flags = counseling.get("red_flags", [])
        text = "Orientacoes principais: " + ", ".join(points[:4]) if points else ""
        if red_flags:
            text = f"{text} Sinais de alerta: {', '.join(red_flags[:4])}."
        return text or "Resumo pratico de seguranca sem itens principais."

    def _source_note(self, bundle: ReportEvidenceBundle) -> str:
        if not bundle.sources:
            return "Sem fontes adicionais cadastradas."
        return "; ".join(
            (
                f"{source.source_id}: {source.source_name} "
                f"[{source.jurisdiction}, {source.validation_status}]"
            )
            for source in bundle.sources
        )

    def _assert_no_reserved_fields(self, raw: dict[str, Any]) -> None:
        invalid = RESERVED_AI_OUTPUT_FIELDS.intersection(raw)
        if invalid:
            raise AIConfigurationError(
                "Resposta de IA tentou retornar campo reservado: " + ", ".join(sorted(invalid))
            )

    def _assert_valid_sources(
        self,
        bundle: ReportEvidenceBundle,
        narrative: ReportNarrativeSchema,
    ) -> None:
        valid_source_ids = {source.source_id for source in bundle.sources}
        invalid = [
            source_id
            for source_id in narrative.cited_source_ids
            if source_id not in valid_source_ids
        ]
        if invalid:
            raise AIConfigurationError(
                "Resposta de IA citou fonte inexistente: " + ", ".join(invalid)
            )

    def _ai_safe_bundle(self, bundle: ReportEvidenceBundle) -> dict[str, Any]:
        payload = bundle.model_dump(mode="json")
        patient_context = payload.get("patient_context")
        if isinstance(patient_context, dict):
            reference = str(patient_context.get("patient_reference") or "Paciente")
            patient_id = str(
                bundle.metadata.get("audit_id") or bundle.metadata.get("batch_id") or "0"
            )
            if not reference.startswith("Paciente #"):
                patient_context["patient_reference"] = f"Paciente #P-{patient_id.zfill(5)}"
        metadata = payload.get("metadata")
        if isinstance(metadata, dict):
            for key in ("user_name", "user_email", "patient_name", "phone", "email", "document"):
                metadata.pop(key, None)
        ai_context = payload.get("ai_context")
        if isinstance(ai_context, dict):
            ai_context["send_identifiable_data"] = False
        return payload

    def _elapsed_ms(self, start: float) -> int:
        return int((time.perf_counter() - start) * 1000)

    def _safe_error(self, exc: Exception) -> str:
        text = str(exc) or type(exc).__name__
        return text[:300]
