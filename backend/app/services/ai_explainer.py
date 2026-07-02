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
    "Resposta gerada como apoio educacional e demonstrativo. Ela nao substitui "
    "avaliacao clinica, protocolos institucionais ou decisao profissional."
)

ALERT_EXPLANATIONS = {
    "ALLERGY_BLOCK": (
        "Ha compatibilidade entre alergia registrada e medicamento, principio ativo ou classe."
    ),
    "MAX_DAILY_DOSE_EXCEEDED": "A dose diaria calculada ultrapassa o limite cadastrado.",
    "DRUG_INTERACTION": "Existe interacao demonstrativa entre medicamento novo e uso continuo.",
    "POLYPHARMACY": "O paciente usa cinco ou mais medicamentos continuos.",
    "AGE_RISK": "A idade do paciente aumenta a necessidade de revisao cuidadosa.",
    "CONTRAINDICATION": "Uma comorbidade coincide com contraindicao cadastrada.",
    "INVALID_ROUTE": "A via informada nao consta nas vias permitidas do medicamento.",
}

ALERT_QUESTIONS = {
    "ALLERGY_BLOCK": "Existe alternativa terapeutica sem relacao com a alergia registrada?",
    "MAX_DAILY_DOSE_EXCEEDED": (
        "A dose e a frequencia podem ser ajustadas para ficar dentro do limite diario?"
    ),
    "DRUG_INTERACTION": "A associacao medicamentosa e necessaria ou ha substituicao mais segura?",
    "POLYPHARMACY": "Ha medicamentos continuos duplicados, obsoletos ou sem indicacao atual?",
    "AGE_RISK": "A idade exige dose inicial menor, monitoramento adicional ou ajuste de intervalo?",
    "CONTRAINDICATION": "A comorbidade contraindica o uso ou exige protocolo de monitoramento?",
    "INVALID_ROUTE": "A via de administracao deve ser corrigida antes de prosseguir?",
}

SYSTEM_INSTRUCTIONS = """
Voce e uma camada explicativa educacional do Prescripta.
Explique apenas alertas ja gerados por regras deterministicas.
Nao libere prescricao, nao reduza risco, nao calcule dose critica e nao substitua revisao humana.
Responda em JSON com as chaves: simple_explanation, technical_summary,
review_questions, educational_notice.
Use portugues claro, tecnico quando necessario, e preserve todo bloqueio critico.
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

        if provider == "openai" and self.settings.ai_api_key.strip():
            try:
                draft = self._explain_with_openai(payload, requester_role)
                return self._response(
                    payload=payload,
                    provider=provider,
                    model=model,
                    draft=draft,
                    used_fallback=False,
                )
            except Exception as exc:  # pragma: no cover - defensive runtime fallback
                fallback_reason = f"Fallback deterministico acionado ({type(exc).__name__})."
        elif provider != "fallback":
            fallback_reason = (
                "Provider de IA sem chave ou nao suportado; "
                "fallback deterministico acionado."
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

    def _explain_with_openai(
        self,
        payload: PrescriptionExplainRequest,
        requester_role: str,
    ) -> ExplanationDraft:
        from openai import OpenAI

        client = OpenAI(api_key=self.settings.ai_api_key)
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
        if payload.alerts:
            alert_lines = [self._plain_alert_line(alert) for alert in payload.alerts]
            alerts_text = " ".join(alert_lines)
        else:
            alerts_text = "Nenhum alerta foi gerado pelas regras cadastradas."

        if payload.status == "bloqueado":
            opening = "A prescricao foi bloqueada porque ha pelo menos um risco critico."
        elif payload.human_review_required:
            opening = "A prescricao exige atencao e revisao humana antes de qualquer decisao."
        else:
            opening = "A checagem nao encontrou risco relevante nas regras demonstrativas."

        technical_summary = (
            f"Paciente: {payload.patient.name}. Medicamento: {payload.medication.brand_name} "
            f"({payload.medication.active_ingredient}). Dose diaria calculada: {daily_total:g} mg. "
            f"Status deterministico: {payload.status}. Risco: {payload.risk_level}. "
            f"Perfil solicitante: {requester_role}. Alertas avaliados: {len(payload.alerts)}."
        )
        if fallback_reason:
            technical_summary = f"{technical_summary} {fallback_reason}"

        questions = [
            ALERT_QUESTIONS.get(alert.code, f"Como revisar o alerta {alert.title}?")
            for alert in payload.alerts
        ]
        if not questions:
            questions = [
                "A prescricao foi revisada conforme protocolo local?",
                "Ha novas alergias, comorbidades ou medicamentos continuos nao cadastrados?",
            ]

        return ExplanationDraft(
            simple_explanation=f"{opening} {alerts_text}",
            technical_summary=technical_summary,
            review_questions=questions[:6],
        )

    def _plain_alert_line(self, alert: AlertRead) -> str:
        explanation = ALERT_EXPLANATIONS.get(alert.code, alert.description)
        return (
            f"{alert.title}: {explanation} Recomendacao cadastrada: "
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
        return PrescriptionExplainResponse(
            provider=provider,
            model=model,
            used_fallback=used_fallback,
            simple_explanation=draft.simple_explanation.strip(),
            technical_summary=draft.technical_summary.strip(),
            review_questions=draft.review_questions
            or ["Quais pontos precisam de revisao profissional antes de prosseguir?"],
            educational_notice=EDUCATIONAL_NOTICE,
            prescription_status=payload.status,
            risk_level=payload.risk_level,
            critical_alert_codes=critical_alert_codes,
        )
