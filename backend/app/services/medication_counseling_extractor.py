from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Protocol

from sqlalchemy.orm import Session

from app.core.config import Settings, settings
from app.database.models import MedicationModel
from app.knowledge.retriever import retrieve
from app.schemas.counseling_schema import CounselingEvidence, MedicationCounselingProviderOutput
from app.services.adverse_effect_taxonomy import (
    category_for_code,
    label_for_effect,
    normalize_effect_list,
)
from app.services.ai_settings import AISettingsService
from app.services.normalizer import normalize_text

PROVIDER_INSTRUCTIONS = """
Leia apenas os trechos fornecidos.
Não use conhecimento externo não fornecido.
Não invente efeitos.
Se não encontrar evidência, marque como insufficient_evidence.
Preencha somente categorias suportadas.
Cite source_id/trecho quando possível.
Gere resumo curto para paciente e resumo técnico para profissional.
"""


@dataclass(frozen=True)
class CounselingSourceContext:
    source_id: str
    jurisdiction: str
    source_name: str
    source_url: str | None
    source_version: str | None
    source_text: str
    evidence: list[CounselingEvidence]


@dataclass(frozen=True)
class CounselingExtractionRequest:
    active_ingredient: str
    jurisdiction: str
    source_text: str
    source_id: str
    source_name: str
    source_url: str | None
    source_version: str | None
    patient_context: dict
    evidence: list[CounselingEvidence]


class CounselingProvider(Protocol):
    provider_name: str

    def extract(self, request: CounselingExtractionRequest) -> dict:
        raise NotImplementedError


