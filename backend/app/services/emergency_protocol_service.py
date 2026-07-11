# ruff: noqa: E501
from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field, ValidationError, field_validator
from sqlalchemy.orm import Session

from app.database.models import AuditEventModel, UserModel
from app.reports.csv_exporter import export_csv_bytes
from app.reports.json_exporter import export_json_bytes
from app.schemas.protocol_schema import (
    EmergencyProtocolRead,
    ProtocolCalculatedValue,
    ProtocolEvidenceRead,
    ProtocolExplainResponse,
    ProtocolReportPreview,
    ProtocolRunEventExport,
    ProtocolRunRequest,
    ProtocolRunResponse,
)
from app.services.ai_settings import AIConfigurationError, AISettingsService
from app.services.audit_service import AuditService

PROTOCOL_EDUCATIONAL_NOTICE = (
    "Protocolo demonstrativo para apoio educacional/controlado; não substitui "
    "protocolo institucional, regulação médica, bula ou decisão profissional."
)


class ProtocolNotFoundError(ValueError):
    pass


class ProtocolValidationError(ValueError):
    pass


class ProtocolNarrative(BaseModel):
    simple_explanation: str = ""
    professional_summary: str = ""
    safety_note: str = ""
    cited_evidence_refs: list[str] = Field(default_factory=list)

    @field_validator("simple_explanation", "professional_summary", "safety_note", mode="before")
    @classmethod
    def safe_text(cls, value: object) -> str:
        text = str(value or "").strip()
        if "<" in text or ">" in text:
            raise ValueError("HTML bruto não é aceito.")
        return text[:1800]

    @field_validator("cited_evidence_refs", mode="before")
    @classmethod
    def safe_refs(cls, value: object) -> list[str]:
        if not isinstance(value, list):
            return []
        return [str(item).strip()[:80] for item in value if str(item).strip()][:8]


