"""Revogação server-side de access tokens no logout (PRE-05).

O JWT continua stateless para autenticação; somente tokens encerrados antes do `exp` ficam
registrados, e apenas até o próprio `exp`. O armazenamento é limitado por
`tokens revogados na janela de expiração` e é podado a cada logout.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.database.models import RevokedAccessTokenModel


class SessionRevocationService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def is_revoked(self, jti: str) -> bool:
        return (
            self.db.scalar(
                select(RevokedAccessTokenModel.jti).where(RevokedAccessTokenModel.jti == jti)
            )
            is not None
        )

    def revoke(self, payload: dict[str, Any]) -> None:
        jti = str(payload["jti"])
        now = datetime.now(UTC)
        self.db.execute(
            delete(RevokedAccessTokenModel).where(RevokedAccessTokenModel.expires_at < now)
        )
        if self.is_revoked(jti):
            return
        self.db.add(
            RevokedAccessTokenModel(
                jti=jti,
                user_id=int(payload["sub"]),
                expires_at=datetime.fromtimestamp(int(payload["exp"]), tz=UTC),
                revoked_at=now,
            )
        )
        self.db.flush()
