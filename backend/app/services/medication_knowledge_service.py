from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field, ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import (
    ActiveIngredientModel,
    MedicationKnowledgeCurationModel,
    UserModel,
)
from app.schemas.medication_knowledge_schema import (
    MedicationBulkImportRequest,
    MedicationKnowledgeLookupRequest,
    MedicationKnowledgeReviewRequest,
)
from app.services.ai_settings import AIConfigurationError, AISettingsService
from app.services.audit_service import AuditService
from app.services.normalizer import normalize_text


class MedicationKnowledgePayload(BaseModel):
    active_ingredient: str = ""
    dcb_name: str = ""
    synonyms: list[str] = Field(default_factory=list)
    brand_names: list[str] = Field(default_factory=list)
    therapeutic_class: str = ""
    therapeutic_classes: list[str] = Field(default_factory=list)
    jurisdiction: str = "BR"
    source_name: str = ""
    source_url: str | None = None
    validation_status: str = "pending_review"
    max_daily_dose: float | None = None
    dose_mg_per_kg: float | None = None
    contraindications: list[str] = Field(default_factory=list)
    adverse_effects: list[str] = Field(default_factory=list)
    interactions: list[str] = Field(default_factory=list)
    renal_caution: bool = False
    hepatic_caution: bool = False
    psychiatric_cautions: list[str] = Field(default_factory=list)
    reproductive_cautions: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)


