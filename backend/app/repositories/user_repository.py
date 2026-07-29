from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import UserModel


class UserRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list(self) -> list[UserModel]:
        return list(self.db.scalars(select(UserModel).order_by(UserModel.name)))

    def get(self, user_id: int) -> UserModel | None:
        return self.db.get(UserModel, user_id)

    def get_by_email(self, email: str) -> UserModel | None:
        return self.db.scalar(select(UserModel).where(UserModel.email == email.casefold()))

    def create(
        self,
        *,
        name: str,
        email: str,
        hashed_password: str,
        role: str,
        profession: str,
        capabilities: list[str] | None = None,
        is_active: bool = True,
        specialty_code: str | None = None,
        specialty_codes: list[str] | None = None,
        credential_type: str | None = None,
        credential_code_demo: str | None = None,
        credential_region: str | None = None,
        credential_expires_at=None,
        institutional_policy: dict | None = None,
        sensitive_data_segments: list[str] | None = None,
        crm_demo: str | None = None,
        crm_uf: str | None = None,
        rqe_demo: str | None = None,
        credential_verification_status: str = "demo_unverified",
        institution_id: str = "demo",
    ) -> UserModel:
        user = UserModel(
            name=name,
            email=email.casefold(),
            hashed_password=hashed_password,
            role=role,
            profession=profession,
            capabilities=list(capabilities or []),
            capability_policy_version="explicit-v1",
            is_active=is_active,
            specialty_code=specialty_code,
            specialty_codes=list(specialty_codes or ([specialty_code] if specialty_code else [])),
            credential_type=credential_type,
            credential_code_demo=credential_code_demo,
            credential_region=credential_region,
            credential_expires_at=credential_expires_at,
            institutional_policy=dict(institutional_policy or {}),
            sensitive_data_segments=list(sensitive_data_segments or []),
            crm_demo=crm_demo,
            crm_uf=crm_uf,
            rqe_demo=rqe_demo,
            credential_verification_status=credential_verification_status,
            institution_id=institution_id,
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def set_status(self, user: UserModel, is_active: bool) -> UserModel:
        user.is_active = is_active
        self.db.commit()
        self.db.refresh(user)
        return user

    def set_role(self, user: UserModel, role: str) -> UserModel:
        user.role = role
        self.db.commit()
        self.db.refresh(user)
        return user