class FallbackDeterministicProvider:
    provider_name = "fallback_deterministic"

    KEYWORDS = {
        "insonia": ("insonia",),
        "sonolencia": ("sonolencia", "sono", "sonolento"),
        "sedacao": ("sedacao", "sedativo"),
        "alteracao_atencao_reflexos": ("atencao", "reflexos", "alerta"),
        "tontura": ("tontura", "tonteira"),
        "confusao": ("confusao",),
        "fadiga": ("fadiga", "cansaco"),
        "dirigir": ("dirigir", "direcao", "veiculos"),
        "operar_maquinas": ("operar maquinas", "maquinas"),
        "trabalho_em_altura": ("trabalho em altura", "altura"),
        "atividade_de_risco": ("atividade de risco",),
        "risco_de_queda": ("queda", "quedas", "risco de queda"),
        "alteracao_humor": ("humor",),
        "ansiedade": ("ansiedade",),
        "irritabilidade": ("irritabilidade",),
        "piora_psiquiatrica": ("piora psiquiatrica", "ideacao suicida"),
        "agitacao": ("agitacao",),
        "apatia": ("apatia",),
        "risco_serotoninergico": ("serotoninergico", "serotonina"),
        "alteracao_apetite": ("apetite",),
        "aumento_apetite": ("aumento do apetite",),
        "reducao_apetite": ("reducao do apetite", "perda de apetite"),
        "ganho_peso": ("ganho de peso",),
        "perda_peso": ("perda de peso",),
        "alteracao_glicemica": ("glicemia", "glicemica"),
        "baixa_libido": ("baixa libido", "libido"),
        "disfuncao_sexual": ("disfuncao sexual",),
        "alteracao_ejaculatoria": ("ejaculacao", "ejaculatoria"),
        "erecao_persistente_dolorosa": ("priapismo", "erecao persistente"),
        "alteracao_ciclo_menstrual": ("ciclo menstrual",),
        "contracepcao": ("contracepcao", "contraceptivo", "anticoncepcional"),
        "gestacao_lactacao": ("gestacao", "lactacao", "gravidez", "amamentacao"),
        "dor_cabeca": ("dor de cabeca", "cefaleia"),
        "tremor": ("tremor",),
        "convulsao": ("convulsao", "convulsoes"),
        "parestesia": ("parestesia",),
        "vertigem": ("vertigem",),
        "hipotermia": ("hipotermia",),
        "hipertermia": ("hipertermia", "febre alta"),
        "sudorese": ("sudorese", "suor"),
        "calafrios": ("calafrios",),
        "hipotensao": ("hipotensao", "queda de pressao"),
        "hipotensao_ortostatica": ("hipotensao ortostatica", "pressao ao levantar"),
        "palpitacao": ("palpitacao", "palpitacoes"),
        "arritmia": ("arritmia",),
        "sincope_desmaio": ("sincope", "desmaio"),
        "nausea": ("nausea",),
        "vomito": ("vomito", "vomitos"),
        "diarreia": ("diarreia",),
        "constipacao": ("constipacao",),
        "dor_abdominal": ("dor abdominal",),
        "sangramento_gastrointestinal": ("sangramento gastrointestinal",),
        "cautela_renal": ("renal", "rim"),
        "cautela_hepatica": ("hepatica", "figado"),
        "toxicidade_renal": ("toxicidade renal",),
        "toxicidade_hepatica": ("toxicidade hepatica", "hepatotoxicidade"),
        "monitoramento_renal": ("monitoramento renal",),
        "monitoramento_hepatico": ("monitoramento hepatico",),
        "procurar_atendimento": ("procurar atendimento", "atendimento"),
        "reacao_alergica": ("reacao alergica", "alergica"),
        "falta_de_ar": ("falta de ar",),
        "inchaco_importante": ("inchaco", "edema"),
        "desmaio": ("desmaio",),
        "sangramento_importante": ("sangramento importante",),
        "dor_intensa_persistente": ("dor intensa", "dor persistente"),
    }

    def extract(self, request: CounselingExtractionRequest) -> dict:
        normalized_source = normalize_text(request.source_text)
        effects = self._extract_effects(normalized_source)
        categories = self._categorize(effects)
        evidence = request.evidence[:5]
        confidence = self._confidence(effects, request.source_text)
        insufficient = confidence == "insufficient_evidence"
        main_effects = effects[:7]
        red_flags = categories["red_flags"] or ["procurar_atendimento"]
        if insufficient:
            main_effects = []
            red_flags = []

        return {
            "main_adverse_effects": main_effects,
            "patient_relevant_effects": main_effects,
            "activity_warnings": categories["daily_activity"],
            "driving_warning": "dirigir" in categories["daily_activity"]
            or bool({"tontura", "sedacao", "sonolencia", "hipotensao"} & set(effects)),
            "machine_operation_warning": "operar_maquinas" in categories["daily_activity"]
            or bool({"sedacao", "sonolencia", "alteracao_atencao_reflexos"} & set(effects)),
            "work_at_height_warning": "trabalho_em_altura" in categories["daily_activity"]
            or "risco_de_queda" in effects,
            "fall_risk_warning": bool({"risco_de_queda", "tontura", "hipotensao"} & set(effects)),
            "sedation_attention_warning": bool(
                {"sedacao", "sonolencia", "alteracao_atencao_reflexos", "confusao"} & set(effects)
            ),
            "sleep_effects": categories["sleep_attention"],
            "appetite_weight_effects": categories["appetite_weight"],
            "mood_behavior_effects": categories["mood_behavior"],
            "libido_sexual_effects": categories["sexual_reproductive"],
            "neurologic_effects": categories["neurologic"],
            "tremor_warning": "tremor" in effects,
            "headache_warning": "dor_cabeca" in effects,
            "temperature_regulation_effects": categories["temperature_autonomic"],
            "blood_pressure_warning": bool(
                {"hipotensao", "hipotensao_ortostatica", "sincope_desmaio"} & set(effects)
            ),
            "gastrointestinal_effects": categories["gastrointestinal"],
            "renal_effects": [
                item for item in categories["renal_hepatic"] if "renal" in item
            ],
            "hepatic_effects": [
                item for item in categories["renal_hepatic"] if "hepat" in item
            ],
            "reproductive_contraceptive_effects": [
                item
                for item in categories["sexual_reproductive"]
                if item in {"contracepcao", "gestacao_lactacao", "alteracao_ciclo_menstrual"}
            ],
            "red_flags": red_flags,
            "monitoring_required": self._monitoring(effects),
            "patient_friendly_summary": self._patient_summary(main_effects, insufficient),
            "professional_summary": self._professional_summary(effects, confidence),
            "source_ids": [request.source_id],
            "extracted_evidence": [item.model_dump() for item in evidence],
            "confidence": confidence,
            "requires_review": True,
        }

    def _extract_effects(self, normalized_source: str) -> list[str]:
        effects: list[str] = []
        for code, keywords in self.KEYWORDS.items():
            if any(keyword in normalized_source for keyword in keywords):
                effects.append(code)
        return normalize_effect_list(effects)

    def _categorize(self, effects: list[str]) -> dict[str, list[str]]:
        categories = {
            "sleep_attention": [],
            "daily_activity": [],
            "mood_behavior": [],
            "appetite_weight": [],
            "sexual_reproductive": [],
            "neurologic": [],
            "temperature_autonomic": [],
            "cardiovascular_pressure": [],
            "gastrointestinal": [],
            "renal_hepatic": [],
            "red_flags": [],
        }
        for effect in effects:
            category = category_for_code(effect)
            if category and category in categories:
                categories[category].append(effect)
        return categories

    def _confidence(self, effects: list[str], source_text: str) -> str:
        if len(normalize_text(source_text)) < 30 or "nenhum trecho especifico" in normalize_text(
            source_text
        ):
            return "insufficient_evidence"
        if len(effects) >= 5:
            return "medium"
        if effects:
            return "low"
        return "insufficient_evidence"

    def _monitoring(self, effects: list[str]) -> list[str]:
        monitoring: list[str] = []
        if "monitoramento_renal" in effects or "cautela_renal" in effects:
            monitoring.append("monitoramento_renal")
        if "monitoramento_hepatico" in effects or "cautela_hepatica" in effects:
            monitoring.append("monitoramento_hepatico")
        return monitoring

    def _patient_summary(self, effects: list[str], insufficient: bool) -> str:
        if insufficient:
            return (
                "Fonte insuficiente para resumo especifico. Orientar revisao da bula completa e "
                "confirmar dados clinicos antes da decisao."
            )
        labels = [label_for_effect(effect).lower() for effect in effects[:5]]
        return (
            "Pode exigir orientacao pratica sobre "
            f"{', '.join(labels)}. Procurar atendimento se houver reacao intensa "
            "ou piora importante."
        )

    def _professional_summary(self, effects: list[str], confidence: str) -> str:
        if confidence == "insufficient_evidence":
            return "Evidencia insuficiente nos trechos recuperados; manter revisao profissional."
        labels = [label_for_effect(effect).lower() for effect in effects[:8]]
        return (
            "Resumo extraido apenas dos trechos recuperados. Revisar orientacao sobre "
            f"{', '.join(labels)} e manter status deterministico separado."
        )


