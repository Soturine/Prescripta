from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database.models import EvidenceLinkModel, EvidenceSourceModel, UserModel
from app.schemas.evidence_schema import EvidenceLinkCreate, EvidenceSourceCreate
from app.services.audit_service import AuditService


class EvidenceError(ValueError):
    pass


class EvidenceService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_source(
        self,
        payload: EvidenceSourceCreate,
        actor: UserModel,
    ) -> EvidenceSourceModel:
        source = EvidenceSourceModel(
            institution_id=actor.institution_id,
            **payload.model_dump(mode="python"),
            review_status="pending_review",
            created_by_user_id=actor.id,
        )
        self.db.add(source)
        try:
            self.db.flush()
        except IntegrityError as exc:
            raise EvidenceError("Fonte com esse identificador já existe na instituição.") from exc
        AuditService(self.db).record_action(
            user=actor,
            action="evidence.source.create",
            resource_type="evidence_source",
            resource_id=source.id,
            status=source.review_status,
            details={"source_type": source.source_type, "identifier": source.identifier},
        )
        return source

    def list_sources(
        self,
        actor: UserModel,
        *,
        offset: int = 0,
        limit: int = 50,
    ) -> list[EvidenceSourceModel]:
        return list(
            self.db.scalars(
                select(EvidenceSourceModel)
                .where(EvidenceSourceModel.institution_id == actor.institution_id)
                .order_by(EvidenceSourceModel.created_at.desc())
                .offset(offset)
                .limit(limit)
            )
        )

    def create_link(
        self,
        payload: EvidenceLinkCreate,
        actor: UserModel,
    ) -> EvidenceLinkModel:
        source = self.db.get(EvidenceSourceModel, payload.source_id)
        if source is None or source.institution_id != actor.institution_id:
            raise EvidenceError("Fonte não encontrada.")
        link = EvidenceLinkModel(
            institution_id=actor.institution_id,
            **payload.model_dump(),
            review_status="pending_review",
            created_by_user_id=actor.id,
        )
        self.db.add(link)
        try:
            self.db.flush()
        except IntegrityError as exc:
            raise EvidenceError("Vínculo de evidência já existe.") from exc
        return link

    def links(
        self,
        actor: UserModel,
        *,
        target_type: str | None = None,
        target_id: str | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> list[EvidenceLinkModel]:
        statement = select(EvidenceLinkModel).where(
            EvidenceLinkModel.institution_id == actor.institution_id
        )
        if target_type:
            statement = statement.where(EvidenceLinkModel.target_type == target_type)
        if target_id:
            statement = statement.where(EvidenceLinkModel.target_id == target_id)
        statement = statement.order_by(EvidenceLinkModel.created_at.desc())
        return list(self.db.scalars(statement.offset(offset).limit(limit)))