class EmergencyProtocolService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self._protocols = {protocol.id: protocol for protocol in _build_protocols()}

    def list_protocols(self, category: str | None = None) -> list[EmergencyProtocolRead]:
        protocols = sorted(self._protocols.values(), key=lambda item: (item.category, item.title))
        if category:
            needle = category.lower()
            protocols = [item for item in protocols if needle in item.category.lower()]
        return protocols

    def get_protocol(self, protocol_id: str) -> EmergencyProtocolRead:
        normalized_id = _normalize_protocol_id(protocol_id)
        protocol = self._protocols.get(normalized_id) or self._protocols.get(
            normalized_id.replace("-", "_")
        )
        if protocol is None:
            raise ProtocolNotFoundError("Protocolo não encontrado.")
        return protocol

    def evidence(self, protocol_id: str) -> list[ProtocolEvidenceRead]:
        protocol = self.get_protocol(protocol_id)
        refs: dict[str, ProtocolEvidenceRead] = {}
        for step in protocol.steps:
            refs[step.evidence_ref] = ProtocolEvidenceRead(
                evidence_ref=step.evidence_ref,
                source_name=protocol.source_name,
                source_url=protocol.source_url,
                source_version=protocol.source_version,
                summary=step.explanation,
                validation_status=protocol.validation_status,
            )
        return list(refs.values())

    def run(
        self,
        protocol_id: str,
        payload: ProtocolRunRequest,
        user: UserModel,
    ) -> ProtocolRunResponse:
        protocol = self.get_protocol(protocol_id)
        self._validate_context(protocol, payload.context)
        calculations = self._calculations(protocol, payload.context)
        flags = self._triage_flags(protocol, payload.context, calculations)
        timeline = self._timeline(protocol, payload)
        evidence = self.evidence(protocol.id)
        event = AuditService(self.db).record_action(
            user=user,
            action="protocol.run",
            resource_type="protocol",
            resource_id=protocol.id,
            status="recorded",
            risk_level=_risk_level(protocol.severity_level),
            details={
                "protocol_id": protocol.id,
                "protocol_title": protocol.title,
                "category": protocol.category,
                "severity_level": protocol.severity_level,
                "context": _safe_context(payload.context),
                "notes_present": bool(payload.notes),
                "triage_flags": flags,
                "calculated_values": [item.model_dump(mode="json") for item in calculations],
                "timeline": timeline,
                "evidence_refs": [item.evidence_ref for item in evidence],
                "source": protocol.source_name,
                "jurisdiction": protocol.jurisdiction,
                "validation_status": protocol.validation_status,
                "secret_logged": False,
            },
        )
        return ProtocolRunResponse(
            run_id=event.id,
            protocol_id=protocol.id,
            title=protocol.title,
            status="recorded",
            warning_level=protocol.severity_level,
            triage_flags=flags,
            calculated_values=calculations,
            timeline=timeline,
            evidence=evidence,
            audit_notice=f"Evento de protocolo registrado na auditoria #{event.id}.",
            educational_notice=PROTOCOL_EDUCATIONAL_NOTICE,
        )

    def explain(
        self,
        protocol_id: str,
        context: dict[str, Any],
        *,
        user: UserModel,
        run_id: int | None = None,
        question: str | None = None,
    ) -> ProtocolExplainResponse:
        protocol = self.get_protocol(protocol_id)
        evidence_refs = {step.evidence_ref for step in protocol.steps}
        config = AISettingsService(self.db).runtime_config()
        provider = config.provider
        model = config.model
        try:
            raw = AISettingsService(self.db).complete_json(
                system_instructions=_protocol_ai_instructions(),
                payload={
                    "protocol": _protocol_payload(protocol),
                    "context": _safe_context(context),
                    "question": question,
                    "allowed_evidence_refs": sorted(evidence_refs),
                },
                purpose="protocol_explanation",
                config=config,
            )
            narrative = ProtocolNarrative.model_validate(raw)
            if set(narrative.cited_evidence_refs) - evidence_refs:
                raise AIConfigurationError("IA citou referência de evidência inexistente.")
            used_fallback = False
        except (AIConfigurationError, ValidationError, ValueError):
            narrative = self._fallback_narrative(protocol, context, question)
            provider = "fallback"
            model = "deterministic"
            used_fallback = True

        AuditService(self.db).record_action(
            user=user,
            action="protocol.explain",
            resource_type="protocol",
            resource_id=protocol.id,
            status="fallback" if used_fallback else "ai_generated",
            risk_level=_risk_level(protocol.severity_level),
            details={
                "protocol_id": protocol.id,
                "run_id": run_id,
                "provider": provider,
                "model": model,
                "used_fallback": used_fallback,
                "structure_locked": True,
                "cited_evidence_refs": narrative.cited_evidence_refs,
                "secret_logged": False,
            },
        )
        return ProtocolExplainResponse(
            provider=provider,
            model=model,
            used_fallback=used_fallback,
            protocol_id=protocol.id,
            simple_explanation=narrative.simple_explanation,
            professional_summary=narrative.professional_summary,
            safety_note=narrative.safety_note,
            cited_evidence_refs=narrative.cited_evidence_refs,
            educational_notice=PROTOCOL_EDUCATIONAL_NOTICE,
        )

    def report(self, protocol_id: str, run_id: int | None = None) -> ProtocolReportPreview:
        protocol = self.get_protocol(protocol_id)
        event = self._run_event(run_id, protocol.id) if run_id else None
        context = (event.details or {}).get("context", {}) if event else {}
        calculations = [
            ProtocolCalculatedValue.model_validate(item)
            for item in ((event.details or {}).get("calculated_values", []) if event else [])
        ]
        flags = list((event.details or {}).get("triage_flags", []) if event else [])
        timeline = list((event.details or {}).get("timeline", []) if event else self._timeline(protocol))
        evidence = self.evidence(protocol.id)
        lines = [
            "Prescripta - Relatório de Protocolo Rápido",
            f"Protocolo: {protocol.title}",
            f"Categoria: {protocol.category}",
            f"Severidade: {protocol.severity_level}",
            f"Fonte: {protocol.source_name}",
            f"Versão da fonte: {protocol.source_version or '-'}",
            f"Status de validação: {protocol.validation_status}",
            "",
            "Aviso:",
            PROTOCOL_EDUCATIONAL_NOTICE,
            "",
            "Objetivo clínico:",
            protocol.clinical_goal,
            "",
            "Sinais de alerta:",
            *[f"- {item}" for item in protocol.red_flags],
            "",
            "Linha do tempo estruturada:",
            *[f"{item['order']}. {item['title']} - {item['status']}" for item in timeline],
        ]
        if flags:
            lines.extend(["", "Flags do contexto:", *[f"- {flag}" for flag in flags]])
        if calculations:
            lines.extend(["", "Cálculos demonstrativos:"])
            lines.extend([f"- {item.label}: {item.value} ({item.warning})" for item in calculations])
        payload = {
            "protocol": protocol.model_dump(mode="json"),
            "run_id": run_id,
            "context": context,
            "triage_flags": flags,
            "calculated_values": [item.model_dump(mode="json") for item in calculations],
            "timeline": timeline,
            "evidence": [item.model_dump(mode="json") for item in evidence],
            "educational_notice": PROTOCOL_EDUCATIONAL_NOTICE,
        }
        return ProtocolReportPreview(
            title=f"Relatório de Protocolo - {protocol.title}",
            protocol_id=protocol.id,
            run_id=run_id,
            generated_at=datetime.now(UTC),
            report_lines=lines,
            report_payload=payload,
            timeline=timeline,
            evidence=evidence,
        )

    def export_event_json(self, protocol_id: str, run_id: int) -> bytes:
        protocol = self.get_protocol(protocol_id)
        event = self._run_event(run_id, protocol.id)
        payload = ProtocolRunEventExport.model_validate(event).model_dump(mode="json")
        return export_json_bytes("protocol_run", payload)

    def export_event_csv(self, protocol_id: str, run_id: int) -> bytes:
        protocol = self.get_protocol(protocol_id)
        event = self._run_event(run_id, protocol.id)
        details = event.details or {}
        rows = [
            {
                "run_id": event.id,
                "protocol_id": protocol.id,
                "protocol_title": protocol.title,
                "created_at": event.created_at.isoformat(),
                "status": event.status,
                "risk_level": event.risk_level,
                "triage_flags": "; ".join(details.get("triage_flags", [])),
                "evidence_refs": "; ".join(details.get("evidence_refs", [])),
            }
        ]
        return export_csv_bytes(rows)

    def _validate_context(self, protocol: EmergencyProtocolRead, context: dict[str, Any]) -> None:
        missing = [
            field.label
            for field in protocol.context_fields
            if field.required and _empty(context.get(field.name))
        ]
        if missing:
            raise ProtocolValidationError(
                "Contexto mínimo ausente: " + ", ".join(missing) + "."
            )

    def _calculations(
        self, protocol: EmergencyProtocolRead, context: dict[str, Any]
    ) -> list[ProtocolCalculatedValue]:
        values: list[ProtocolCalculatedValue] = []
        if protocol.id == "anafilaxia" and _number(context.get("weight_kg")):
            weight = float(context["weight_kg"])
            age = _number(context.get("age_years"))
            max_dose = 0.3 if age is not None and age < 12 else 0.5
            dose_mg = min(weight * 0.01, max_dose)
            values.append(
                ProtocolCalculatedValue(
                    label="Adrenalina IM 1 mg/mL demonstrativa",
                    value=f"{dose_mg:.2f} mg ({dose_mg:.2f} mL)",
                    formula="0,01 mg/kg, limitado por faixa etária/peso no protocolo-fonte.",
                    source_ref="anafilaxia_adrenalina_im",
                    warning="Confirmar concentração, via, faixa etária, apresentação e protocolo local.",
                )
            )
        if protocol.id == "hipoglicemia" and _number(context.get("glucose_mg_dl")):
            glucose = float(context["glucose_mg_dl"])
            label = "Hipoglicemia provável" if glucose < 70 else "Glicemia fora do gatilho"
            warning = (
                "Reavaliar glicemia e estado neurológico após correção."
                if glucose < 70
                else "Manter avaliação clínica se sintomas persistirem."
            )
            values.append(
                ProtocolCalculatedValue(
                    label="Classificação glicêmica",
                    value=f"{label}: {glucose:.0f} mg/dL",
                    formula="Gatilho demonstrativo: glicemia capilar < 70 mg/dL.",
                    source_ref="hipoglicemia_linha_cuidado",
                    warning=warning,
                )
            )
        if protocol.id == "broncoespasmo" and _number(context.get("spo2")):
            spo2 = float(context["spo2"])
            values.append(
                ProtocolCalculatedValue(
                    label="Alvo de oxigenação",
                    value="Abaixo do alvo > 94%" if spo2 < 94 else "No alvo informado",
                    formula="Comparação simples com alvo de saturação citado na linha de cuidado.",
                    source_ref="asma_linha_cuidado",
                    warning="Oxigenoterapia e broncodilatador dependem de avaliação profissional.",
                )
            )
        return values

    def _triage_flags(
        self,
        protocol: EmergencyProtocolRead,
        context: dict[str, Any],
        calculations: list[ProtocolCalculatedValue],
    ) -> list[str]:
        flags: list[str] = []
        if protocol.severity_level == "critical":
            flags.append("Acionar equipe/regulação conforme protocolo institucional.")
        if protocol.id == "pcr":
            if context.get("responsive") is False and context.get("normal_breathing") is False:
                flags.append("Contexto compatível com avaliação imediata de PCR.")
        if protocol.id == "dor_toracica" and _number(context.get("chest_pain_minutes")):
            if float(context["chest_pain_minutes"]) >= 20:
                flags.append("Dor prolongada: priorizar ECG/monitorização e avaliação de SCA.")
        if protocol.id == "intoxicacao" and context.get("substance"):
            flags.append("Preservar embalagem/receita e acionar centro toxicológico.")
        flags.extend(item.warning for item in calculations if item.requires_human_confirmation)
        return flags[:10]

    def _timeline(
        self,
        protocol: EmergencyProtocolRead,
        payload: ProtocolRunRequest | None = None,
    ) -> list[dict[str, Any]]:
        selected = set(payload.selected_step_orders if payload else [])
        return [
            {
                "order": step.order,
                "title": step.title,
                "status": "marcado" if step.order in selected else "pendente/revisão",
                "warning_level": step.warning_level,
                "requires_human_judgment": step.requires_human_judgment,
                "evidence_ref": step.evidence_ref,
            }
            for step in protocol.steps
        ]

    def _fallback_narrative(
        self,
        protocol: EmergencyProtocolRead,
        context: dict[str, Any],
        question: str | None,
    ) -> ProtocolNarrative:
        context_note = " Contexto informado foi usado apenas para destacar cautelas auditáveis."
        if not context:
            context_note = " Nenhum contexto adicional foi informado."
        question_note = f" Pergunta registrada: {question}" if question else ""
        return ProtocolNarrative(
            simple_explanation=(
                f"{protocol.title} organiza medidas iniciais e pontos de atenção para leitura "
                f"rápida. O fluxo deve ser confirmado por profissional habilitado."
            ),
            professional_summary=(
                f"Objetivo: {protocol.clinical_goal} "
                f"Fonte principal: {protocol.source_name}.{context_note}{question_note}"
            ),
            safety_note=PROTOCOL_EDUCATIONAL_NOTICE,
            cited_evidence_refs=[step.evidence_ref for step in protocol.steps[:3]],
        )

    def _run_event(self, run_id: int | None, protocol_id: str) -> AuditEventModel:
        if run_id is None:
            raise ProtocolValidationError("Informe o evento de execução do protocolo.")
        event = self.db.get(AuditEventModel, run_id)
        if event is None or event.action != "protocol.run":
            raise ProtocolNotFoundError("Execução de protocolo não encontrada.")
        if (event.details or {}).get("protocol_id") != protocol_id:
            raise ProtocolValidationError("Evento não pertence ao protocolo informado.")
        return event


