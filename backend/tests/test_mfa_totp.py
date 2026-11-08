"""NEW-21: verificação TOTP sem nenhum teste e sem fluxo de cadastro.

Oráculo independente: vetores do RFC 6238, Apêndice B (HMAC-SHA1, semente ASCII
"12345678901234567890"), usando os 6 dígitos finais do código de 8 dígitos publicado.
"""

from __future__ import annotations

import base64

import pytest
from fastapi.testclient import TestClient

from app.core import security
from app.core.security import encrypt_mfa_secret, verify_totp
from app.domain.user import UserRole

RFC_SECRET = base64.b32encode(b"12345678901234567890").decode("ascii")


@pytest.mark.parametrize(
    ("unix_time", "rfc_8_digits"),
    [
        (59, "94287082"),
        (1111111109, "07081804"),
        (1234567890, "89005924"),
        (2000000000, "69279037"),
    ],
)
def test_totp_matches_rfc6238_vectors(monkeypatch, unix_time: int, rfc_8_digits: str) -> None:
    monkeypatch.setattr(security.time, "time", lambda: unix_time)
    encrypted = encrypt_mfa_secret(RFC_SECRET)
    assert verify_totp(rfc_8_digits[-6:], encrypted) is True
    # Um dígito trocado nunca vale.
    wrong = rfc_8_digits[-6:-1] + str((int(rfc_8_digits[-1]) + 1) % 10)
    assert verify_totp(wrong, encrypted) is False


def test_totp_window_is_one_step_each_side(monkeypatch) -> None:
    encrypted = encrypt_mfa_secret(RFC_SECRET)
    code = "081804"  # RFC 6238 em t=1111111109, passo 37037036 (t=1111111080..1111111109)
    step_start = 37037036 * 30
    for t, accepted in (
        (step_start - 31, False),  # dois passos antes
        (step_start - 30, True),  # passo anterior
        (step_start + 29, True),
        (step_start + 59, True),  # passo seguinte
        (step_start + 60, False),  # dois passos depois
    ):
        monkeypatch.setattr(security.time, "time", lambda t=t: t)
        assert verify_totp(code, encrypted) is accepted, t


@pytest.mark.parametrize("bad", [None, "", "12345", "abcdef", "1234567"])
def test_totp_rejects_malformed_codes(bad) -> None:
    assert verify_totp(bad, encrypt_mfa_secret(RFC_SECRET)) is False


def test_totp_fails_closed_on_corrupted_secret() -> None:
    assert verify_totp("287082", "not-a-fernet-token") is False


def test_login_with_mfa_enabled(client: TestClient, create_test_user, db_session, monkeypatch):
    user = create_test_user(email="mfa@example.test", password="Admin@12345", role=UserRole.MEDICO)
    user.mfa_enabled = True
    user.mfa_secret_encrypted = encrypt_mfa_secret(RFC_SECRET)
    db_session.commit()
    monkeypatch.setattr(security.time, "time", lambda: 59)
    body = {"email": "mfa@example.test", "password": "Admin@12345"}

    assert client.post("/api/auth/login", json=body).status_code == 401
    assert client.post("/api/auth/login", json=body | {"mfa_code": "000000"}).status_code == 401
    ok = client.post("/api/auth/login", json=body | {"mfa_code": "287082"})
    assert ok.status_code == 200
    assert ok.json()["user"]["email"] == "mfa@example.test"
