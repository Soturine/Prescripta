from __future__ import annotations

from datetime import UTC, datetime

from app.database.models import UserModel
from app.domain.user import (
    PROFESSION_CAPABILITY_TEMPLATES,
    ROLE_PROFESSION,
    Capability,
    Profession,
    UserRole,
)


class InvalidProfessionalProfile(ValueError):
    pass


def nursing_protocol_authorized(user: UserModel, protocol_id: str) -> bool:
    """Exige credencial vigente e política institucional versionada e limitada."""

    if user.profession != Profession.NURSING.value:
        return False
    policy = user.institutional_policy or {}
    protocol_policy = (policy.get("nursing_protocols") or {}).get(protocol_id) or {}
    expires_at = user.credential_expires_at
    if expires_at is not None and expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)
    scope_defined = bool(
        protocol_policy.get("allowed_medications")
        or protocol_policy.get("allowed_conditions")
    )
    return all(
        (
            policy.get("nursing_prescribing_enabled") is True,
            bool(user.credential_type),
            expires_at is not None and expires_at > datetime.now(UTC),
            bool(protocol_policy.get("source")),
            bool(protocol_policy.get("version")),
            scope_defined,
            bool(protocol_policy.get("limits")),
        )
    )


def allowed_capabilities(
    profession: Profession | str,
    *,
    specialty_codes: list[str] | None = None,
) -> set[str]:
    normalized = Profession(profession)
    allowed = {
        capability.value for capability in PROFESSION_CAPABILITY_TEMPLATES[normalized]
    }
    specialties = set(specialty_codes or [])
    if normalized == Profession.MEDICINE and "psychiatry" in specialties:
        allowed.add(Capability.PATIENT_SENSITIVE_PSYCHOLOGY_READ.value)
    if normalized == Profession.CLINICAL_SAFETY:
        allowed.add(Capability.PATIENT_SENSITIVE_PSYCHOLOGY_READ.value)
    return allowed


def validate_professional_profile(
    *,
    role: UserRole | str,
    profession: Profession | str,
    capabilities: list[str],
    specialty_codes: list[str] | None = None,
) -> None:
    normalized_role = UserRole(role)
    normalized_profession = Profession(profession)
    expected = ROLE_PROFESSION[normalized_role]
    if normalized_profession != expected:
        raise InvalidProfessionalProfile(
            "Papel organizacional e profissão exigem uma conta coerente e separada."
        )
    unknown = set(capabilities) - {capability.value for capability in Capability}
    if unknown:
        raise InvalidProfessionalProfile(
            f"Capacidades desconhecidas: {', '.join(sorted(unknown))}."
        )
    excessive = set(capabilities) - allowed_capabilities(
        normalized_profession, specialty_codes=specialty_codes
    )
    if excessive:
        raise InvalidProfessionalProfile(
            f"Capacidades incompatíveis com a profissão: {', '.join(sorted(excessive))}."
        )