def _protocol_ai_instructions() -> str:
    return """
Você é o explicador de protocolos do Prescripta.
Use somente o protocolo e as referências enviadas no payload.
Não invente etapa, dose, contraindicação, fonte, evidência ou decisão.
Não altere a ordem do protocolo e não autorize conduta.
Retorne JSON com: simple_explanation, professional_summary, safety_note, cited_evidence_refs.
""".strip()


def _protocol_payload(protocol: EmergencyProtocolRead) -> dict[str, Any]:
    return {
        "id": protocol.id,
        "title": protocol.title,
        "summary": protocol.summary,
        "clinical_goal": protocol.clinical_goal,
        "steps": [step.model_dump(mode="json") for step in protocol.steps],
        "source_name": protocol.source_name,
        "source_url": protocol.source_url,
        "disclaimer": protocol.disclaimer,
    }


def _risk_level(severity: str) -> str:
    return {
        "critical": "critico",
        "high": "alto",
        "attention": "moderado",
        "info": "baixo",
    }.get(severity, "moderado")


def _normalize_protocol_id(protocol_id: str) -> str:
    return protocol_id.strip().lower().replace(" ", "-")


def _empty(value: object) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip()
    if isinstance(value, list | dict):
        return len(value) == 0
    return False


def _number(value: object) -> float | None:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _safe_context(context: dict[str, Any]) -> dict[str, Any]:
    safe: dict[str, Any] = {}
    for key, value in context.items():
        if isinstance(value, str):
            safe[key] = value.strip()[:240]
        elif isinstance(value, int | float | bool) or value is None:
            safe[key] = value
        elif isinstance(value, list):
            safe[key] = [str(item).strip()[:120] for item in value[:12]]
        else:
            safe[key] = str(value)[:240]
    return safe