class MedicationKnowledgeService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def lookup(
        self,
        payload: MedicationKnowledgeLookupRequest,
        *,
        user: UserModel,
    ) -> MedicationKnowledgeCurationModel:
        extracted, provider, model = self._extract_payload(payload)
        item = MedicationKnowledgeCurationModel(
            query=payload.query,
            source_name=payload.source_name,
            source_url=payload.source_url,
            source_text_excerpt=(payload.source_text or "")[:2000],
            extracted_payload=extracted.model_dump(mode="json"),
            provider=provider,
            model=model,
            validation_status="pending_review",
            review_status="pending_review",
            created_by=user.id,
        )
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        AuditService(self.db).record_action(
            user=user,
            action="medication_knowledge.lookup",
            resource_type="medication_knowledge_curation",
            resource_id=str(item.id),
            status=item.review_status,
            details={
                "query": payload.query,
                "source_name": payload.source_name,
                "source_url": payload.source_url,
                "provider": provider,
                "model": model,
                "validation_status": item.validation_status,
                "secret_logged": False,
            },
        )
        return item

    def bulk_import(
        self,
        payload: MedicationBulkImportRequest,
        *,
        user: UserModel,
    ) -> list[MedicationKnowledgeCurationModel]:
        created: list[MedicationKnowledgeCurationModel] = []
        for raw in payload.items:
            normalized = self._payload_from_raw(raw, payload.source_name, payload.source_url)
            if payload.dry_run:
                continue
            item = MedicationKnowledgeCurationModel(
                query=normalized.active_ingredient or normalized.dcb_name or "sem_nome",
                source_name=payload.source_name,
                source_url=payload.source_url,
                source_text_excerpt="importacao_lote",
                extracted_payload=normalized.model_dump(mode="json"),
                provider="bulk_import",
                model=None,
                validation_status="pending_review",
                review_status="pending_review",
                created_by=user.id,
            )
            self.db.add(item)
            created.append(item)
        self.db.commit()
        for item in created:
            self.db.refresh(item)
        AuditService(self.db).record_action(
            user=user,
            action="medication_knowledge.bulk_import",
            resource_type="medication_knowledge_curation",
            resource_id=None,
            status="dry_run" if payload.dry_run else "pending_review",
            details={
                "items_received": len(payload.items),
                "items_created": len(created),
                "source_name": payload.source_name,
                "dry_run": payload.dry_run,
                "secret_logged": False,
            },
        )
        return created

    def list_queue(
        self, review_status: str | None = None
    ) -> list[MedicationKnowledgeCurationModel]:
        stmt = select(MedicationKnowledgeCurationModel).order_by(
            MedicationKnowledgeCurationModel.created_at.desc()
        )
        if review_status:
            stmt = stmt.where(MedicationKnowledgeCurationModel.review_status == review_status)
        return list(self.db.scalars(stmt))

    def review(
        self,
        item_id: int,
        payload: MedicationKnowledgeReviewRequest,
        *,
        user: UserModel,
    ) -> MedicationKnowledgeCurationModel:
        item = self.db.get(MedicationKnowledgeCurationModel, item_id)
        if item is None:
            raise ValueError("Item de curadoria nao encontrado.")
        final_payload = payload.edited_payload or item.extracted_payload or {}
        if payload.decision == "approve":
            item.review_status = "approved"
            item.validation_status = "curated"
            item.extracted_payload = final_payload
            self._upsert_active_ingredient(final_payload)
        else:
            item.review_status = "rejected"
            item.validation_status = "rejected"
        item.reviewed_by = user.id
        item.reviewed_at = datetime.now(UTC)
        self.db.commit()
        self.db.refresh(item)
        AuditService(self.db).record_action(
            user=user,
            action="medication_knowledge.review",
            resource_type="medication_knowledge_curation",
            resource_id=str(item.id),
            status=item.review_status,
            details={
                "decision": payload.decision,
                "validation_status": item.validation_status,
                "justification": payload.justification,
                "query": item.query,
                "secret_logged": False,
            },
        )
        return item

    def _extract_payload(
        self, payload: MedicationKnowledgeLookupRequest
    ) -> tuple[MedicationKnowledgePayload, str, str | None]:
        config = AISettingsService(self.db).runtime_config()
        if config.enable_external_calls and payload.source_text:
            try:
                raw = AISettingsService(self.db).complete_json(
                    system_instructions=_medication_extraction_instructions(),
                    payload={
                        "query": payload.query,
                        "source_name": payload.source_name,
                        "source_url": payload.source_url,
                        "source_text": payload.source_text[:12000],
                    },
                    purpose="medication_knowledge_extraction",
                    config=config,
                )
                extracted = MedicationKnowledgePayload.model_validate(raw)
                extracted.validation_status = "pending_review"
                extracted.source_name = extracted.source_name or payload.source_name
                extracted.source_url = extracted.source_url or payload.source_url
                return extracted, config.provider, config.model
            except (AIConfigurationError, ValidationError, ValueError):
                pass
        return self._fallback_payload(payload), "fallback", "deterministic"

    def _fallback_payload(
        self, payload: MedicationKnowledgeLookupRequest
    ) -> MedicationKnowledgePayload:
        source_text = payload.source_text or ""
        aliases = _terms_after(source_text, ["sinonimos", "nomes comerciais", "marcas"])
        return MedicationKnowledgePayload(
            active_ingredient=payload.query.strip(),
            dcb_name=payload.query.strip(),
            synonyms=aliases[:8],
            brand_names=[],
            therapeutic_class="pendente_de_revisao",
            therapeutic_classes=["pendente_de_revisao"],
            jurisdiction="BR",
            source_name=payload.source_name,
            source_url=payload.source_url,
            validation_status="pending_review",
            limitations=[
                "Fallback local nao interpreta bula completa; revisar fonte oficial.",
                "Dados extraidos por IA/fallback ficam pendentes e nao substituem Anvisa/DCB.",
            ],
        )

    def _payload_from_raw(
        self,
        raw: dict[str, Any],
        source_name: str,
        source_url: str | None,
    ) -> MedicationKnowledgePayload:
        active = str(raw.get("active_ingredient") or raw.get("dcb_name") or raw.get("name") or "")
        classes = raw.get("therapeutic_classes") or raw.get("therapeutic_class") or []
        if isinstance(classes, str):
            classes = [classes]
        return MedicationKnowledgePayload(
            active_ingredient=active,
            dcb_name=str(raw.get("dcb_name") or active),
            synonyms=_as_list(raw.get("synonyms")),
            brand_names=_as_list(raw.get("brand_names")),
            therapeutic_class=str(raw.get("therapeutic_class") or (classes[0] if classes else "")),
            therapeutic_classes=[str(item) for item in classes],
            jurisdiction=str(raw.get("jurisdiction") or "BR"),
            source_name=str(raw.get("source_name") or source_name),
            source_url=str(raw.get("source_url") or source_url or "") or None,
            validation_status="pending_review",
            max_daily_dose=_number(raw.get("max_daily_dose") or raw.get("max_daily_dose_mg")),
            dose_mg_per_kg=_number(raw.get("dose_mg_per_kg")),
            contraindications=_as_list(raw.get("contraindications")),
            adverse_effects=_as_list(raw.get("adverse_effects")),
            interactions=_as_list(raw.get("interactions")),
            renal_caution=bool(raw.get("renal_caution")),
            hepatic_caution=bool(raw.get("hepatic_caution")),
            psychiatric_cautions=_as_list(raw.get("psychiatric_cautions")),
            reproductive_cautions=_as_list(raw.get("reproductive_cautions")),
            limitations=["Importado como pendente de revisao humana."],
        )

    def _upsert_active_ingredient(self, payload: dict[str, Any]) -> None:
        name = str(payload.get("dcb_name") or payload.get("active_ingredient") or "").strip()
        if not name:
            return
        normalized = normalize_text(name)
        existing = self.db.scalar(
            select(ActiveIngredientModel).where(ActiveIngredientModel.normalized_name == normalized)
        )
        therapeutic_classes = _as_list(payload.get("therapeutic_classes")) or _as_list(
            payload.get("therapeutic_class")
        )
        if existing is None:
            self.db.add(
                ActiveIngredientModel(
                    dcb_name=name,
                    normalized_name=normalized,
                    synonyms=_as_list(payload.get("synonyms")),
                    therapeutic_classes=therapeutic_classes,
                    common_brands=_as_list(payload.get("brand_names")),
                    jurisdiction=str(payload.get("jurisdiction") or "BR"),
                    source=str(payload.get("source_name") or "curadoria_prescripta"),
                    validation_status="curated",
                )
            )
            return
        existing.synonyms = _as_list(payload.get("synonyms"))
        existing.therapeutic_classes = therapeutic_classes
        existing.common_brands = _as_list(payload.get("brand_names"))
        existing.source = str(payload.get("source_name") or existing.source)
        existing.validation_status = "curated"


