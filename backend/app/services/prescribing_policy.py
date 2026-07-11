from datetime import UTC, datetime
from typing import Any

from app.domain.clinical_intelligence import PrescribingPolicyResult

PRESCRIBING_ROLES = {"admin", "medico"}


class PrescribingPolicyService:
    """Separa autorização do sistema, política institucional e regra regulatória."""

    def evaluate(
        self,
        user: Any,
        medication: Any,
        prescription: Any | None = None,
        patient_context: Any | None = None,
    ) -> PrescribingPolicyResult:
        def get(obj: Any, key: str, default: Any = None) -> Any:
            return obj.get(key, default) if isinstance(obj, dict) else getattr(obj, key, default)

        role_value = get(user, "role", "")
        role = str(getattr(role_value, "value", role_value))
        specialty = get(user, "specialty_code")
        verification = get(user, "credential_verification_status", "demo_unverified")
        policy_type = get(medication, "policy_type", "demo_policy")
        strength = get(medication, "policy_strength", "warning_only")
        required = list(get(medication, "required_specialty_codes", []) or [])
        recommended = list(get(medication, "recommended_specialty_codes", []) or [])
        sources = list(get(medication, "policy_source_refs", []) or [])
        effective_from = get(medication, "policy_effective_from")
        effective_until = get(medication, "policy_effective_until")
        form = get(medication, "prescription_form_type")
        missing: list[str] = []
        warnings: list[str] = []
        institutional: list[str] = []
        legal: list[str] = []
        status = "allowed"
        now = datetime.now(UTC)

        def normalize_datetime(value: Any) -> datetime | None:
            if value is None:
                return None
            if isinstance(value, str):
                value = datetime.fromisoformat(value.replace("Z", "+00:00"))
            return value.replace(tzinfo=UTC) if value.tzinfo is None else value

        if role not in PRESCRIBING_ROLES:
            status = "blocked_by_policy"
            warnings.append("O perfil de sistema não possui permissão para prescrever.")
        elif role == "medico" and not specialty:
            status = "insufficient_credentials"
            missing.append("especialidade demo")
        if verification != "verified":
            warnings.append("Credencial demo não verificada; esta versão não consulta CRM/CFM.")
        if policy_type == "legal_regulatory":
            if not sources:
                warnings.append(
                    "Regra regulatória sem fonte oficial: tratada como pendente de revisão."
                )
                status = "allowed_with_warning" if status == "allowed" else status
            else:
                legal.append("Aplicar somente a versão vigente da fonte regulatória indicada.")
        else:
            institutional.append(
                "Regra institucional/demonstrativa; não constitui restrição legal definitiva."
            )
        starts = normalize_datetime(effective_from)
        ends = normalize_datetime(effective_until)
        if starts and now < starts:
            warnings.append("Política ainda não vigente; mantida apenas como referência.")
            status = "allowed_with_warning" if status == "allowed" else status
        if ends and now > ends:
            warnings.append("Política expirada; revisão da fonte e da versão é obrigatória.")
            status = "allowed_with_warning" if status == "allowed" else status
        if (
            required
            and specialty not in required
            and status not in {"blocked_by_policy", "insufficient_credentials"}
        ):
            status = "requires_specialist_review"
            warnings.append(
                "Especialidade informada não atende à regra demonstrativa de revisão especializada."
            )
        elif recommended and specialty not in recommended and status == "allowed":
            status = "allowed_with_warning"
            warnings.append("Revisão pela especialidade recomendada deve ser considerada.")
        if get(medication, "requires_second_review", False) and status not in {
            "blocked_by_policy",
            "insufficient_credentials",
        }:
            status = "requires_second_review"
        if strength in {"soft_block", "hard_block"} and policy_type != "legal_regulatory":
            warnings.append("Bloqueio de política não regulatória convertido em revisão humana.")
            if status == "allowed":
                status = "requires_specialist_review"
        rules = [
            {
                "policy_type": policy_type,
                "policy_strength": strength,
                "validation_status": get(
                    medication,
                    "policy_validation_status",
                    get(medication, "validation_status", "pending_review"),
                ),
                "source_refs": sources,
                "policy_version": get(medication, "policy_version", "unversioned"),
                "source_version": get(medication, "source_version"),
                "institution_id": get(medication, "institution_id"),
                "effective_from": effective_from,
                "effective_until": effective_until,
                "override_allowed": bool(get(medication, "override_allowed", False)),
                "override_reason_required": bool(get(medication, "override_reason_required", True)),
                "second_reviewer_role": get(medication, "second_reviewer_role"),
            }
        ]
        return PrescribingPolicyResult(
            status=status,
            rules_applied=rules,
            prescriber_profile={
                "role": role,
                "specialty_code": specialty,
                "credential_verification_status": verification,
            },
            required_specialties=required,
            recommended_specialties=recommended,
            missing_credentials=missing,
            prescription_form_requirements=[form] if form else [],
            warnings=warnings,
            legal_regulatory_notes=legal,
            institutional_notes=institutional,
            source_refs=sources,
            requires_human_review=status != "allowed"
            or verification != "verified"
            or rules[0]["validation_status"] != "validated",
        )


PrescriberPolicyService = PrescribingPolicyService
