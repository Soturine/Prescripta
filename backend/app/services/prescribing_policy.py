from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import (
    InstitutionalClinicalProtocolModel,
    InstitutionalClinicalProtocolVersionModel,
    ProtocolConditionScopeModel,
    ProtocolCredentialRequirementModel,
    ProtocolMedicationScopeModel,
    ProtocolPrescribingScopeModel,
)
from app.domain.clinical_intelligence import PrescribingPolicyResult
from app.services.audit_service import AuditService
from app.services.object_authorization import ObjectAuthorizationService

PRESCRIBING_ROLES = {"medico"}
POLICY_STATUSES = {
    "allowed",
    "allowed_with_warning",
    "blocked_by_policy",
    "insufficient_credentials",
    "insufficient_protocol_context",
    "requires_second_review",
    "requires_specialist_review",
}


class PrescribingPolicyService:
    """Combina profissão, relação assistencial e policy versionada sem decisão por LLM."""

    def __init__(self, db: Session | None = None) -> None:
        self.db = db

    def evaluate(
        self,
        user: Any,
        medication: Any,
        prescription: Any | None = None,
        patient_context: Any | None = None,
    ) -> PrescribingPolicyResult:
        role = self._text(self._get(user, "role", ""))
        profession = self._text(self._get(user, "profession", ""))
        if role == "enfermagem" or profession == "nursing":
            return self._evaluate_nursing(user, medication, prescription, patient_context)
        return self._evaluate_standard(user, medication)

    def _evaluate_nursing(
        self,
        user: Any,
        medication: Any,
        prescription: Any | None,
        patient: Any | None,
    ) -> PrescribingPolicyResult:
        capability = "nursing.protocol_prescribe"
        capabilities = set(self._get(user, "capabilities", []) or [])
        missing: list[str] = []
        warnings: list[str] = []
        status = "allowed"
        capability_status = "granted" if capability in capabilities else "missing"
        if capability_status == "missing":
            status = "blocked_by_policy"
            missing.append(capability)

        relationship_status = "not_evaluated"
        patient_id = self._get(patient, "id")
        if self.db is None or patient_id is None:
            relationship_status = "insufficient_context"
            if status == "allowed":
                status = "insufficient_protocol_context"
            missing.append("patient relationship")
        elif ObjectAuthorizationService(self.db).can_access_patient(
            user,
            patient_id,
            capability="patient.read",
            purpose="treatment",
            record_break_glass_object=False,
        ):
            relationship_status = "active"
        else:
            relationship_status = "missing"
            status = "blocked_by_policy"
            missing.append("patient relationship")

        version_id = self._get(prescription, "protocol_version_id")
        version = (
            self.db.get(InstitutionalClinicalProtocolVersionModel, version_id)
            if self.db is not None and version_id is not None
            else None
        )
        protocol = (
            self.db.get(InstitutionalClinicalProtocolModel, version.protocol_id)
            if self.db is not None and version is not None
            else None
        )
        protocol_context: dict[str, Any] = {
            "requested_version_id": version_id,
            "applicable": False,
        }
        source_refs: list[str] = []
        rules: list[dict[str, Any]] = []
        if version is None or protocol is None:
            if status == "allowed":
                status = "insufficient_protocol_context"
            missing.append("active protocol version")
        else:
            protocol_context.update(
                {
                    "protocol_id": protocol.id,
                    "protocol_code": protocol.code,
                    "protocol_name": protocol.name,
                    "program": protocol.program,
                    "version_id": version.id,
                    "version": version.version,
                    "status": version.status,
                    "review_status": version.review_status,
                    "effective_from": version.effective_from,
                    "effective_until": version.effective_until,
                    "definition_hash": version.definition_hash,
                }
            )
            source_refs = list(version.source_refs or [])
            rules.append(
                {
                    "policy_type": "institutional_protocol",
                    "policy_strength": "hard_block",
                    "validation_status": version.review_status,
                    "source_refs": source_refs,
                    "policy_version": version.version,
                    "institution_id": version.institution_id,
                    "effective_from": version.effective_from,
                    "effective_until": version.effective_until,
                    "override_allowed": bool((version.override_policy or {}).get("allowed")),
                    "second_reviewer_role": version.second_reviewer_role,
                }
            )
            version_errors = self._validate_protocol_version(user, protocol, version)
            scope_errors = self._validate_protocol_scope(
                user, medication, prescription, patient, version
            )
            missing.extend(version_errors + scope_errors)
            if version_errors or scope_errors:
                status = (
                    "insufficient_credentials"
                    if any("credential" in item for item in version_errors + scope_errors)
                    else "blocked_by_policy"
                    if any(
                        token in item
                        for item in version_errors + scope_errors
                        for token in (
                            "institution",
                            "revoked",
                            "medication",
                            "condition",
                            "route",
                            "dose",
                        )
                    )
                    else "insufficient_protocol_context"
                )
            elif version.requires_second_review:
                status = "requires_second_review"
                missing.append("independent second review")
            else:
                protocol_context["applicable"] = True

        if status not in POLICY_STATUSES:
            status = "blocked_by_policy"
        result = PrescribingPolicyResult(
            status=status,
            rules_applied=rules,
            prescriber_profile={
                "role": self._text(self._get(user, "role", "")),
                "profession": self._text(self._get(user, "profession", "")),
                "credential_verification_status": self._get(
                    user, "credential_verification_status", "demo_unverified"
                ),
            },
            required_specialties=[],
            recommended_specialties=[],
            missing_credentials=[item for item in missing if "credential" in item],
            prescription_form_requirements=[],
            warnings=warnings,
            legal_regulatory_notes=[],
            institutional_notes=[
                "Prescrição de enfermagem somente dentro do protocolo institucional demonstrado."
            ],
            source_refs=source_refs,
            requires_human_review=status != "allowed",
            capability_status=capability_status,
            relationship_status=relationship_status,
            protocol_context=protocol_context,
            missing_context=list(dict.fromkeys(missing)),
            second_review={
                "required": bool(version and version.requires_second_review),
                "status": "required" if status == "requires_second_review" else "not_required",
                "reviewer_role": version.second_reviewer_role if version else None,
            },
        )
        if self.db is not None and self._get(user, "id") is not None:
            AuditService(self.db).record_action(
                user=user,
                action="protocol_prescribing.evaluate",
                resource_type="institutional_clinical_protocol_version",
                resource_id=str(version_id) if version_id else None,
                status=status,
                details={
                    "medication_id": self._get(medication, "id"),
                    "capability_status": capability_status,
                    "relationship_status": relationship_status,
                    "missing_context": result.missing_context,
                },
            )
        return result

    def _validate_protocol_version(self, user, protocol, version) -> list[str]:
        errors: list[str] = []
        now = datetime.now(UTC)
        starts = self._aware(version.effective_from)
        ends = self._aware(version.effective_until)
        if protocol.institution_id != self._get(user, "institution_id") or (
            version.institution_id != self._get(user, "institution_id")
        ):
            errors.append("institution mismatch")
        if protocol.status != "active" or version.status != "active":
            errors.append("revoked or inactive protocol")
        if version.review_status != "reviewed_demo":
            errors.append("protocol human review")
        if starts and now < starts:
            errors.append("future protocol")
        if ends and now > ends:
            errors.append("expired protocol")
        if not version.source_refs:
            errors.append("protocol source")
        profession = self._text(self._get(user, "profession", ""))
        if profession not in set(version.eligible_professions or []):
            errors.append("eligible profession")
        if version.required_capability not in set(self._get(user, "capabilities", []) or []):
            errors.append("required capability")
        if self.db is not None:
            requirements = list(
                self.db.scalars(
                    select(ProtocolCredentialRequirementModel).where(
                        ProtocolCredentialRequirementModel.protocol_version_id == version.id
                    )
                )
            )
            for requirement in requirements:
                if self._get(user, "credential_type") != requirement.credential_type:
                    errors.append(f"credential type {requirement.credential_type}")
                if requirement.credential_region and (
                    self._get(user, "credential_region") != requirement.credential_region
                ):
                    errors.append("credential region")
                if requirement.verification_required and (
                    self._get(user, "credential_verification_status") != "verified"
                ):
                    errors.append("credential verification")
                expires = self._aware(self._get(user, "credential_expires_at"))
                if requirement.unexpired_required and (expires is None or expires <= now):
                    errors.append("credential expiration")
        return errors

    def _validate_protocol_scope(
        self,
        user,
        medication,
        prescription,
        patient,
        version,
    ) -> list[str]:
        if self.db is None:
            return ["protocol repository"]
        errors: list[str] = []
        medication_id = self._get(medication, "id")
        medication_allowed = self.db.scalar(
            select(ProtocolMedicationScopeModel.id).where(
                ProtocolMedicationScopeModel.protocol_version_id == version.id,
                ProtocolMedicationScopeModel.medication_id == medication_id,
            )
        )
        if medication_allowed is None:
            errors.append("medication outside protocol scope")
        allowed_conditions = set(
            self.db.scalars(
                select(ProtocolConditionScopeModel.condition_code).where(
                    ProtocolConditionScopeModel.protocol_version_id == version.id
                )
            )
        )
        presented_conditions = {
            str(item).casefold()
            for item in (
                list(self._get(prescription, "condition_codes", ()) or ())
                + list(self._get(patient, "comorbidities", []) or [])
                + (
                    [self._get(prescription, "indication")]
                    if self._get(prescription, "indication")
                    else []
                )
            )
        }
        if allowed_conditions and not allowed_conditions.intersection(presented_conditions):
            errors.append("condition outside protocol scope")
        scope = self.db.scalar(
            select(ProtocolPrescribingScopeModel).where(
                ProtocolPrescribingScopeModel.protocol_version_id == version.id
            )
        )
        if scope is None:
            return errors + ["prescribing scope"]
        route = self._get(prescription, "route")
        if scope.allowed_routes and route not in set(scope.allowed_routes):
            errors.append("route outside protocol scope")
        effective_dose = self._get(prescription, "effective_dose")
        if effective_dose is not None and scope.dose_unit:
            amount = effective_dose.amount_as(scope.dose_unit)
            if amount is None:
                errors.append("dose unit outside protocol scope")
            elif (scope.dose_min is not None and amount < scope.dose_min) or (
                scope.dose_max is not None and amount > scope.dose_max
            ):
                errors.append("dose outside protocol scope")
            frequency = effective_dose.inferred_frequency_per_day
            if frequency is not None and (
                (
                    scope.frequency_min_per_day is not None
                    and frequency < scope.frequency_min_per_day
                )
                or (
                    scope.frequency_max_per_day is not None
                    and frequency > scope.frequency_max_per_day
                )
            ):
                errors.append("frequency outside protocol scope")
        duration = self._get(prescription, "duration_days")
        if scope.max_duration_days is not None and (
            duration is None or duration > scope.max_duration_days
        ):
            errors.append("duration outside protocol scope")
        age = self._decimal(self._get(patient, "age"))
        weight = self._decimal(self._get(patient, "weight_kg"))
        if age is not None and (
            (scope.min_age_years is not None and age < scope.min_age_years)
            or (scope.max_age_years is not None and age > scope.max_age_years)
        ):
            errors.append("age outside protocol scope")
        if weight is not None and (
            (scope.min_weight_kg is not None and weight < scope.min_weight_kg)
            or (scope.max_weight_kg is not None and weight > scope.max_weight_kg)
        ):
            errors.append("weight outside protocol scope")
        for parameter in version.required_parameters or []:
            if self._get(patient, parameter) is None:
                errors.append(f"required parameter {parameter}")
        patient_factors = {
            str(item).casefold()
            for item in (
                list(self._get(patient, "allergies", []) or [])
                + list(self._get(patient, "comorbidities", []) or [])
            )
        }
        if patient_factors.intersection(
            {str(item).casefold() for item in version.contraindications or []}
        ):
            errors.append("protocol contraindication")
        return errors

    def _evaluate_standard(self, user: Any, medication: Any) -> PrescribingPolicyResult:
        role = self._text(self._get(user, "role", ""))
        specialty = self._get(user, "specialty_code")
        verification = self._get(user, "credential_verification_status", "demo_unverified")
        policy_type = self._get(medication, "policy_type", "demo_policy")
        strength = self._get(medication, "policy_strength", "warning_only")
        required = list(self._get(medication, "required_specialty_codes", []) or [])
        recommended = list(self._get(medication, "recommended_specialty_codes", []) or [])
        sources = list(self._get(medication, "policy_source_refs", []) or [])
        effective_from = self._get(medication, "policy_effective_from")
        effective_until = self._get(medication, "policy_effective_until")
        form = self._get(medication, "prescription_form_type")
        missing: list[str] = []
        warnings: list[str] = []
        institutional: list[str] = []
        legal: list[str] = []
        status = "allowed"
        now = datetime.now(UTC)
        if role not in PRESCRIBING_ROLES:
            status = "blocked_by_policy"
            warnings.append("O perfil de sistema não possui permissão para prescrever.")
        elif not specialty:
            status = "insufficient_credentials"
            missing.append("especialidade demo")
        if verification != "verified":
            warnings.append("Credencial demo não verificada; esta versão não consulta CRM/CFM.")
        if policy_type == "legal_regulatory":
            if not sources:
                warnings.append("Regra regulatória sem fonte oficial: pendente de revisão.")
                status = "allowed_with_warning" if status == "allowed" else status
            else:
                legal.append("Aplicar somente a versão vigente da fonte regulatória indicada.")
        else:
            institutional.append(
                "Regra institucional/demonstrativa; não constitui restrição legal definitiva."
            )
        starts = self._aware(effective_from)
        ends = self._aware(effective_until)
        if starts and now < starts:
            warnings.append("Política ainda não vigente; mantida apenas como referência.")
            status = "allowed_with_warning" if status == "allowed" else status
        if ends and now > ends:
            warnings.append("Política expirada; revisão da fonte e da versão é obrigatória.")
            status = "allowed_with_warning" if status == "allowed" else status
        if required and specialty not in required and status not in {
            "blocked_by_policy",
            "insufficient_credentials",
        }:
            status = "requires_specialist_review"
            warnings.append("Especialidade informada não atende à regra de revisão.")
        elif recommended and specialty not in recommended and status == "allowed":
            status = "allowed_with_warning"
            warnings.append("Revisão pela especialidade recomendada deve ser considerada.")
        if self._get(medication, "requires_second_review", False) and status not in {
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
                "validation_status": self._get(
                    medication,
                    "policy_validation_status",
                    self._get(medication, "validation_status", "pending_review"),
                ),
                "source_refs": sources,
                "policy_version": self._get(medication, "policy_version", "unversioned"),
                "source_version": self._get(medication, "source_version"),
                "institution_id": self._get(medication, "institution_id"),
                "effective_from": effective_from,
                "effective_until": effective_until,
                "override_allowed": bool(self._get(medication, "override_allowed", False)),
                "override_reason_required": bool(
                    self._get(medication, "override_reason_required", True)
                ),
                "second_reviewer_role": self._get(medication, "second_reviewer_role"),
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
            capability_status="granted" if role in PRESCRIBING_ROLES else "missing",
            relationship_status="not_required_by_legacy_policy",
        )

    @staticmethod
    def _get(obj: Any, key: str, default: Any = None) -> Any:
        if obj is None:
            return default
        value = obj.get(key, default) if isinstance(obj, dict) else getattr(obj, key, default)
        try:
            return value() if key == "effective_dose" and callable(value) else value
        except ValueError:
            return default

    @staticmethod
    def _text(value: Any) -> str:
        return str(getattr(value, "value", value) or "")

    @staticmethod
    def _aware(value: Any) -> datetime | None:
        if value is None:
            return None
        if isinstance(value, str):
            value = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)

    @staticmethod
    def _decimal(value: Any) -> Decimal | None:
        if value is None:
            return None
        try:
            return Decimal(str(value))
        except (InvalidOperation, ValueError):
            return None


PrescriberPolicyService = PrescribingPolicyService
