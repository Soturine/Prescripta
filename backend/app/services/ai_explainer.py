from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from sqlalchemy.orm import Session

from app.core.config import Settings, settings
from app.schemas.prescription_schema import (
    AlertRead,
    PrescriptionExplainRequest,
    PrescriptionExplainResponse,
)
from app.services.ai_settings import AIConfigurationError, AISettingsService

EDUCATIONAL_NOTICE = (
    "Resposta gerada como apoio educacional. Ela não substitui avaliação clínica, "
    "protocolos institucionais ou decisão profissional."
)

ALERT_EXPLANATIONS = {
    "ALLERGY_BLOCK": (
        "Há compatibilidade entre alergia registrada e medicamento, princípio ativo ou classe."
    ),
    "MAX_DAILY_DOSE_EXCEEDED": "A dose diária calculada ultrapassa o limite cadastrado.",
    "DRUG_INTERACTION": "Existe interação entre medicamento novo e uso contínuo.",
    "POLYPHARMACY": "O paciente usa cinco ou mais medicamentos contínuos.",
    "AGE_RISK": "A idade aumenta a necessidade de revisão cuidadosa.",
    "CONTRAINDICATION": "Uma comorbidade coincide com contraindicação cadastrada.",
    "INVALID_ROUTE": "A via informada não consta nas vias permitidas do medicamento.",
    "CONTINUOUS_USE_REVIEW": "Uso contínuo ou prolongado exige plano de revisão.",
    "MONITORING_REQUIRED": "O medicamento possui monitoramento cadastrado.",
    "PROLONGED_USE_REVIEW": "A duração sugere revisão por uso prolongado.",
    "RENAL_ELIMINATION_REVIEW": "O perfil ADME indica eliminação renal relevante.",
    "HEPATIC_METABOLISM_REVIEW": "O perfil ADME indica metabolismo hepático relevante.",
    "SEROTONERGIC_REVIEW": "Há sobreposição de fatores serotoninérgicos.",
    "IMAO_INTERACTION_REVIEW": "Uso de IMAO exige revisão de interação em fonte validada.",
    "SEIZURE_THRESHOLD_REVIEW": "Histórico convulsivo coincide com cautela cadastrada.",
    "SEDATION_REVIEW": "Há cautela de sedação/depressor do SNC.",
    "RIFAMYCIN_HORMONAL_CONTRACEPTIVE_REVIEW": (
        "Regra para rifampicina/rifabutina e contraceptivo hormonal exige fonte validada."
    ),
    "REPRODUCTIVE_REVIEW": "Fator gestacional/lactacional/reprodutivo exige revisão.",
}

ALERT_QUESTIONS = {
    "ALLERGY_BLOCK": "Existe alternativa terapêutica sem relação com a alergia registrada?",
    "MAX_DAILY_DOSE_EXCEEDED": (
        "A dose e a frequência podem ser ajustadas para ficar dentro do limite diário?"
    ),
    "DRUG_INTERACTION": "A associação medicamentosa é necessária ou há substituição mais segura?",
    "POLYPHARMACY": "Há medicamentos contínuos duplicados, obsoletos ou sem indicação atual?",
    "AGE_RISK": "A idade exige dose inicial menor, monitoramento adicional ou ajuste de intervalo?",
    "CONTRAINDICATION": "A comorbidade contraindica o uso ou exige monitoramento?",
    "INVALID_ROUTE": "A via de administração deve ser corrigida antes de prosseguir?",
    "MONITORING_REQUIRED": (
        "Quais exames, sinais clínicos ou prazos de retorno devem ser definidos?"
    ),
    "RENAL_ELIMINATION_REVIEW": "A função renal recente permite esta dose e intervalo?",
    "HEPATIC_METABOLISM_REVIEW": "A função hepática recente muda dose, intervalo ou alternativa?",
    "SEROTONERGIC_REVIEW": "A associação serotoninérgica é necessária e monitorável?",
    "IMAO_INTERACTION_REVIEW": "Há intervalo seguro e fonte validada para esta associação?",
    "SEIZURE_THRESHOLD_REVIEW": "O histórico convulsivo muda escolha ou monitoramento?",
    "RIFAMYCIN_HORMONAL_CONTRACEPTIVE_REVIEW": (
        "A paciente precisa de orientação contraceptiva adicional validada?"
    ),
}

