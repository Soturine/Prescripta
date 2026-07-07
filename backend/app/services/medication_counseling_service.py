from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import MedicationCounselingSummaryModel, MedicationModel
from app.schemas.counseling_schema import (
    MedicationCounselingReviewRequest,
    MedicationCounselingSummaryRead,
)
from app.services.adverse_effect_taxonomy import normalize_effect_list
from app.services.medication_counseling_extractor import MedicationCounselingExtractor

STATUS_PRIORITY = {
    "validated": 0,
    "curated": 1,
    "pending_review": 2,
    "generated_by_ai": 3,
    "obsolete": 4,
    "rejected": 5,
}


class MedicationCounselingService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_best_for_medication(
        self, medication: MedicationModel
    ) -> MedicationCounselingSummaryModel | None:
        conditions = [MedicationCounselingSummaryModel.medication_id == medication.id]
        if medication.active_ingredient_id:
            conditions.append(
                MedicationCounselingSummaryModel.active_ingredient_id
                == medication.active_ingredient_id
            )
        summaries = list(
            self.db.scalars(
                select(MedicationCounselingSummaryModel).where(
                    MedicationCounselingSummaryModel.validation_status != "rejected",
                    MedicationCounselingSummaryModel.validation_status != "obsolete",
                    conditions[0] if len(conditions) == 1 else conditions[0] | conditions[1],
                )
            )
        )
        if not summaries:
            return None
        return sorted(
            summaries,
            key=lambda item: (
                STATUS_PRIORITY.get(item.validation_status, 99),
                item.updated_at,
            ),
            reverse=False,
        )[0]

    def generate_for_medication(
        self,
        medication: MedicationModel,
        *,
        source_text: str | None = None,
        force_regenerate: bool = False,
        provider_name: str | None = None,
    ) -> MedicationCounselingSummaryModel:
        extractor = MedicationCounselingExtractor(db=self.db)
        context = extractor.build_source_context(medication, source_text=source_text)
        if not force_regenerate:
            cached = self._cached_summary(medication, context.source_id, context.source_version)
            if cached is not None:
                return cached

        output, context, used_provider = extractor.extract(
            medication,
            source_text=source_text,
            patient_context={"functional_profile": {}},
        )
        generated_by = (
            "ai_provider"
            if used_provider in {"gpt", "llama", "gemini", "openai", "ollama", "openai_compatible"}
            else "fallback_deterministic"
        )
        summary = MedicationCounselingSummaryModel(
            active_ingredient_id=medication.active_ingredient_id,
            medication_id=medication.id,
            source_id=context.source_id,
            jurisdiction=context.jurisdiction,
            source_name=context.source_name,
            source_url=context.source_url,
            source_version=context.source_version,
            validation_status="pending_review",
            generated_by=generated_by,
            provider_name=provider_name or used_provider,
            confidence=output.confidence,
            requires_review=True,
            **self._summary_fields(output.model_dump()),
        )
        self.db.add(summary)
        self.db.commit()
        self.db.refresh(summary)
        return summary

    def review_summary(
        self,
        summary: MedicationCounselingSummaryModel,
        payload: MedicationCounselingReviewRequest,
    ) -> MedicationCounselingSummaryModel:
        for field in (
            "patient_friendly_summary",
            "professional_summary",
            "main_adverse_effects",
            "patient_relevant_effects",
            "activity_warnings",
            "red_flags",
        ):
            value = getattr(payload, field)
            if value is None:
                continue
            if isinstance(value, list):
                value = normalize_effect_list(value)
            setattr(summary, field, value)
        summary.validation_status = payload.validation_status
        summary.requires_review = payload.validation_status not in {"curated", "validated"}
        summary.generated_by = "manual_curated" if summary.validation_status in {
            "curated",
            "validated",
        } else summary.generated_by
        summary.updated_at = datetime.now(UTC)
        self.db.commit()
        self.db.refresh(summary)
        return summary

    def read_model(
        self, summary: MedicationCounselingSummaryModel | None
    ) -> MedicationCounselingSummaryRead | None:
        if summary is None:
            return None
        return MedicationCounselingSummaryRead.model_validate(summary)

    def _cached_summary(
        self,
        medication: MedicationModel,
        source_id: str,
        source_version: str | None,
    ) -> MedicationCounselingSummaryModel | None:
        query = select(MedicationCounselingSummaryModel).where(
            MedicationCounselingSummaryModel.source_id == source_id,
            MedicationCounselingSummaryModel.source_version == source_version,
            MedicationCounselingSummaryModel.validation_status.in_(
                ["validated", "curated", "pending_review", "generated_by_ai"]
            ),
        )
        if medication.active_ingredient_id:
            query = query.where(
                MedicationCounselingSummaryModel.active_ingredient_id
                == medication.active_ingredient_id
            )
        else:
            query = query.where(MedicationCounselingSummaryModel.medication_id == medication.id)
        summaries = list(self.db.scalars(query))
        if not summaries:
            return None
        return sorted(
            summaries,
            key=lambda item: STATUS_PRIORITY.get(item.validation_status, 99),
        )[0]

    def _summary_fields(self, values: dict) -> dict:
        values = dict(values)
        values.pop("source_ids", None)
        fields = {
            "main_adverse_effects",
            "patient_relevant_effects",
            "activity_warnings",
            "driving_warning",
            "machine_operation_warning",
            "work_at_height_warning",
            "fall_risk_warning",
            "sedation_attention_warning",
            "sleep_effects",
            "appetite_weight_effects",
            "mood_behavior_effects",
            "libido_sexual_effects",
            "neurologic_effects",
            "tremor_warning",
            "headache_warning",
            "temperature_regulation_effects",
            "blood_pressure_warning",
            "gastrointestinal_effects",
            "renal_effects",
            "hepatic_effects",
            "reproductive_contraceptive_effects",
            "red_flags",
            "monitoring_required",
            "patient_friendly_summary",
            "professional_summary",
            "extracted_evidence",
        }
        return {key: values[key] for key in fields if key in values}