def _medication_extraction_instructions() -> str:
    return """
Voce estrutura conhecimento farmacologico para curadoria humana no Prescripta.
Use somente o texto/fonte enviados. Nao invente bula, dose, interacao ou efeito.
Retorne JSON com: active_ingredient, dcb_name, synonyms, brand_names,
therapeutic_class, therapeutic_classes, jurisdiction, source_name, source_url,
validation_status, max_daily_dose, dose_mg_per_kg, contraindications,
adverse_effects, interactions, renal_caution, hepatic_caution,
psychiatric_cautions, reproductive_cautions, limitations.
Sempre use validation_status=pending_review.
""".strip()


def _as_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip()[:180] for item in value if str(item).strip()]
    text = str(value).strip()
    if not text:
        return []
    return [item.strip()[:180] for item in text.replace(";", ",").split(",") if item.strip()]


def _number(value: Any) -> float | None:
    try:
        if value in {None, ""}:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _terms_after(text: str, markers: list[str]) -> list[str]:
    lowered = normalize_text(text)
    found: list[str] = []
    for marker in markers:
        index = lowered.find(marker)
        if index < 0:
            continue
        fragment = text[index : index + 300]
        found.extend(_as_list(fragment.split(":", 1)[-1]))
    return list(dict.fromkeys(found))
