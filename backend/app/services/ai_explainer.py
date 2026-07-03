from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from app.core.config import Settings
from app.schemas.prescription_schema import (
    AlertRead,
    PrescriptionExplainRequest,
    PrescriptionExplainResponse,
)

EDUCATIONAL_NOTICE = (
    "Resposta gerada como apoio educacional e demonstrativo. Ela não substitui "
    "avaliação clínica, protocolos institucionais ou decisão profissional."
)

ALERT_EXPLANATIONS = {
    "ALLERGY_BLOCK": (
        "Há compatibilidade entre alergia registrada e medicamento, princípio ativo ou classe."
    ),
    "MAX_DAILY_DOSE_EXCEEDED": "A dose diária calculada ultrapassa o limite cadastrado.",
    "DRUG_INTERACTION": "Existe interação demonstrativa entre medicamento novo e uso contínuo.",
    "POLYPHARMACY": "O paciente usa cinco ou mais medicamentos contínuos.",
    "AGE_RISK": "A idade do paciente aumenta a necessidade de revisão cuidadosa.",
    "CONTRAINDICATION": "Uma comorbidade coincide com contraindicação cadastrada.",
    "INVALID_ROUTE": "A via informada não consta nas vias permitidas do medicamento.",
}

ALERT_QUESTIONS = {
    "ALLERGY_BLOCK": "Existe alternativa terapêutica sem relação com a alergia registrada?",
    "MAX_DAILY_DOSE_EXCEEDED": (
        "A dose e a frequência podem ser ajustadas para ficar dentro do limite diário?"
    ),
    "DRUG_INTERACTION": "A associação medicamentosa é necessária ou há substituição mais segura?",
    "POLYPHARMACY": "Há medicamentos contínuos duplicados, obsoletos ou sem indicação atual?",
    "AGE_RISK": "A idade exige dose inicial menor, monitoramento adicional ou ajuste de intervalo?",
    "CONTRAINDICATION": "A comorbidade contraindica o uso ou exige protocolo de monitoramento?",
    "INVALID_ROUTE": "A via de administração deve ser corrigida antes de prosseguir?",
}

