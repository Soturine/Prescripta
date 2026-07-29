from collections.abc import Callable, Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.security import hash_password
from app.database.models import UserModel
from app.database.session import Base, finish_denied_request, get_db
from app.domain.user import ROLE_PROFESSION, Capability, UserRole, capability_values
from app.main import app
from app.repositories.user_repository import UserRepository

engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db() -> Generator[Session, None, None]:
    db = TestingSessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        finish_denied_request(db)
        raise
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def reset_database() -> Generator[None, None, None]:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def create_test_user(db_session: Session) -> Callable[..., UserModel]:
    def factory(
        *,
        email: str = "admin@test.local",
        password: str = "Admin@12345",
        role: UserRole = UserRole.ADMIN,
        is_active: bool = True,
        name: str = "Usuario Teste",
        institution_id: str = "demo",
    ) -> UserModel:
        capabilities = capability_values(ROLE_PROFESSION[role])
        if role == UserRole.ADMIN:
            capabilities = sorted(
                set(capabilities)
                | {
                    Capability.PATIENT_CREATE.value,
                    Capability.PATIENT_READ.value,
                    Capability.PATIENT_WRITE.value,
                    Capability.PRESCRIPTION_CHECK.value,
                    Capability.PRESCRIPTION_OVERRIDE.value,
                    Capability.REPORT_READ.value,
                    Capability.REPORT_CREATE.value,
                    Capability.PATIENT_GUIDANCE_CREATE.value,
                    Capability.BREAK_GLASS_INVOKE.value,
                    Capability.RECONCILIATION_REVIEW.value,
                }
            )
        return UserRepository(db_session).create(
            name=name,
            email=email,
            hashed_password=hash_password(password),
            role=role.value,
            profession=ROLE_PROFESSION[role].value,
            capabilities=capabilities,
            is_active=is_active,
            institution_id=institution_id,
        )

    return factory


@pytest.fixture
def auth_headers(client: TestClient) -> Callable[[str, str], dict[str, str]]:
    def factory(email: str, password: str) -> dict[str, str]:
        response = client.post("/api/auth/login", json={"email": email, "password": password})
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    return factory