class OpenAICompatibleCounselingProvider:
    provider_name = "openai_compatible"

    def __init__(self, provider_name: str, app_settings: Settings | None = None) -> None:
        self.provider_name = provider_name
        self.settings = app_settings or settings

    def extract(self, request: CounselingExtractionRequest) -> dict:
        from openai import OpenAI

        client_kwargs = {"api_key": self.settings.ai_api_key or "local"}
        if self.settings.ai_base_url:
            client_kwargs["base_url"] = self.settings.ai_base_url
        client = OpenAI(**client_kwargs)
        response = client.responses.create(
            model=self.settings.ai_model,
            instructions=PROVIDER_INSTRUCTIONS,
            input=json.dumps(
                {
                    "active_ingredient": request.active_ingredient,
                    "jurisdiction": request.jurisdiction,
                    "source_text": request.source_text,
                    "patient_context": request.patient_context,
                    "source_id": request.source_id,
                    "source_name": request.source_name,
                    "source_version": request.source_version,
                },
                ensure_ascii=False,
            ),
            text={"format": {"type": "json_object"}, "verbosity": "low"},
        )
        return json.loads(response.output_text)


class GPTProvider(OpenAICompatibleCounselingProvider):
    def __init__(self, app_settings: Settings | None = None) -> None:
        super().__init__("gpt", app_settings)


