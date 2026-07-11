from __future__ import annotations

import hashlib
import re
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field, ValidationError, field_validator
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import (
    ClinicalImportBatchModel,
    EmergencyProtocolRunModel,
    PatientClinicalDocumentModel,
    PatientClinicalTimelineEventModel,
    PatientDocumentExtractionModel,
    PatientMedicationHistoryModel,
    PatientModel,
    UserModel,
)
from app.schemas.patient_history_schema import PatientClinicalDocumentCreate
from app.services.ai_settings import AIConfigurationError, AISettingsService
from app.services.audit_service import AuditService
from app.services.normalizer import merge_terms, normalize_text


class ClinicalDocumentExtractionPayload(BaseModel):
    medications: list[str] = Field(default_factory=list)
    allergies: list[str] = Field(default_factory=list)
    conditions: list[str] = Field(default_factory=list)
    observations: list[str] = Field(default_factory=list)
    lab_results: list[str] = Field(default_factory=list)
    adverse_reactions: list[str] = Field(default_factory=list)
    mental_health_factors: list[str] = Field(default_factory=list)
    reproductive_factors: list[str] = Field(default_factory=list)
    pregnancy_or_lactation: bool | None = None
    notes: list[str] = Field(default_factory=list)

    @field_validator(
        "medications",
        "allergies",
        "conditions",
        "observations",
        "lab_results",
        "adverse_reactions",
        "mental_health_factors",
        "reproductive_factors",
        "notes",
        mode="before",
    )
    @classmethod
    def clean_list(cls, value: object) -> list[str]:
        if not isinstance(value, list):
            return []
        clean: list[str] = []
        for item in value:
            text = str(item or "").strip()
            if text and "<" not in text and ">" not in text:
                clean.append(text[:180])
        return clean[:20]


class DuplicateClinicalDocumentError(ValueError):
    pass


