"""PRE-05: logout revoga o token no servidor; antes, o JWT copiado seguia válido até o `exp`."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import jwt
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.core.config import settings
from app.database.models import RevokedAccessTokenModel
from app.domain.user import UserRole

PASSWORD = "Admin@12345"


def _login(client: TestClient, email: str) -> str:
    response = client.post("/api/auth/login", json={"email": email, "password": PASSWORD})
    assert response.status_code == 200
    return response.json()["access_token"]


def _bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_bearer_token_is_rejected_after_logout(client: TestClient, create_test_user) -> None:
    create_test_user(email="logout-bearer@example.test", password=PASSWORD, role=UserRole.MEDICO)
    token = _login(client, "logout-bearer@example.test")
    assert client.get("/api/auth/me", headers=_bearer(token)).status_code == 200

    client.cookies.clear()
    assert client.post("/api/auth/logout", headers=_bearer(token)).status_code == 204

    replay = client.get("/api/auth/me", headers=_bearer(token))
    assert replay.status_code == 401
    assert replay.json()["detail"] == "Sessão encerrada."


def test_cookie_session_is_revoked_and_other_sessions_survive(
    client: TestClient, create_test_user
) -> None:
    create_test_user(email="logout-cookie@example.test", password=PASSWORD, role=UserRole.MEDICO)
    other_device = _login(client, "logout-cookie@example.test")
    cookie_token = _login(client, "logout-cookie@example.test")  # cookie fica no client
    assert client.cookies.get("prescripta_session") == cookie_token

    assert client.post("/api/auth/logout").status_code == 204

    client.cookies.clear()
    assert client.get("/api/auth/me", headers=_bearer(cookie_token)).status_code == 401
    # Revogação por sessão (jti), não "logout em todos os dispositivos".
    assert client.get("/api/auth/me", headers=_bearer(other_device)).status_code == 200


def test_token_without_jti_is_rejected(client: TestClient, create_test_user) -> None:
    user = create_test_user(
        email="legacy-token@example.test", password=PASSWORD, role=UserRole.MEDICO
    )
    legacy = jwt.encode(
        {"sub": str(user.id), "exp": datetime.now(UTC) + timedelta(minutes=5)},
        settings.secret_key,
        algorithm=settings.jwt_algorithm,
    )
    client.cookies.clear()
    rejected = client.get("/api/auth/me", headers=_bearer(legacy))
    assert rejected.status_code == 401
    assert rejected.json()["detail"] == "Token invalido."


def test_logout_without_or_with_invalid_token_is_idempotent(client: TestClient) -> None:
    client.cookies.clear()
    assert client.post("/api/auth/logout").status_code == 204
    assert client.post("/api/auth/logout", headers=_bearer("not-a-jwt")).status_code == 204


def test_revocations_are_pruned_after_expiry(
    client: TestClient, create_test_user, db_session
) -> None:
    user = create_test_user(email="prune@example.test", password=PASSWORD, role=UserRole.MEDICO)
    db_session.add(
        RevokedAccessTokenModel(
            jti="expired-jti",
            user_id=user.id,
            expires_at=datetime.now(UTC) - timedelta(minutes=1),
        )
    )
    db_session.commit()
    token = _login(client, "prune@example.test")
    client.cookies.clear()
    client.post("/api/auth/logout", headers=_bearer(token))

    db_session.expire_all()
    remaining = db_session.scalars(select(RevokedAccessTokenModel.jti)).all()
    assert "expired-jti" not in remaining
    assert db_session.scalar(select(func.count()).select_from(RevokedAccessTokenModel)) == 1