def _build_protocols() -> list[EmergencyProtocolRead]:
    common_disclaimer = PROTOCOL_EDUCATIONAL_NOTICE
    return [
        EmergencyProtocolRead(
            id="anafilaxia",
            slug="anafilaxia",
            title="Anafilaxia",
            category="Emergência alérgica",
            summary="Fluxo inicial para suspeita de reação anafilática com foco em ABCDE, adrenalina IM e monitorização.",
            clinical_goal="Reconhecer sinais sistêmicos rapidamente, acionar suporte e organizar medidas imediatas enquanto a decisão final permanece humana.",
            severity_level="critical",
            audience="Profissionais de saúde treinados",
            source_name="Secretaria Municipal de Saúde de Campinas - Protocolo de Anafilaxia para Enfermeiros",
            source_url="https://portal-adm.campinas.sp.gov.br/sites/default/files/secretarias/arquivos-avulsos/125/2022/10/04-111720/Protocolo_Anafilaxia_Enfermeiros.pdf",
            source_version="publicação municipal consultada em 2026",
            last_reviewed_at="2026-07-11",
            disclaimer=common_disclaimer,
            red_flags=["estridor ou broncoespasmo", "hipotensão", "urticária extensa com sintomas respiratórios", "rebaixamento de consciência"],
            immediate_measures=["ABCDE", "acionar ajuda", "adrenalina IM por profissional habilitado", "oxigênio/acesso venoso conforme gravidade"],
            medication_references=["Adrenalina 1 mg/mL IM é referência demonstrativa; confirmar dose, concentração e protocolo local."],
            cautions=["Não atrasar acionamento de suporte", "Cautela em idosos/cardiopatas exige julgamento, mas não dispensa manejo urgente"],
            referral_criteria=["qualquer suspeita de anafilaxia sistêmica", "recorrência ou necessidade de doses repetidas"],
            monitoring=["pressão arterial", "frequência cardíaca", "saturação", "sinais respiratórios", "recorrência bifásica"],
            documentation_items=["gatilho suspeito", "horário de início", "sinais vitais", "medicações administradas", "resposta clínica"],
            do_not_apply_when=["quadro local leve sem sinais sistêmicos deve ser avaliado por protocolo próprio"],
            human_judgment_points=["confirmar diagnóstico diferencial", "confirmar dose e via", "decidir observação e transferência"],
            safety_notes=["A calculadora é demonstrativa e nunca deve ser usada como prescrição automática."],
            context_fields=[
                {"name": "suspected_trigger", "label": "Gatilho suspeito", "field_type": "text", "required": True},
                {"name": "weight_kg", "label": "Peso", "field_type": "number", "unit": "kg", "helper": "Usado apenas em cálculo demonstrativo."},
                {"name": "age_years", "label": "Idade", "field_type": "number", "unit": "anos"},
                {"name": "respiratory_symptoms", "label": "Sintomas respiratórios", "field_type": "boolean"},
                {"name": "hypotension", "label": "Hipotensão", "field_type": "boolean"},
            ],
            calculators=[
                {
                    "id": "adrenalina_im_demo",
                    "label": "Adrenalina IM demonstrativa",
                    "description": "Estimativa 0,01 mg/kg para conferência, com teto demonstrativo por faixa etária.",
                    "input_fields": ["weight_kg", "age_years"],
                    "source_note": "Conferir concentração 1 mg/mL, apresentação, via e protocolo local.",
                }
            ],
            steps=[
                _step(1, "Reconhecer sinais sistêmicos", "Avaliar pele/mucosa, respiração, circulação e consciência.", "A presença de comprometimento respiratório ou circulatório exige ação imediata.", "critical", "anafilaxia_reconhecimento"),
                _step(2, "Acionar suporte", "Chamar equipe, preparar monitorização e acionar regulação/SAMU quando aplicável.", "Fluxo rápido reduz atraso em tratamento e transferência.", "critical", "anafilaxia_suporte"),
                _step(3, "Organizar ABCDE", "Posicionar, avaliar via aérea, respiração, circulação e sinais vitais.", "ABCDE mantém a sequência verificável e auditável.", "high", "anafilaxia_abcde"),
                _step(4, "Adrenalina IM", "Usar adrenalina IM conforme profissional habilitado e protocolo local.", "A etapa não é autorização automática de dose; exige conferência humana.", "critical", "anafilaxia_adrenalina_im"),
                _step(5, "Monitorar resposta", "Registrar sinais, resposta, recorrência e necessidade de reavaliação.", "Anafilaxia pode exigir observação e nova decisão clínica.", "high", "anafilaxia_monitoramento"),
            ],
        ),
        EmergencyProtocolRead(
            id="pcr",
            slug="parada-cardiorrespiratoria",
            title="Parada cardiorrespiratória (PCR)",
            category="Emergência cardiovascular",
            summary="Sequência inicial de reconhecimento, acionamento de ajuda, compressões e desfibrilação quando indicada.",
            clinical_goal="Reduzir atraso entre reconhecimento, compressões de qualidade e desfibrilação/ALS quando disponível.",
            severity_level="critical",
            audience="Profissionais de saúde e equipes treinadas em suporte básico/avançado",
            source_name="Ministério da Saúde / SAMU 192 - Protocolos de Suporte Básico e Avançado de Vida",
            source_url="https://www.gov.br/saude/pt-br/composicao/saes/samu-192/publicacoes/protocolo-de-suporte-basico-de-vida-1-2.pdf/view",
            source_version="atualizado em 23/04/2024 no portal gov.br",
            last_reviewed_at="2026-07-11",
            disclaimer=common_disclaimer,
            red_flags=["inconsciência", "respiração ausente ou anormal", "ausência de pulso por profissional treinado"],
            immediate_measures=["segurança da cena", "acionar ajuda", "compressões torácicas", "DEA/desfibrilador"],
            referral_criteria=["todo caso suspeito de PCR"],
            monitoring=["ritmo quando disponível", "qualidade das compressões", "retorno de circulação espontânea", "tempo de ciclos"],
            documentation_items=["horário de colapso", "início das compressões", "choques", "ritmos", "retorno de circulação"],
            do_not_apply_when=["paciente responsivo com respiração normal deve seguir outra avaliação de urgência"],
            human_judgment_points=["confirmar responsividade/respiração", "decidir via aérea e medicações no suporte avançado", "decidir interrupção/continuidade conforme regulação"],
            safety_notes=["Fluxo exige treinamento em SBV/SAV e protocolo institucional."],
            context_fields=[
                {"name": "responsive", "label": "Paciente responsivo", "field_type": "boolean", "required": True},
                {"name": "normal_breathing", "label": "Respiração normal", "field_type": "boolean", "required": True},
                {"name": "aed_available", "label": "DEA disponível", "field_type": "boolean"},
            ],
            steps=[
                _step(1, "Garantir segurança", "Confirmar segurança da cena e uso de EPI.", "Evita risco para equipe e paciente.", "high", "pcr_seguranca"),
                _step(2, "Checar responsividade e respiração", "Avaliar resposta e respiração normal sem atrasar acionamento.", "Reconhecimento rápido é gatilho do fluxo.", "critical", "pcr_reconhecimento"),
                _step(3, "Acionar ajuda e DEA", "Chamar equipe, carrinho de emergência e desfibrilador/DEA.", "Desfibrilação precoce é ponto crítico quando indicada.", "critical", "pcr_dea"),
                _step(4, "Iniciar compressões", "Realizar compressões de alta qualidade conforme treinamento.", "Qualidade das compressões depende de treinamento e revezamento.", "critical", "pcr_compressoes"),
                _step(5, "Registrar ciclos", "Registrar tempos, ritmos, choques e retorno de circulação.", "Registro sustenta auditoria e continuidade do cuidado.", "high", "pcr_documentacao"),
            ],
        ),
        EmergencyProtocolRead(
            id="convulsao",
            slug="convulsao-crise-convulsiva",
            title="Convulsão / crise convulsiva",
            category="Emergência neurológica",
            summary="Apoio inicial para segurança, tempo de crise, via aérea, glicemia e acionamento de suporte.",
            clinical_goal="Prevenir trauma/aspiração, reconhecer crise prolongada e organizar dados essenciais para transferência.",
            severity_level="high",
            audience="Profissionais de saúde em atendimento inicial",
            source_name="Ministério da Saúde / SAMU 192 - Protocolos de Suporte Avançado de Vida",
            source_url="https://www.gov.br/saude/pt-br/composicao/saes/samu-192/publicacoes/protocolo-de-suporte-avancado-de-vida-1.pdf/view",
            source_version="atualizado em 23/04/2024 no portal gov.br",
            last_reviewed_at="2026-07-11",
            disclaimer=common_disclaimer,
            red_flags=["crise ativa prolongada", "trauma", "gestação", "hipoglicemia", "rebaixamento persistente"],
            immediate_measures=["proteger contra trauma", "não inserir objetos na boca", "lateralizar se possível", "avaliar glicemia"],
            medication_references=["Benzodiazepínicos aparecem em protocolos de SAV, mas exigem prescrição/competência profissional."],
            referral_criteria=["primeira crise", "crise prolongada", "recorrência", "trauma", "alteração persistente de consciência"],
            monitoring=["tempo de crise", "saturação", "glicemia", "nível de consciência", "recorrência"],
            documentation_items=["horário de início/fim", "descrição da crise", "glicemia", "medicações em uso", "trauma"],
            human_judgment_points=["diferenciar síncope/AVC/intoxicação", "decidir medicação e via", "definir transferência"],
            context_fields=[
                {"name": "seizure_active", "label": "Crise ativa", "field_type": "boolean", "required": True},
                {"name": "duration_minutes", "label": "Duração", "field_type": "number", "unit": "min"},
                {"name": "glucose_mg_dl", "label": "Glicemia", "field_type": "number", "unit": "mg/dL"},
            ],
            steps=[
                _step(1, "Proteger o paciente", "Afastar objetos, proteger cabeça e evitar contenção inadequada.", "Evita trauma sem piorar a crise.", "high", "convulsao_seguranca"),
                _step(2, "Não inserir objetos na boca", "Manter via aérea observada sem manobras perigosas.", "Reduz risco de lesão e aspiração.", "critical", "convulsao_via_aerea"),
                _step(3, "Cronometrar e avaliar glicemia", "Registrar duração e glicemia capilar quando disponível.", "Hipoglicemia é causa reversível importante.", "high", "convulsao_glicemia"),
                _step(4, "Acionar suporte se prolongada", "Crise prolongada/recorrente exige suporte e protocolo local.", "Medicação depende de profissional habilitado.", "high", "convulsao_suporte"),
                _step(5, "Documentar recuperação", "Registrar pós-ictal, sinais vitais, trauma e encaminhamento.", "Continuidade do cuidado depende do registro.", "attention", "convulsao_documentacao"),
            ],
        ),
        EmergencyProtocolRead(
            id="hipoglicemia",
            slug="hipoglicemia",
            title="Hipoglicemia",
            category="Emergência metabólica",
            summary="Fluxo inicial baseado em glicemia, consciência, correção e reavaliação.",
            clinical_goal="Identificar glicemia baixa, corrigir de modo compatível com consciência/via segura e reavaliar.",
            severity_level="high",
            audience="Profissionais de saúde em atendimento inicial",
            source_name="Ministério da Saúde - Linha de Cuidado DM2 no adulto / UPA / Hipoglicemia",
            source_url="https://linhasdecuidado.saude.gov.br/portal/diabetes-mellitus-tipo-2-%28DM2%29-no-adulto/unidade-de-pronto-atendimento/dm2-aguda/hipoglicemia/",
            source_version="Linha de cuidado consultada em 2026",
            last_reviewed_at="2026-07-11",
            disclaimer=common_disclaimer,
            red_flags=["glicemia < 70 mg/dL", "inconsciência", "convulsão", "não consegue ingerir com segurança"],
            immediate_measures=["medir glicemia", "avaliar consciência/deglutição", "corrigir conforme via segura", "reavaliar glicemia"],
            medication_references=["Carboidrato oral ou glicose EV dependem de consciência, acesso e protocolo local."],
            referral_criteria=["rebaixamento", "sem resposta à correção", "uso de sulfonilureia/insulina", "recorrência"],
            monitoring=["glicemia seriada", "consciência", "sinais vitais", "recorrência"],
            documentation_items=["glicemia inicial", "estado de consciência", "correção realizada", "glicemia pós-correção"],
            human_judgment_points=["via oral segura", "necessidade de acesso venoso", "investigar causa e recorrência"],
            context_fields=[
                {"name": "glucose_mg_dl", "label": "Glicemia capilar", "field_type": "number", "unit": "mg/dL", "required": True},
                {"name": "conscious", "label": "Consciente", "field_type": "boolean", "required": True},
                {"name": "can_swallow", "label": "Consegue deglutir", "field_type": "boolean"},
            ],
            calculators=[
                {
                    "id": "classificacao_glicemia",
                    "label": "Classificação glicêmica",
                    "description": "Marca gatilho demonstrativo de hipoglicemia quando glicemia < 70 mg/dL.",
                    "input_fields": ["glucose_mg_dl"],
                    "source_note": "Repetição e via de correção dependem do protocolo local.",
                }
            ],
            steps=[
                _step(1, "Confirmar glicemia", "Medir glicemia capilar e avaliar sintomas.", "A medida orienta correção e reavaliação.", "high", "hipoglicemia_linha_cuidado"),
                _step(2, "Avaliar consciência/deglutição", "Decidir se há via oral segura.", "Evita aspiração em paciente rebaixado.", "critical", "hipoglicemia_via_segura"),
                _step(3, "Corrigir conforme protocolo", "Usar carboidrato oral ou glicose EV conforme condição e competência.", "Dose/via dependem de protocolo local.", "high", "hipoglicemia_correcao"),
                _step(4, "Reavaliar glicemia", "Repetir glicemia após correção conforme protocolo.", "Recorrência exige nova avaliação.", "high", "hipoglicemia_reavaliacao"),
                _step(5, "Investigar causa", "Registrar insulina, antidiabéticos, jejum, álcool, infecção ou exercício.", "Evita alta sem plano de prevenção.", "attention", "hipoglicemia_causa"),
            ],
        ),
        EmergencyProtocolRead(
            id="dor_toracica",
            slug="dor-toracica-sca",
            title="Dor torácica / suspeita de SCA",
            category="Emergência cardiovascular",
            summary="Visão inicial para dor torácica aguda: ABCDE, ECG, monitorização e exclusão de causas fatais.",
            clinical_goal="Acelerar reconhecimento de dor torácica potencialmente grave e organizar avaliação inicial sem fechar diagnóstico.",
            severity_level="high",
            audience="Profissionais de pronto atendimento/regulação",
            source_name="Secretaria de Saúde do Distrito Federal - Protocolo de Urgências e Emergências Cardiológicas / SAMU",
            source_url="https://www.saude.df.gov.br/documents/37101/0/Protocolo%2Bde%2Batendimento%2Ba%2BUrg%C3%AAncias%2Be%2BEmerg%C3%AAncias%2BCardio%2B-%2BSAMU.pdf/e3454ac0-dee5-4c4e-b1e2-35d1d634aeb8?t=1739898804135",
            source_version="publicação DF consultada em 2026",
            last_reviewed_at="2026-07-11",
            disclaimer=common_disclaimer,
            red_flags=["dor prolongada", "sudorese", "dispneia", "síncope", "instabilidade hemodinâmica", "dor irradiada"],
            immediate_measures=["ABCDE", "ECG prioritário", "monitorização", "acesso e regulação conforme gravidade"],
            referral_criteria=["suspeita de SCA", "ECG alterado", "instabilidade", "dor persistente"],
            monitoring=["dor", "ECG", "pressão arterial", "frequência cardíaca", "saturação"],
            documentation_items=["início da dor", "características", "ECG", "sinais vitais", "fatores de risco", "condutas"],
            human_judgment_points=["interpretar ECG", "avaliar contraindicações", "decidir terapia e destino"],
            context_fields=[
                {"name": "chest_pain_minutes", "label": "Duração da dor", "field_type": "number", "unit": "min", "required": True},
                {"name": "radiation", "label": "Irradiação", "field_type": "boolean"},
                {"name": "systolic_bp", "label": "PAS", "field_type": "number", "unit": "mmHg"},
                {"name": "spo2", "label": "Saturação", "field_type": "number", "unit": "%"},
            ],
            steps=[
                _step(1, "Avaliar ABCDE", "Identificar instabilidade e causas ameaçadoras.", "Dor torácica pode ser SCA ou outra emergência fatal.", "high", "dor_toracica_abcde"),
                _step(2, "Priorizar ECG", "Obter/encaminhar ECG conforme protocolo de porta/primeiro atendimento.", "ECG rápido orienta rota assistencial.", "high", "dor_toracica_ecg"),
                _step(3, "Monitorar sinais", "Monitorizar dor, PA, FC, saturação e sintomas associados.", "Instabilidade altera prioridade.", "high", "dor_toracica_monitorizacao"),
                _step(4, "Checar contraindicações", "Não automatizar medicações; avaliar alergias, sangramento e protocolos.", "Conduta farmacológica exige julgamento.", "attention", "dor_toracica_contraindicacoes"),
                _step(5, "Documentar tempos", "Registrar início da dor, ECG, decisão e transferência.", "Tempo é indicador crítico do fluxo.", "attention", "dor_toracica_documentacao"),
            ],
        ),
        EmergencyProtocolRead(
            id="broncoespasmo",
            slug="broncoespasmo-crise-asmatica",
            title="Broncoespasmo / crise asmática inicial",
            category="Emergência respiratória",
            summary="Manejo inicial de exacerbação asmática/broncoespasmo com gravidade, oxigenação, broncodilatação e reavaliação.",
            clinical_goal="Estruturar avaliação de gravidade e tratamento inicial sem substituir protocolo local de medicação.",
            severity_level="high",
            audience="Profissionais de saúde em APS, UPA ou atendimento móvel",
            source_name="Ministério da Saúde - Linha de Cuidado da Asma / Manejo inicial",
            source_url="https://linhasdecuidado.saude.gov.br/portal/asma/servico-de-atendimento-movel/manejo-inicial/",
            source_version="Linha de cuidado consultada em 2026",
            last_reviewed_at="2026-07-11",
            disclaimer=common_disclaimer,
            red_flags=["saturação baixa", "fala entrecortada", "exaustão", "cianose", "rebaixamento", "silêncio auscultatório"],
            immediate_measures=["posição confortável", "saturação", "oxigênio se indicado", "broncodilatador conforme protocolo"],
            medication_references=["Salbutamol/ipratrópio/corticoide aparecem em linhas de cuidado; uso exige protocolo local."],
            referral_criteria=["exacerbação moderada/grave", "baixa resposta", "saturação baixa", "exaustão"],
            monitoring=["saturação", "frequência respiratória", "fala", "uso de musculatura acessória", "resposta ao broncodilatador"],
            documentation_items=["gatilho", "saturação", "gravidade", "doses administradas", "resposta"],
            human_judgment_points=["classificar gravidade", "decidir via/dispositivo", "decidir transferência"],
            context_fields=[
                {"name": "spo2", "label": "Saturação", "field_type": "number", "unit": "%", "required": True},
                {"name": "wheezing", "label": "Sibilância", "field_type": "boolean"},
                {"name": "speaks_sentences", "label": "Fala frases", "field_type": "boolean"},
            ],
            calculators=[
                {
                    "id": "alvo_saturacao",
                    "label": "Alvo de saturação",
                    "description": "Compara saturação informada com alvo > 94% citado na linha de cuidado.",
                    "input_fields": ["spo2"],
                    "source_note": "Oxigênio e broncodilatador dependem de avaliação e protocolo local.",
                }
            ],
            steps=[
                _step(1, "Classificar gravidade", "Avaliar fala, esforço, saturação e estado mental.", "Gravidade define urgência e transferência.", "high", "asma_gravidade"),
                _step(2, "Posicionar e oxigenar", "Manter sentado/confortável e oxigênio conforme alvo e protocolo.", "Oxigenação baixa é sinal de risco.", "high", "asma_oxigenio"),
                _step(3, "Broncodilatar conforme protocolo", "Aplicar broncodilatador por dispositivo adequado quando indicado.", "Dose/dispositivo exigem profissional habilitado.", "high", "asma_broncodilatador"),
                _step(4, "Reavaliar resposta", "Reavaliar saturação, fala e esforço após medidas iniciais.", "Baixa resposta exige escalonamento.", "high", "asma_reavaliacao"),
                _step(5, "Registrar gatilhos", "Documentar gatilho, medicações prévias e plano de seguimento.", "Ajuda prevenção e continuidade.", "attention", "asma_documentacao"),
            ],
        ),
        EmergencyProtocolRead(
            id="intoxicacao",
            slug="intoxicacao-medicamentosa",
            title="Intoxicação medicamentosa",
            category="Toxicologia",
            summary="Triagem orientativa inicial para exposição medicamentosa com segurança, ABCDE, identificação da substância e CIAT.",
            clinical_goal="Organizar informações essenciais e acionar referência toxicológica sem induzir condutas inseguras.",
            severity_level="high",
            audience="Profissionais de saúde e triagem regulada",
            source_name="Anvisa / Renaciat - Disque-Intoxicação",
            source_url="https://www.gov.br/anvisa/pt-br/assuntos/fiscalizacao-e-monitoramento/renaciat",
            source_version="portal Anvisa consultado em 2026",
            last_reviewed_at="2026-07-11",
            disclaimer=common_disclaimer,
            red_flags=["rebaixamento", "convulsão", "instabilidade", "ingestão intencional", "múltiplas substâncias", "criança"],
            immediate_measures=["segurança da cena", "ABCDE", "não induzir vômito", "identificar substância/dose/tempo", "acionar CIAT/Disque-Intoxicação"],
            referral_criteria=["qualquer sintoma sistêmico", "dose desconhecida", "substância de alto risco", "tentativa de autoextermínio"],
            monitoring=["consciência", "sinais vitais", "glicemia", "ECG quando indicado", "evolução neurológica"],
            documentation_items=["substância", "dose estimada", "horário", "embalagem", "coingestões", "orientação do CIAT"],
            do_not_apply_when=["exposição ocupacional/química complexa exige protocolo específico e segurança ambiental"],
            human_judgment_points=["descontaminação", "antídotos", "observação", "risco psiquiátrico"],
            safety_notes=["Não orientar vômito, leite, carvão ou antídoto sem protocolo/CIAT."],
            context_fields=[
                {"name": "substance", "label": "Substância suspeita", "field_type": "text", "required": True},
                {"name": "time_since_exposure_minutes", "label": "Tempo desde exposição", "field_type": "number", "unit": "min"},
                {"name": "intentional", "label": "Exposição intencional", "field_type": "boolean"},
            ],
            steps=[
                _step(1, "Garantir segurança", "Avaliar cena, EPI e risco de exposição secundária.", "Protege equipe e paciente.", "high", "intoxicacao_seguranca"),
                _step(2, "ABCDE e sinais vitais", "Priorizar via aérea, respiração, circulação e consciência.", "Sintomas sistêmicos mudam prioridade.", "critical", "intoxicacao_abcde"),
                _step(3, "Não induzir vômito", "Evitar medidas caseiras ou descontaminação sem orientação.", "Condutas inadequadas podem agravar lesão.", "critical", "intoxicacao_nao_induzir"),
                _step(4, "Identificar substância", "Registrar nome, dose, horário, coingestões e embalagem.", "CIAT depende dessas informações.", "high", "intoxicacao_identificacao"),
                _step(5, "Acionar CIAT/Disque-Intoxicação", "Usar rede toxicológica/regulação e registrar orientação.", "Antídotos e observação dependem de orientação especializada.", "high", "intoxicacao_renaciat"),
            ],
        ),
    ]


def _step(
    order: int,
    title: str,
    action: str,
    explanation: str,
    warning_level: str,
    evidence_ref: str,
) -> dict[str, object]:
    return {
        "order": order,
        "title": title,
        "action": action,
        "explanation": explanation,
        "warning_level": warning_level,
        "requires_human_judgment": True,
        "evidence_ref": evidence_ref,
    }