SYSTEM_INSTRUCTIONS = """
Você é uma camada explicativa educacional do Prescripta.
Explique apenas alertas já gerados por regras determinísticas.
Não libere prescrição, não reduza risco, não calcule dose crítica e não substitua revisão humana.
Priorize fontes brasileiras quando o contexto for BR.
Trate fontes internacionais como apoio secundário.
Informe quando uma evidência for demonstrativa, externa ou pendente de revisão.
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
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def explain(
        self,
        payload: PrescriptionExplainRequest,
        *,
        requester_role: str,
    ) -> PrescriptionExplainResponse:
        provider = self.settings.ai_provider.strip().lower() or "fallback"
        model = self.settings.ai_model.strip() or None
        fallback_reason = ""

        external_provider_ready = (
            self.settings.ai_api_key.strip() or self.settings.ai_base_url.strip()
        )
        if provider in {"openai", "llama", "local"} and external_provider_ready:
            try:
                draft = self._explain_with_openai_compatible(payload, requester_role)
                return self._response(
                    payload=payload,
                    provider=provider,
                    model=model,
                    draft=draft,
                    used_fallback=False,
                )
            except Exception as exc:  # pragma: no cover - defensive runtime fallback
                fallback_reason = f"Fallback determinístico acionado ({type(exc).__name__})."
        elif provider == "gemini":
            fallback_reason = (
                "Provider Gemini selecionado sem conector leve configurado nesta versão; "
                "fallback determinístico acionado."
            )
        elif provider != "fallback":
            fallback_reason = (
                "Provider de IA sem chave ou não suportado; "
                "fallback determinístico acionado."
            )

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

    def _explain_with_openai_compatible(
        self,
        payload: PrescriptionExplainRequest,
        requester_role: str,
    ) -> ExplanationDraft:
        from openai import OpenAI

        client_kwargs = {"api_key": self.settings.ai_api_key or "local"}
        if self.settings.ai_base_url:
            client_kwargs["base_url"] = self.settings.ai_base_url
        client = OpenAI(**client_kwargs)
        response = client.responses.create(
            model=self.settings.ai_model,
            instructions=SYSTEM_INSTRUCTIONS,
            input=self._build_prompt(payload, requester_role),
            text={"format": {"type": "json_object"}, "verbosity": "low"},
        )
        parsed = json.loads(response.output_text)
        draft = ExplanationDraft(
            simple_explanation=str(parsed.get("simple_explanation") or ""),
            technical_summary=str(parsed.get("technical_summary") or ""),
            review_questions=self._coerce_questions(parsed.get("review_questions")),
            educational_notice=str(parsed.get("educational_notice") or EDUCATIONAL_NOTICE),
        )
        has_required_fields = (
            draft.simple_explanation and draft.technical_summary and draft.review_questions
        )
        if not has_required_fields:
            raise ValueError("Resposta de IA incompleta.")
        return draft

    def _fallback_explanation(
        self,
        payload: PrescriptionExplainRequest,
        requester_role: str,
        *,
        fallback_reason: str = "",
    ) -> ExplanationDraft:
        daily_total = payload.dose_mg * payload.frequency_per_day
        cumulative = (
            daily_total * payload.duration_days if payload.duration_days is not None else None
        )
        if payload.alerts:
            alert_lines = [self._plain_alert_line(alert) for alert in payload.alerts]
            alerts_text = " ".join(alert_lines)
        else:
            alerts_text = "Nenhum alerta foi gerado pelas regras cadastradas."

        if payload.status == "bloqueado":
            opening = "A prescrição foi bloqueada porque há pelo menos um risco crítico."
        elif payload.human_review_required:
            opening = "A prescrição exige atenção e revisão humana antes de qualquer decisão."
        else:
            opening = "A checagem não encontrou risco relevante nas regras demonstrativas."

        cumulative_text = (
            f"Dose acumulada estimada: {cumulative:g} mg. " if cumulative else ""
        )
        technical_summary = (
            f"Paciente: {payload.patient.name}. Medicamento: {payload.medication.brand_name} "
            f"({payload.medication.active_ingredient}). Dose diária calculada: {daily_total:g} mg. "
            f"{cumulative_text}"
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
            if any(
                str(item.get("jurisdiction", "")).upper() not in {"BR", "GLOBAL"}
                for item in payload.rag_evidence
            ):
                technical_summary = (
                    f"{technical_summary} Fontes internacionais são apoio secundário "
                    "e não substituem a prioridade brasileira Anvisa/DCB no contexto BR."
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
            questions.append("Alguma alternativa avaliada apresenta menor risco demonstrativo?")
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
        return (
            f"{alert.title}: {explanation} Recomendação cadastrada: "
            f"{alert.recommendation}"
        )

    def _build_prompt(self, payload: PrescriptionExplainRequest, requester_role: str) -> str:
        context = {
            "patient": payload.patient.model_dump(),
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
            "rag_evidence": payload.rag_evidence,
            "clinical_context_graph": payload.clinical_context_graph,
            "alternatives": payload.alternatives,
            "requester_role": requester_role,
        }
        return json.dumps(context, ensure_ascii=False)

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
        missing_patient_data = self._missing_patient_data(payload)
        rag_sources = [
            self._rag_source_label(item)
            for item in payload.rag_evidence
            if item.get("source")
        ]
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
            missing_patient_data=missing_patient_data,
            rag_sources=rag_sources,
        )

    def _rag_source_label(self, item: dict) -> str:
        source = str(item.get("source_name") or item.get("source") or "fonte interna")
        jurisdiction = str(item.get("jurisdiction") or "GLOBAL").upper()
        status = str(item.get("validation_status") or "demo")
        evidence_type = str(item.get("evidence_type") or "demo_seed")
        return f"{source} [{jurisdiction}, {evidence_type}, {status}]"

    def _missing_patient_data(self, payload: PrescriptionExplainRequest) -> list[str]:
        missing: list[str] = []
        patient = payload.patient
        checks = {
            "condição renal": patient.renal_condition,
            "condição hepática": patient.hepatic_condition,
            "condição cardíaca": patient.cardiac_condition,
            "histórico gastrointestinal": patient.gastrointestinal_history,
            "reações adversas": patient.adverse_reactions,
            "medicamentos contínuos": patient.current_medications,
        }
        for label, value in checks.items():
            if not value:
                missing.append(label)
        return missing