SYSTEM_INSTRUCTIONS = """
Você é uma camada explicativa educacional do Prescripta.
Explique apenas alertas já gerados por regras determinísticas.
Não libere prescrição, não reduza risco, não calcule dose crítica e não substitua revisão humana.
Priorize fontes brasileiras quando o contexto for BR.
Trate fontes internacionais como apoio secundário.
Informe quando uma evidência for externa, educacional ou pendente de revisão.
Responda em JSON com as chaves: simple_explanation, technical_summary,
review_questions, educational_notice.
Use português claro, técnico quando necessário, e preserve todo bloqueio crítico.
"""


@dataclass(frozen=True)
class ExplanationDraft:
    simple_explanation: str
    technical_summary: str
    review_questions: list[str]
    educational_notice: str = EDUCATIONAL_NOTICE


class AIExplainer:
    def __init__(self, app_settings: Settings = settings, db: Session | None = None) -> None:
        self.settings = app_settings
        self.db = db

    def explain(
        self,
        payload: PrescriptionExplainRequest,
        *,
        requester_role: str,
    ) -> PrescriptionExplainResponse:
        fallback_reason = ""
        if self.db is not None:
            ai_service = AISettingsService(self.db, self.settings)
            config = ai_service.runtime_config()
            if config.enable_external_calls:
                try:
                    raw = ai_service.complete_json(
                        system_instructions=SYSTEM_INSTRUCTIONS,
                        payload=self._build_context(payload, requester_role),
                        purpose="prescription_explanation",
                        config=config,
                    )
                    draft = self._draft_from_json(raw)
                    return self._response(
                        payload=payload,
                        provider=config.provider,
                        model=config.model,
                        draft=draft,
                        used_fallback=False,
                    )
                except Exception as exc:  # pragma: no cover - defensive runtime fallback
                    fallback_reason = (
                        "IA externa indisponível; fallback local acionado "
                        f"({type(exc).__name__})."
                    )
            elif config.provider != "fallback":
                fallback_reason = "Chamadas externas de IA desabilitadas; fallback local acionado."
        elif self.settings.ai_provider.strip().lower() != "fallback":
            fallback_reason = "Configuração persistida indisponível; fallback local acionado."

        draft = self._fallback_explanation(
            payload,
            requester_role,
            fallback_reason=fallback_reason,
        )
        return self._response(
            payload=payload,
            provider="fallback",
            model=None,
            draft=draft,
            used_fallback=True,
        )

    def _draft_from_json(self, raw: dict) -> ExplanationDraft:
        draft = ExplanationDraft(
            simple_explanation=str(raw.get("simple_explanation") or "").strip(),
            technical_summary=str(raw.get("technical_summary") or "").strip(),
            review_questions=self._coerce_questions(raw.get("review_questions")),
            educational_notice=str(raw.get("educational_notice") or EDUCATIONAL_NOTICE),
        )
        if not draft.simple_explanation or not draft.technical_summary:
            raise AIConfigurationError("Resposta de IA incompleta.")
        if not draft.review_questions:
            raise AIConfigurationError("Resposta de IA sem perguntas de revisão.")
        return draft

    def _fallback_explanation(
        self,
        payload: PrescriptionExplainRequest,
        requester_role: str,
        *,
        fallback_reason: str = "",
    ) -> ExplanationDraft:
        daily_total = payload.dose_mg * payload.frequency_per_day
        cumulative = daily_total * payload.duration_days if payload.duration_days else None
        alerts_text = (
            " ".join(self._plain_alert_line(alert) for alert in payload.alerts)
            if payload.alerts
            else "Nenhum alerta foi gerado pelas regras cadastradas."
        )

        if payload.status == "bloqueado":
            opening = "A prescrição foi bloqueada porque há pelo menos um risco crítico."
        elif payload.human_review_required:
            opening = "A prescrição exige atenção e revisão humana antes da decisão."
        else:
            opening = "A checagem não encontrou risco relevante nas regras cadastradas."

        cumulative_text = f"Dose acumulada estimada: {cumulative:g} mg. " if cumulative else ""
        technical_summary = (
            f"Paciente: {payload.patient.name}. Medicamento: {payload.medication.brand_name} "
            f"({payload.medication.active_ingredient}). Dose diária calculada: "
            f"{daily_total:g} mg. {cumulative_text}"
            f"Status determinístico: {payload.status}. Risco: {payload.risk_level}. "
            f"Compatibilidade: {payload.compatibility.get('level', 'não calculada')}. "
            f"Perfil solicitante: {requester_role}. Alertas avaliados: {len(payload.alerts)}."
        )
        if payload.rag_evidence:
            sources = ", ".join(
                self._rag_source_label(item)
                for item in payload.rag_evidence[:3]
                if item.get("source")
            )
            technical_summary = (
                f"{technical_summary} Contexto RAG interno com fonte/jurisdição: {sources}."
            )
            has_external_source = any(
                str(item.get("jurisdiction", "")).upper() not in {"BR", "GLOBAL"}
                for item in payload.rag_evidence
            )
            if has_external_source:
                technical_summary = (
                    f"{technical_summary} Fontes internacionais são apoio secundário "
                    "e não substituem a prioridade brasileira Anvisa/DCB no contexto BR."
                )
        mechanism = payload.dose_summary.get("mechanism_profile") or {}
        exposure = payload.dose_summary.get("exposure_plan") or {}
        if mechanism:
            technical_summary = (
                f"{technical_summary} Perfil ADME/mecanismo: "
                f"metabolização={mechanism.get('metabolism_organs')}, "
                f"eliminação={mechanism.get('elimination_organs')}, "
                f"renal={mechanism.get('renal_elimination_level')}, "
                f"hepático={mechanism.get('hepatic_metabolism_level')}."
            )
        if payload.dose_summary.get("monitoring_required"):
            technical_summary = (
                f"{technical_summary} Monitoramento cadastrado: "
                f"{payload.dose_summary.get('monitoring_notes') or 'revisão profissional'}."
            )
        if exposure.get("has_missing_duration_for_cumulative_dose"):
            technical_summary = (
                f"{technical_summary} Duração ausente limita interpretação da exposição acumulada."
            )
        if fallback_reason:
            technical_summary = f"{technical_summary} {fallback_reason}"

        questions = [
            ALERT_QUESTIONS.get(alert.code, f"Como revisar o alerta {alert.title}?")
            for alert in payload.alerts
        ]
        if payload.compatibility.get("review_required"):
            questions.append("Quais dados do perfil clínico ainda precisam ser confirmados?")
        if payload.alternatives:
            questions.append("Alguma alternativa avaliada apresenta menor risco?")
        if not questions:
            questions = [
                "A prescrição foi revisada conforme protocolo local?",
                "Há novas alergias, comorbidades ou medicamentos contínuos não cadastrados?",
            ]

        return ExplanationDraft(
            simple_explanation=f"{opening} {alerts_text}",
            technical_summary=technical_summary,
            review_questions=questions[:6],
        )

    def _plain_alert_line(self, alert: AlertRead) -> str:
        explanation = ALERT_EXPLANATIONS.get(alert.code, alert.description)
        return f"{alert.title}: {explanation} Recomendação cadastrada: {alert.recommendation}"

    def _build_context(self, payload: PrescriptionExplainRequest, requester_role: str) -> dict:
        patient = payload.patient.model_dump()
        patient["name"] = f"Paciente #{payload.patient.id or 'sem_id'}"
        patient["birth_date"] = None
        return {
            "patient": patient,
            "medication": payload.medication.model_dump(),
            "dose_mg": payload.dose_mg,
            "frequency_per_day": payload.frequency_per_day,
            "route": payload.route,
            "status": payload.status,
            "risk_level": payload.risk_level,
            "recommendation": payload.recommendation,
            "human_review_required": payload.human_review_required,
            "alerts": [alert.model_dump() for alert in payload.alerts],
            "dose_summary": payload.dose_summary,
            "compatibility": payload.compatibility,
            "patient_factors_considered": payload.patient_factors_considered,
            "medication_factors_considered": payload.medication_factors_considered,
            "patient_knowledge_bundle": self._minimized_patient_bundle(
                payload.patient_knowledge_bundle
            ),
            "rag_evidence": payload.rag_evidence,
            "clinical_context_graph": payload.clinical_context_graph,
            "alternatives": payload.alternatives,
            "requester_role": requester_role,
        }

    def _minimized_patient_bundle(self, bundle: dict) -> dict:
        if not bundle:
            return {}
        safe = dict(bundle)
        structured = dict(safe.get("structured_profile") or {})
        structured.pop("name", None)
        safe["structured_profile"] = structured
        safe.pop("identifiers", None)
        safe["send_identifiable_data"] = False
        return safe

    def _coerce_questions(self, raw_questions: Any) -> list[str]:
        if not isinstance(raw_questions, list):
            return []
        questions = [str(question).strip() for question in raw_questions if str(question).strip()]
        return questions[:6]

    def _response(
        self,
        *,
        payload: PrescriptionExplainRequest,
        provider: str,
        model: str | None,
        draft: ExplanationDraft,
        used_fallback: bool,
    ) -> PrescriptionExplainResponse:
        critical_alert_codes = [
            alert.code for alert in payload.alerts if alert.severity == "critico"
        ]
        how_to_explain = None
        if payload.patient_counseling and payload.patient_counseling.orientation_points:
            how_to_explain = " ".join(payload.patient_counseling.orientation_points[:4])
        return PrescriptionExplainResponse(
            provider=provider,
            model=model,
            used_fallback=used_fallback,
            simple_explanation=draft.simple_explanation.strip(),
            technical_summary=draft.technical_summary.strip(),
            review_questions=draft.review_questions
            or ["Quais pontos precisam de revisão profissional antes de prosseguir?"],
            educational_notice=EDUCATIONAL_NOTICE,
            prescription_status=payload.status,
            risk_level=payload.risk_level,
            critical_alert_codes=critical_alert_codes,
            missing_patient_data=self._missing_patient_data(payload),
            rag_sources=[
                self._rag_source_label(item) for item in payload.rag_evidence if item.get("source")
            ],
            how_to_explain_to_patient=how_to_explain,
        )

    def _rag_source_label(self, item: dict) -> str:
        source = str(item.get("source_name") or item.get("source") or "fonte interna")
        jurisdiction = str(item.get("jurisdiction") or "GLOBAL").upper()
        status = str(item.get("validation_status") or "pendente")
        evidence_type = str(item.get("evidence_type") or "seed_educacional")
        return f"{source} [{jurisdiction}, {evidence_type}, {status}]"

    def _missing_patient_data(self, payload: PrescriptionExplainRequest) -> list[str]:
        patient = payload.patient
        checks = {
            "condição renal": patient.renal_condition,
            "condição hepática": patient.hepatic_condition,
            "condição cardíaca": patient.cardiac_condition,
            "histórico gastrointestinal": patient.gastrointestinal_history,
            "reações adversas": patient.adverse_reactions,
            "medicamentos contínuos": patient.current_medications,
        }
        return [label for label, value in checks.items() if not value]

    def _build_prompt(self, payload: PrescriptionExplainRequest, requester_role: str) -> str:
        return json.dumps(self._build_context(payload, requester_role), ensure_ascii=False)