class PatientHistoryService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_document(
        self,
        patient: PatientModel,
        payload: PatientClinicalDocumentCreate,
        user: UserModel,
    ) -> PatientClinicalDocumentModel:
        raw_text = payload.raw_text or ""
        file_hash = hashlib.sha256(
            (raw_text + repr(payload.structured_payload)).encode("utf-8")
        ).hexdigest()
        duplicate = self.db.scalar(
            select(PatientClinicalDocumentModel).where(
                PatientClinicalDocumentModel.patient_id == patient.id,
                PatientClinicalDocumentModel.file_hash == file_hash,
                PatientClinicalDocumentModel.document_type == payload.document_type,
                PatientClinicalDocumentModel.document_date == payload.document_date,
                PatientClinicalDocumentModel.source_system == payload.source_system,
            )
        )
        if duplicate is not None:
            raise DuplicateClinicalDocumentError(
                "Documento clínico duplicado para o paciente e a origem informados."
            )
        document = PatientClinicalDocumentModel(
            patient_id=patient.id,
            document_type=payload.document_type,
            title=payload.title,
            summary=payload.summary or raw_text[:240],
            source_type=payload.source_type,
            source_system=payload.source_system,
            document_date=payload.document_date,
            uploaded_by=user.id,
            raw_text=raw_text,
            structured_payload=payload.structured_payload,
            file_hash=file_hash,
            storage_path=payload.storage_path,
        )
        self.db.add(document)
        self.db.commit()
        self.db.refresh(document)
        self._timeline(
            patient_id=patient.id,
            event_type="document_uploaded",
            title=f"Laudo/documento: {document.title}",
            summary=document.summary,
            source_type=document.source_type,
            source_system=document.source_system,
            payload={"document_id": document.id, "document_type": document.document_type},
            user=user,
        )
        AuditService(self.db).record_action(
            user=user,
            action="patient.document.uploaded",
            resource_type="patient_document",
            resource_id=str(document.id),
            status=document.review_status,
            details={
                "patient_id": patient.id,
                "document_type": document.document_type,
                "source_type": document.source_type,
                "file_hash": document.file_hash,
                "secret_logged": False,
            },
        )
        return document

    def list_documents(self, patient_id: int) -> list[PatientClinicalDocumentModel]:
        return list(
            self.db.scalars(
                select(PatientClinicalDocumentModel)
                .where(PatientClinicalDocumentModel.patient_id == patient_id)
                .order_by(PatientClinicalDocumentModel.uploaded_at.desc())
            )
        )

    def extract_document(
        self,
        patient: PatientModel,
        document: PatientClinicalDocumentModel,
        user: UserModel,
    ) -> PatientDocumentExtractionModel:
        provider = "fallback"
        model = "deterministic"
        confidence = 0.42
        try:
            config = AISettingsService(self.db).runtime_config()
            if not config.enable_external_calls or config.provider == "fallback":
                raise AIConfigurationError("IA externa desabilitada.")
            raw = AISettingsService(self.db).complete_json(
                system_instructions=_document_extraction_prompt(),
                payload={
                    "document_type": document.document_type,
                    "source_type": document.source_type,
                    "text_minimized": self._minimize_text(document.raw_text, patient),
                    "structured_payload": document.structured_payload,
                    "allowed_status": "pending_review",
                },
                purpose="clinical_document_extraction",
                config=config,
            )
            parsed = ClinicalDocumentExtractionPayload.model_validate(raw)
            provider = config.provider
            model = config.model or "configured"
            confidence = 0.68
        except (AIConfigurationError, ValidationError, ValueError):
            parsed = self._fallback_extract(document)

        extraction = PatientDocumentExtractionModel(
            patient_id=patient.id,
            document_id=document.id,
            provider=provider,
            model=model,
            extracted_entities=parsed.model_dump(),
            confidence=confidence,
            validation_status="pending_review",
            review_status="pending_review",
        )
        document.extracted_entities = parsed.model_dump()
        document.confidence = confidence
        document.validation_status = "pending_review"
        document.review_status = "pending_review"
        self.db.add(extraction)
        self.db.commit()
        self.db.refresh(extraction)
        AuditService(self.db).record_action(
            user=user,
            action="patient.document.extracted",
            resource_type="patient_document",
            resource_id=str(document.id),
            status="pending_review",
            details={
                "patient_id": patient.id,
                "extraction_id": extraction.id,
                "provider": provider,
                "model": model,
                "confidence": confidence,
                "send_identifiable_data": False,
                "secret_logged": False,
            },
        )
        return extraction

    def review_extraction(
        self,
        patient: PatientModel,
        extraction: PatientDocumentExtractionModel,
        *,
        decision: str,
        accepted_entities: dict[str, Any] | None,
        user: UserModel,
        justification: str | None = None,
    ) -> PatientDocumentExtractionModel:
        now = datetime.now(UTC)
        document = self.db.get(PatientClinicalDocumentModel, extraction.document_id)
        if decision == "reject":
            extraction.review_status = "rejected"
            extraction.validation_status = "rejected"
            if document is not None:
                document.review_status = "rejected"
                document.validation_status = "rejected"
            status = "rejected"
        else:
            entities = accepted_entities or extraction.extracted_entities or {}
            self._apply_entities(patient, entities, document_id=extraction.document_id)
            extraction.review_status = "accepted"
            extraction.validation_status = "reviewed"
            if document is not None:
                document.review_status = "accepted"
                document.validation_status = "reviewed"
                document.reviewed_by = user.id
                document.reviewed_at = now
            status = "accepted"
            self._timeline(
                patient_id=patient.id,
                event_type="document_entities_reviewed",
                title="Itens do documento aplicados ao histórico",
                summary="Entidades extraídas foram revisadas por humano e aplicadas ao perfil.",
                source_type="document_extraction",
                source_system=document.source_system if document else None,
                payload={"document_id": extraction.document_id, "entities": entities},
                user=user,
                validation_status="reviewed",
            )
        extraction.reviewed_by = user.id
        extraction.reviewed_at = now
        self.db.commit()
        self.db.refresh(extraction)
        AuditService(self.db).record_action(
            user=user,
            action="patient.document.reviewed",
            resource_type="patient_document",
            resource_id=str(extraction.document_id),
            status=status,
            details={
                "patient_id": patient.id,
                "extraction_id": extraction.id,
                "decision": decision,
                "justification": justification,
                "secret_logged": False,
            },
        )
        return extraction

    def timeline(self, patient_id: int) -> list[dict[str, Any]]:
        events = [
            {
                "id": event.id,
                "event_type": event.event_type,
                "title": event.title,
                "summary": event.summary,
                "source_type": event.source_type,
                "source_system": event.source_system,
                "event_date": event.event_date.isoformat() if event.event_date else None,
                "created_at": event.created_at.isoformat(),
                "validation_status": event.validation_status,
                "payload": event.payload,
            }
            for event in self.db.scalars(
                select(PatientClinicalTimelineEventModel)
                .where(PatientClinicalTimelineEventModel.patient_id == patient_id)
                .order_by(PatientClinicalTimelineEventModel.created_at.desc())
            )
        ]
        protocol_runs = [
            {
                "id": run.id,
                "event_type": "protocol_run",
                "title": f"Protocolo: {run.protocol_title}",
                "summary": "; ".join(run.triage_flags or []) or run.status,
                "source_type": "protocol",
                "source_system": "Prescripta",
                "event_date": run.created_at.isoformat(),
                "created_at": run.created_at.isoformat(),
                "validation_status": run.status,
                "payload": {
                    "protocol_id": run.protocol_id,
                    "protocol_version": run.protocol_version,
                    "severity": run.protocol_severity,
                },
            }
            for run in self.db.scalars(
                select(EmergencyProtocolRunModel)
                .where(EmergencyProtocolRunModel.patient_id == patient_id)
                .order_by(EmergencyProtocolRunModel.created_at.desc())
            )
        ]
        return sorted(
            [*events, *protocol_runs],
            key=lambda item: str(item.get("created_at") or ""),
            reverse=True,
        )

    def knowledge_bundle(
        self,
        patient: PatientModel,
        *,
        include_identifiable: bool = False,
    ) -> dict[str, Any]:
        documents = self.list_documents(patient.id)
        reviewed_docs = [doc for doc in documents if doc.review_status == "accepted"]
        reviewed_entities = self._merge_reviewed_entities(reviewed_docs)
        imports = list(
            self.db.scalars(
                select(ClinicalImportBatchModel)
                .where(ClinicalImportBatchModel.patient_id == patient.id)
                .order_by(ClinicalImportBatchModel.imported_at.desc())
            )
        )
        medication_history = list(
            self.db.scalars(
                select(PatientMedicationHistoryModel)
                .where(PatientMedicationHistoryModel.patient_id == patient.id)
                .order_by(PatientMedicationHistoryModel.created_at.desc())
            )
        )
        protocol_runs = list(
            self.db.scalars(
                select(EmergencyProtocolRunModel)
                .where(EmergencyProtocolRunModel.patient_id == patient.id)
                .order_by(EmergencyProtocolRunModel.created_at.desc())
            )
        )
        missing = self._missing_data(patient, reviewed_docs)
        return {
            "patient_id": patient.id,
            "patient_reference": (
                patient.name if include_identifiable else f"Paciente #P-{patient.id:05d}"
            ),
            "generated_at": datetime.now(UTC).isoformat(),
            "send_identifiable_data": include_identifiable,
            "structured_profile": {
                "age": patient.age,
                "age_years": patient.age,
                "weight_kg": patient.weight_kg,
                "height_cm": patient.height_cm,
                "allergies": list(patient.allergies or []),
                "current_medications": list(patient.current_medications or []),
                "comorbidities": list(patient.comorbidities or []),
                "renal_condition": patient.renal_condition,
                "hepatic_condition": patient.hepatic_condition,
                "cardiac_condition": patient.cardiac_condition,
                "gastrointestinal_history": patient.gastrointestinal_history,
                "mental_health_factors": list(patient.mental_health_factors or []),
                "reproductive_gynecologic_factors": list(
                    patient.reproductive_gynecologic_factors or []
                ),
                "adverse_reactions": list(patient.adverse_reactions or []),
                "clinical_profile_completeness_score": (
                    patient.clinical_profile_completeness_score or 0
                ),
            },
            "documents": [
                {
                    "id": doc.id,
                    "document_type": doc.document_type,
                    "title": doc.title,
                    "summary": doc.summary,
                    "validation_status": doc.validation_status,
                    "review_status": doc.review_status,
                    "source_type": doc.source_type,
                    "source_system": doc.source_system,
                }
                for doc in reviewed_docs[:12]
            ],
            "reviewed_documents": [
                {
                    "id": doc.id,
                    "document_type": doc.document_type,
                    "title": doc.title,
                    "summary": doc.summary,
                    "validation_status": doc.validation_status,
                    "review_status": doc.review_status,
                    "source_type": doc.source_type,
                    "source_system": doc.source_system,
                }
                for doc in reviewed_docs[:12]
            ],
            "reviewed_entities": reviewed_entities,
            "reviewed_extractions": [
                {"document_id": doc.id, "entities": doc.extracted_entities}
                for doc in reviewed_docs[:12]
            ],
            "medication_history": [
                {
                    "id": item.id,
                    "medication_name": item.medication_name,
                    "active_ingredient": item.active_ingredient,
                    "status": item.status,
                    "validation_status": item.validation_status,
                    "source_document_id": item.source_document_id,
                }
                for item in medication_history[:20]
            ],
            "timeline": self.timeline(patient.id)[:20],
            "imported_context": [
                {
                    "id": batch.id,
                    "source_system": batch.source_system,
                    "source_type": batch.source_type,
                    "status": batch.status,
                    "imported_at": batch.imported_at.isoformat(),
                }
                for batch in imports[:10]
            ],
            "imports": [
                {
                    "id": batch.id,
                    "source_system": batch.source_system,
                    "source_type": batch.source_type,
                    "status": batch.status,
                    "imported_at": batch.imported_at.isoformat(),
                }
                for batch in imports[:10]
            ],
            "protocol_context": [
                {
                    "run_id": run.id,
                    "protocol_id": run.protocol_id,
                    "protocol_title": run.protocol_title,
                    "protocol_version": run.protocol_version,
                    "created_at": run.created_at.isoformat(),
                    "flags": list(run.triage_flags or []),
                }
                for run in protocol_runs[:10]
            ],
            "protocol_runs": [
                {
                    "run_id": run.id,
                    "protocol_id": run.protocol_id,
                    "protocol_title": run.protocol_title,
                    "protocol_version": run.protocol_version,
                    "created_at": run.created_at.isoformat(),
                    "flags": list(run.triage_flags or []),
                }
                for run in protocol_runs[:10]
            ],
            "missing_data": missing,
            "limitations": [
                "Documentos extraídos por IA/fallback entram como pendentes até revisão humana.",
                "OCR de imagem não está implementado; usar texto colado ou cadastro estruturado.",
                "O bundle é minimizado para IA e não envia identificadores por padrão.",
            ],
        }

    def _fallback_extract(
        self,
        document: PatientClinicalDocumentModel,
    ) -> ClinicalDocumentExtractionPayload:
        text = normalize_text(
            " ".join(
                [
                    document.raw_text or "",
                    " ".join(str(value) for value in (document.structured_payload or {}).values()),
                ]
            )
        )
        medications = _matches(
            text,
            [
                "sertralina",
                "fluoxetina",
                "paroxetina",
                "escitalopram",
                "litio",
                "carbonato de litio",
                "diazepam",
                "clonazepam",
                "ibuprofeno",
                "nimesulida",
                "dipirona",
                "metamizol",
                "novalgina",
            ],
        )
        allergies = _terms_after(text, ["alergia", "alergico", "alergica"])
        conditions = _matches(
            text,
            [
                "doenca renal cronica",
                "insuficiencia renal",
                "hepatopatia",
                "insuficiencia cardiaca",
                "diabetes",
                "hipertensao",
                "asma",
                "epilepsia",
                "convulsao",
            ],
        )
        mental = _matches(
            text,
            [
                "depressao",
                "transtorno bipolar",
                "mania",
                "hipomania",
                "risco suicida",
                "ansiedade",
                "uso alcool",
                "uso substancias",
            ],
        )
        reproductive = _matches(text, ["gestante", "lactante", "gravidez", "tentando engravidar"])
        return ClinicalDocumentExtractionPayload(
            medications=medications,
            allergies=allergies,
            conditions=conditions,
            observations=_extract_observations(document.raw_text),
            lab_results=_extract_labs(document.raw_text),
            adverse_reactions=_terms_after(text, ["reacao adversa", "evento adverso"]),
            mental_health_factors=mental,
            reproductive_factors=reproductive,
            pregnancy_or_lactation=bool(reproductive) or None,
            notes=["Extração determinística simples; revisar manualmente."],
        )

    def _apply_entities(
        self,
        patient: PatientModel,
        entities: dict[str, Any],
        *,
        document_id: int,
    ) -> None:
        patient.current_medications = merge_terms(
            patient.current_medications,
            list(entities.get("medications") or []),
        )
        patient.allergies = merge_terms(patient.allergies, list(entities.get("allergies") or []))
        patient.comorbidities = merge_terms(
            patient.comorbidities,
            list(entities.get("conditions") or []),
        )
        patient.adverse_reactions = merge_terms(
            patient.adverse_reactions,
            list(entities.get("adverse_reactions") or []),
        )
        patient.mental_health_factors = merge_terms(
            patient.mental_health_factors,
            list(entities.get("mental_health_factors") or []),
        )
        patient.reproductive_gynecologic_factors = merge_terms(
            patient.reproductive_gynecologic_factors,
            list(entities.get("reproductive_factors") or []),
        )
        if entities.get("pregnancy_or_lactation") is True:
            patient.pregnancy_or_lactation = True
        for medication_name in list(entities.get("medications") or []):
            self.db.add(
                PatientMedicationHistoryModel(
                    patient_id=patient.id,
                    medication_name=str(medication_name)[:180],
                    source_document_id=document_id,
                    validation_status="reviewed",
                )
            )

    def _timeline(
        self,
        *,
        patient_id: int,
        event_type: str,
        title: str,
        summary: str,
        source_type: str,
        source_system: str | None,
        payload: dict[str, Any],
        user: UserModel,
        validation_status: str = "pending_review",
    ) -> None:
        self.db.add(
            PatientClinicalTimelineEventModel(
                patient_id=patient_id,
                event_type=event_type,
                title=title,
                summary=summary,
                source_type=source_type,
                source_system=source_system,
                payload=payload,
                validation_status=validation_status,
                created_by=user.id,
            )
        )

    def _merge_reviewed_entities(
        self,
        documents: list[PatientClinicalDocumentModel],
    ) -> dict[str, list[str]]:
        merged: dict[str, list[str]] = {
            "medications": [],
            "allergies": [],
            "conditions": [],
            "mental_health_factors": [],
            "reproductive_factors": [],
            "adverse_reactions": [],
        }
        for document in documents:
            entities = document.extracted_entities or {}
            for key in merged:
                merged[key] = merge_terms(merged[key], list(entities.get(key) or []))
        return merged

    def _missing_data(
        self,
        patient: PatientModel,
        reviewed_docs: list[PatientClinicalDocumentModel],
    ) -> list[str]:
        missing = []
        checks = {
            "altura": patient.height_cm,
            "alergias": patient.allergies,
            "medicamentos atuais": patient.current_medications,
            "condição renal": patient.renal_condition,
            "condição hepática": patient.hepatic_condition,
            "documentos revisados": reviewed_docs,
        }
        for label, value in checks.items():
            if value in (None, "", []) or value == []:
                missing.append(label)
        return missing

    def _minimize_text(self, text: str, patient: PatientModel) -> str:
        minimized = text[:12000]
        minimized = re.sub(r"[\w.\-+]+@[\w.\-]+", "[email]", minimized)
        minimized = re.sub(r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b", "[documento]", minimized)
        minimized = re.sub(
            r"\b(?:\+?55\s?)?\(?\d{2}\)?\s?\d{4,5}-?\d{4}\b",
            "[telefone]",
            minimized,
        )
        if patient.name:
            minimized = re.sub(re.escape(patient.name), "[paciente]", minimized, flags=re.I)
        return minimized


def _document_extraction_prompt() -> str:
    return (
        "Extraia entidades clínicas de texto minimizado para JSON. "
        "Não diagnostique, não valide automaticamente, não invente dados ausentes. "
        "Use apenas campos: medications, allergies, conditions, observations, lab_results, "
        "adverse_reactions, mental_health_factors, reproductive_factors, "
        "pregnancy_or_lactation, notes. "
        "Tudo deve ficar pendente de revisão humana."
    )


def _matches(text: str, candidates: list[str]) -> list[str]:
    found = []
    for candidate in candidates:
        if normalize_text(candidate) in text:
            found.append(candidate)
    return sorted(set(found))


def _terms_after(text: str, markers: list[str]) -> list[str]:
    found = []
    for marker in markers:
        normalized = normalize_text(marker)
        index = text.find(normalized)
        if index >= 0:
            snippet = text[index + len(normalized) : index + len(normalized) + 80]
            tokens = [token for token in re.split(r"[,.;\n]", snippet) if token.strip()]
            if tokens:
                found.append(tokens[0].strip(" :-")[:80])
    return sorted(set(item for item in found if item))


def _extract_labs(text: str) -> list[str]:
    patterns = [
        r"\b(creatinina|glicemia|tgo|tgp|sodio|potassio)\s*[:=]?\s*([\d,.]+)",
    ]
    found = []
    for pattern in patterns:
        for match in re.finditer(pattern, text or "", flags=re.I):
            found.append(f"{match.group(1)} {match.group(2)}")
    return found[:12]


def _extract_observations(text: str) -> list[str]:
    lines = [line.strip() for line in (text or "").splitlines() if line.strip()]
    return [line[:180] for line in lines[:6]]