class LlamaProvider(OpenAICompatibleCounselingProvider):
    def __init__(self, app_settings: Settings | None = None) -> None:
        super().__init__("llama", app_settings)


class GeminiProvider:
    provider_name = "gemini"

    def extract(self, request: CounselingExtractionRequest) -> dict:
        return FallbackDeterministicProvider().extract(request)


class ConfiguredAIProvider:
    def __init__(self, db: Session, app_settings: Settings | None = None) -> None:
        self.settings = app_settings or settings
        self.ai_settings = AISettingsService(db, self.settings)
        self.config = self.ai_settings.runtime_config()
        self.provider_name = self.config.provider

    def extract(self, request: CounselingExtractionRequest) -> dict:
        return self.ai_settings.complete_json(
            system_instructions=PROVIDER_INSTRUCTIONS,
            payload={
                "active_ingredient": request.active_ingredient,
                "jurisdiction": request.jurisdiction,
                "source_text": request.source_text,
                "patient_context": request.patient_context,
                "source_id": request.source_id,
                "source_name": request.source_name,
                "source_url": request.source_url,
                "source_version": request.source_version,
                "supported_output_schema": "MedicationCounselingProviderOutput",
            },
            purpose="medication_counseling_extraction",
            config=self.config,
        )


class MedicationCounselingExtractor:
    def __init__(
        self,
        provider: CounselingProvider | None = None,
        app_settings: Settings | None = None,
        db: Session | None = None,
    ) -> None:
        self.settings = app_settings or settings
        self.db = db
        self.provider = provider or self._provider_from_settings()

    def extract(
        self,
        medication: MedicationModel,
        *,
        source_text: str | None = None,
        patient_context: dict | None = None,
    ) -> tuple[MedicationCounselingProviderOutput, CounselingSourceContext, str]:
        context = self.build_source_context(medication, source_text=source_text)
        request = CounselingExtractionRequest(
            active_ingredient=medication.active_ingredient,
            jurisdiction=context.jurisdiction,
            source_text=context.source_text,
            source_id=context.source_id,
            source_name=context.source_name,
            source_url=context.source_url,
            source_version=context.source_version,
            patient_context=patient_context or {},
            evidence=context.evidence,
        )
        used_provider = self.provider.provider_name
        try:
            raw_output = self.provider.extract(request)
        except Exception:
            if not isinstance(self.provider, ConfiguredAIProvider):
                raise
            fallback = FallbackDeterministicProvider()
            raw_output = fallback.extract(request)
            used_provider = fallback.provider_name
        output = self.validate_output(raw_output)
        return output, context, used_provider

    def build_source_context(
        self,
        medication: MedicationModel,
        *,
        source_text: str | None = None,
    ) -> CounselingSourceContext:
        source_id = f"medication-{medication.id or 'new'}-{medication.validation_status}"
        source_name = medication.knowledge_source or medication.evidence_source_type
        source_url = medication.evidence_source_url
        source_version = medication.validation_status
        jurisdiction = medication.source_jurisdiction or "BR"

        if source_text:
            evidence = [
                CounselingEvidence(
                    source_id=source_id,
                    source_name=source_name or "Fonte informada",
                    jurisdiction=jurisdiction,
                    source_url=source_url,
                    excerpt=source_text[:700],
                    validation_status=medication.validation_status,
                )
            ]
            return CounselingSourceContext(
                source_id=source_id,
                jurisdiction=jurisdiction,
                source_name=source_name or "Fonte informada",
                source_url=source_url,
                source_version=source_version,
                source_text=source_text,
                evidence=evidence,
            )

        hits = retrieve(
            [
                medication.brand_name,
                medication.active_ingredient,
                *(medication.commercial_aliases or []),
                medication.therapeutic_class,
                *(medication.therapeutic_classes or []),
                *(medication.relevant_adverse_effects or []),
                *(medication.neuropsychiatric_cautions or []),
                *(medication.reproductive_cautions or []),
                medication.monitoring_notes or "",
            ],
            limit=5,
        )
        if hits:
            evidence = [
                CounselingEvidence(
                    source_id=hit.source,
                    source_name=str(hit.metadata.get("source_name") or hit.source),
                    jurisdiction=str(hit.metadata.get("jurisdiction") or jurisdiction),
                    source_url=hit.metadata.get("source_url"),
                    excerpt=hit.excerpt,
                    validation_status=str(hit.metadata.get("validation_status") or "demo"),
                )
                for hit in hits
            ]
            source_text_from_hits = "\n\n".join(item.excerpt for item in evidence)
            return CounselingSourceContext(
                source_id=evidence[0].source_id,
                jurisdiction=evidence[0].jurisdiction,
                source_name=evidence[0].source_name,
                source_url=evidence[0].source_url,
                source_version=str(hits[0].metadata.get("version") or source_version),
                source_text=source_text_from_hits,
                evidence=evidence,
            )

        fallback_text = "\n".join(
            item
            for item in [
                medication.notes or "",
                medication.monitoring_notes or "",
                " ".join(medication.relevant_adverse_effects or []),
                " ".join(medication.neuropsychiatric_cautions or []),
                " ".join(medication.reproductive_cautions or []),
            ]
            if item
        )
        if not fallback_text:
            fallback_text = "Nenhum trecho especifico foi encontrado na base interna demonstrativa."
        evidence = [
            CounselingEvidence(
                source_id=source_id,
                source_name=source_name or "Cadastro demonstrativo",
                jurisdiction=jurisdiction,
                source_url=source_url,
                excerpt=fallback_text[:700],
                validation_status=medication.validation_status,
            )
        ]
        return CounselingSourceContext(
            source_id=source_id,
            jurisdiction=jurisdiction,
            source_name=source_name or "Cadastro demonstrativo",
            source_url=source_url,
            source_version=source_version,
            source_text=fallback_text,
            evidence=evidence,
        )

    def validate_output(self, raw_output: dict) -> MedicationCounselingProviderOutput:
        output = MedicationCounselingProviderOutput.model_validate(raw_output)
        values = output.model_dump()
        for field in (
            "main_adverse_effects",
            "patient_relevant_effects",
            "activity_warnings",
            "sleep_effects",
            "appetite_weight_effects",
            "mood_behavior_effects",
            "libido_sexual_effects",
            "neurologic_effects",
            "temperature_regulation_effects",
            "gastrointestinal_effects",
            "renal_effects",
            "hepatic_effects",
            "reproductive_contraceptive_effects",
            "red_flags",
            "monitoring_required",
        ):
            values[field] = normalize_effect_list(values[field])
        return MedicationCounselingProviderOutput.model_validate(values)

    def _provider_from_settings(self) -> CounselingProvider:
        if self.db is not None:
            configured = ConfiguredAIProvider(self.db, self.settings)
            if configured.config.enable_external_calls and configured.config.provider != "fallback":
                return configured
            return FallbackDeterministicProvider()
        provider = self.settings.ai_provider.strip().lower()
        external_ready = self.settings.ai_api_key.strip() or self.settings.ai_base_url.strip()
        if provider == "openai" and external_ready and self.settings.ai_enable_external_calls:
            return GPTProvider(self.settings)
        if (
            provider in {"llama", "local", "ollama"}
            and external_ready
            and self.settings.ai_enable_external_calls
        ):
            return LlamaProvider(self.settings)
        if provider == "gemini" and external_ready and self.settings.ai_enable_external_calls:
            return GeminiProvider()
        return FallbackDeterministicProvider()
