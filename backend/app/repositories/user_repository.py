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
        is_active: bool = True,
    ) -> UserModel:
        user = UserModel(
            name=name,
            email=email.casefold(),
            hashed_password=hashed_password,
            role=role,
            is_active=is_active,
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
