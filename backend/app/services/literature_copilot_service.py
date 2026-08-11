from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import EvidenceExtractionModel, EvidenceSourceModel, UserModel
from app.schemas.research_v092_schema import EvidenceExtractionCreate
from app.services.audit_service import AuditService
from app.services.canonical_json import canonical_sha256
from app.services.evidence_service import EvidenceError

EXTRACTION_FIELDS = (
    "study_design",
    "population",
    "sample_size",
    "exposure",
    "comparator",
    "outcomes",
    "follow_up",
    "methods",
    "adjustment",
    "effect_measures",
    "limitations",
    "funding_conflicts",
)
INJECTION_MARKERS = (
    "ignore previous instructions",
    "reveal system prompt",
    "export patient data",
    "call another tool",
)


class LiteratureCopilotService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def extract(
        self, payload: EvidenceExtractionCreate, actor: UserModel
    ) -> EvidenceExtractionModel:
        source = self.db.get(EvidenceSourceModel, payload.source_id)
        if source is None or source.institution_id != actor.institution_id:
            raise EvidenceError("Fonte de evidência não encontrada.")
        content_casefold = payload.content.casefold()
        prompt_injection = any(marker in content_casefold for marker in INJECTION_MARKERS)
        fields = {
            field: {
                "value": None,
                "source_id": source.id,
                "locator": None,
                "support_status": "not_found",
                "extraction_status": "not_found",
            }
            for field in EXTRACTION_FIELDS
        }
        claims: list[dict] = []
        seen_fields: set[str] = set()
        for candidate in payload.candidates:
            if candidate.field in seen_fields:
                raise EvidenceError("Cada campo pode ter somente um candidate por extração.")
            seen_fields.add(candidate.field)
            supported = candidate.supporting_text.casefold() in content_casefold
            support_status = "supported" if supported else "not_found"
            value = candidate.value if supported else None
            fields[candidate.field] = {
                "value": value,
                "source_id": source.id,
                "locator": candidate.locator if supported else None,
                "support_status": support_status,
                "extraction_status": "extracted" if supported else "not_found",
            }
            claims.append(
                {
                    "field": candidate.field,
                    "value": value,
                    "source_id": source.id,
                    "locator": candidate.locator if supported else None,
                    "support_status": support_status,
                }
            )
        extraction = EvidenceExtractionModel(
            source_id=source.id,
            institution_id=actor.institution_id,
            schema_version=payload.schema_version,
            content_hash=canonical_sha256(payload.content),
            extracted_fields=fields,
            claims=claims,
            prompt_injection_detected=prompt_injection,
            status="pending_review",
            created_by_user_id=actor.id,
        )
        self.db.add(extraction)
        self.db.flush()
        AuditService(self.db).record_action(
            user=actor,
            action="evidence.extract",
            resource_type="evidence_extraction",
            resource_id=extraction.id,
            status="pending_review",
            details={
                "source_id": source.id,
                "prompt_injection_detected": prompt_injection,
                "supported_fields": sum(
                    item["support_status"] == "supported" for item in fields.values()
                ),
                "raw_content_persisted": False,
            },
        )
        return extraction

    def list_extractions(
        self, source_id: str, actor: UserModel
    ) -> list[EvidenceExtractionModel]:
        source = self.db.get(EvidenceSourceModel, source_id)
        if source is None or source.institution_id != actor.institution_id:
            raise EvidenceError("Fonte de evidência não encontrada.")
        return list(
            self.db.scalars(
                select(EvidenceExtractionModel)
                .where(
                    EvidenceExtractionModel.source_id == source_id,
                    EvidenceExtractionModel.institution_id == actor.institution_id,
                )
                .order_by(EvidenceExtractionModel.created_at.desc())
            )
        )

    def synthesize(self, source_ids: list[str], actor: UserModel) -> dict:
        if not source_ids or len(source_ids) > 30:
            raise EvidenceError("Síntese exige entre 1 e 30 fontes registradas.")
        extractions: list[EvidenceExtractionModel] = []
        for source_id in source_ids:
            source = self.db.get(EvidenceSourceModel, source_id)
            if source is None or source.institution_id != actor.institution_id:
                raise EvidenceError("Fonte de evidência fora do escopo autorizado.")
            extraction = self.db.scalar(
                select(EvidenceExtractionModel)
                .where(
                    EvidenceExtractionModel.source_id == source_id,
                    EvidenceExtractionModel.institution_id == actor.institution_id,
                )
                .order_by(EvidenceExtractionModel.created_at.desc())
            )
            if extraction:
                extractions.append(extraction)
        designs = sorted(
            {
                str(item.extracted_fields["study_design"]["value"])
                for item in extractions
                if item.extracted_fields.get("study_design", {}).get("value")
            }
        )
        supported_outcomes = [
            {
                "source_id": item.source_id,
                "value": item.extracted_fields["outcomes"]["value"],
                "locator": item.extracted_fields["outcomes"]["locator"],
            }
            for item in extractions
            if item.extracted_fields.get("outcomes", {}).get("support_status") == "supported"
        ]
        return {
            "status": "proposal_only",
            "source_ids": source_ids,
            "study_designs": designs,
            "supported_outcomes": supported_outcomes,
            "gaps": [
                field
                for field in EXTRACTION_FIELDS
                if not any(
                    item.extracted_fields.get(field, {}).get("support_status") == "supported"
                    for item in extractions
                )
            ],
            "guideline_generated": False,
            "human_review_required": True,
        }
