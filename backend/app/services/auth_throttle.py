from __future__ import annotations

import hashlib
from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.database.models import AuditEventModel, LoginThrottleModel

LOGIN_WINDOW = timedelta(minutes=15)
LOGIN_LOCKOUT = timedelta(minutes=15)
LOGIN_FAILURE_LIMIT = 5


class LoginThrottle:
    def __init__(self, db: Session) -> None:
        self.db = db

    def identifier(self, email: str) -> str:
        return hashlib.sha256(email.strip().casefold().encode("utf-8")).hexdigest()

    def locked(self, email: str) -> bool:
        row = self.db.get(LoginThrottleModel, self.identifier(email))
        if row is None or row.locked_until is None:
            return False
        locked_until = self._aware(row.locked_until)
        return locked_until > datetime.now(UTC)

    def failure(self, email: str, *, reason: str) -> None:
        identifier = self.identifier(email)
        now = datetime.now(UTC)
        row = self.db.get(LoginThrottleModel, identifier)
        if row is None or now - self._aware(row.window_started_at) > LOGIN_WINDOW:
            row = LoginThrottleModel(
                identifier_hash=identifier,
                failure_count=0,
                window_started_at=now,
            )
            self.db.add(row)
        row.failure_count += 1
        if row.failure_count >= LOGIN_FAILURE_LIMIT:
            row.locked_until = now + LOGIN_LOCKOUT
        self.db.add(
            AuditEventModel(
                action="auth.login_failed",
                resource_type="authentication",
                status="locked" if row.locked_until else "denied",
                details={"identifier_hash": identifier, "reason": reason},
            )
        )
        self.db.flush()

    def success(self, email: str, *, user_id: int, user_role: str) -> None:
        identifier = self.identifier(email)
        row = self.db.get(LoginThrottleModel, identifier)
        if row is not None:
            self.db.delete(row)
        self.db.add(
            AuditEventModel(
                user_id=user_id,
                user_role=user_role,
                action="auth.login_succeeded",
                resource_type="authentication",
                status="success",
                details={"identifier_hash": identifier},
            )
        )
        self.db.flush()

    @staticmethod
    def _aware(value: datetime) -> datetime:
        return value.replace(tzinfo=UTC) if value.tzinfo is None else value
