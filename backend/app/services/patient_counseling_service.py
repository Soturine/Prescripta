from __future__ import annotations

from sqlalchemy.orm import Session

from app.database.models import (
    MedicationCounselingSummaryModel,
    MedicationModel,
    PatientFunctionalProfileModel,
    PatientModel,
)
from app.schemas.prescription_schema import (
    ContextualQuestion,
    FunctionalContextSummary,
    MissingDataMode,
    PatientCounselingResponse,
)
from app.services.adverse_effect_taxonomy import label_for_effect
from app.services.medication_counseling_service import MedicationCounselingService
from app.services.normalizer import normalize_text
from app.services.patient_functional_profile import (
    FUNCTIONAL_FIELDS,
    PatientFunctionalProfileService,
)

CONTEXTUAL_QUESTION_TEXT = (
    "Este medicamento pode causar tontura, sedacao, queda de pressao ou alteracao de reflexos. "
    "O paciente dirige, opera maquinas, trabalha em altura ou realiza atividade de risco hoje?"
)


class PatientCounselingService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.counseling = MedicationCounselingService(db)
        self.functional = PatientFunctionalProfileService(db)

    def build_for_prescription(
        self,
        patient: PatientModel,
        medication: MedicationModel,
        *,
        summary: MedicationCounselingSummaryModel | None = None,
        contextual_activity_answer: str | None = None,
    ) -> PatientCounselingResponse:
        summary = summary or self.counseling.get_best_for_medication(medication)
        profile = self.functional.get_for_patient(patient.id)
        missing_mode = self.missing_data_mode(patient, profile)
        functional_context = self.functional_context(
            summary,
            profile,
            contextual_activity_answer=contextual_activity_answer,
        )
        return PatientCounselingResponse(
            summary=self.counseling.read_model(summary),
            orientation_points=self.orientation_points(summary, functional_context),
            red_flags=list(summary.red_flags or []) if summary else [],
            source_label=self.source_label(summary),
            review_status=summary.validation_status if summary else None,
            generated_by_ai=bool(summary and summary.generated_by == "ai_provider"),
            requires_review=True if summary is None else summary.requires_review,
            functional_context=functional_context,
            missing_data_mode=missing_mode,
        )

    def missing_data_mode(
        self,
        patient: PatientModel,
        profile: PatientFunctionalProfileModel | None,
    ) -> MissingDataMode:
        missing: list[str] = []
        if not patient.allergies:
            missing.append("alergias")
        if not patient.current_medications:
            missing.append("medicamentos continuos")
        if not patient.renal_condition:
            missing.append("condicao renal")
        if not patient.hepatic_condition:
            missing.append("condicao hepatica")
        if patient.pregnancy_or_lactation is None:
            missing.append("gestacao/lactacao")
        if profile is None:
            missing.extend(["perfil funcional", "atividades que exigem atencao"])
        else:
            unknown_fields = [
                field for field in FUNCTIONAL_FIELDS if getattr(profile, field, None) is None
            ]
            if unknown_fields:
                missing.append("atividades que exigem atencao")
        incomplete = bool(missing)
        return MissingDataMode(
            incomplete_history=incomplete,
            message=(
                "Historico clinico incompleto. A analise sera baseada em medicamento, dose, "
                "duracao, efeitos principais e dados minimos disponiveis."
                if incomplete
                else "Historico clinico demonstrativo revisado para os campos principais."
            ),
            limitation_summary=(
                "Risco personalizado limitado por falta de dados. Revisar alergias, "
                "medicamentos continuos, gravidez/lactacao, condicao renal/hepatica e "
                "atividades que exigem atencao."
                if incomplete
                else "Nao ha limitacao principal por ausencia de dados nos campos demonstrativos."
            ),
            missing_data=missing,
            does_not_block_flow=True,
        )

    def functional_context(
        self,
        summary: MedicationCounselingSummaryModel | None,
        profile: PatientFunctionalProfileModel | None,
        *,
        contextual_activity_answer: str | None,
    ) -> FunctionalContextSummary:
        generic_warnings = self._generic_warnings(summary)
        personalized_warnings: list[str] = []
        profile_known = profile is not None
        unknown_fields = list(FUNCTIONAL_FIELDS)
        if profile is not None:
            unknown_fields = [
                field for field in FUNCTIONAL_FIELDS if getattr(profile, field, None) is None
            ]
            if (
                summary
                and summary.driving_warning
                and (profile.drives_regularly or profile.professional_driver)
            ):
                personalized_warnings.append(
                    "Paciente dirige regularmente; reforcar cautela ate saber como reage."
                )
            if summary and summary.machine_operation_warning and profile.operates_machinery:
                personalized_warnings.append(
                    "Paciente opera maquinas; orientar pausa/cautela se houver sono ou tontura."
                )
            if (
                summary
                and summary.fall_risk_warning
                and (
                    profile.works_at_height
                    or profile.fall_risk_activity
                    or profile.history_of_falls
                )
            ):
                personalized_warnings.append(
                    "Perfil com altura/queda; destacar risco de tontura, pressao baixa ou reflexos."
                )
            if (
                summary
                and summary.sedation_attention_warning
                and (profile.high_attention_activity or profile.caregiver_responsibility)
            ):
                personalized_warnings.append(
                    "Rotina exige atencao; orientar observacao nas primeiras doses."
                )
            if (
                summary
                and (summary.sedation_attention_warning or summary.blood_pressure_warning)
                and profile.frequent_alcohol_use
            ):
                personalized_warnings.append(
                    "Uso frequente de alcool informado; revisar risco de sedacao/tontura."
                )
        question = self.contextual_question(
            summary,
            profile,
            contextual_activity_answer=contextual_activity_answer,
        )
        return FunctionalContextSummary(
            profile_known=profile_known,
            unknown_fields=unknown_fields,
            personalized_warnings=personalized_warnings,
            generic_warnings=generic_warnings,
            question=question,
        )

    def contextual_question(
        self,
        summary: MedicationCounselingSummaryModel | None,
        profile: PatientFunctionalProfileModel | None,
        *,
        contextual_activity_answer: str | None,
    ) -> ContextualQuestion:
        relevant = self._has_activity_relevant_risk(summary)
        normalized_answer = normalize_text(contextual_activity_answer).replace(" ", "_")
        answer_known = normalized_answer in {"sim", "nao", "nao_informado"}
        profile_has_activity_answer = bool(
            profile
            and any(
                getattr(profile, field, None) is not None
                for field in (
                    "drives_regularly",
                    "operates_machinery",
                    "works_at_height",
                    "fall_risk_activity",
                    "high_attention_activity",
                )
            )
        )
        should_ask = relevant and not answer_known and not profile_has_activity_answer
        return ContextualQuestion(
            should_ask=should_ask,
            question=CONTEXTUAL_QUESTION_TEXT if should_ask else None,
            reason=(
                "Risco pratico de direcao, maquinas, altura ou reflexos com dado funcional ausente."
                if should_ask
                else None
            ),
        )

    def orientation_points(
        self,
        summary: MedicationCounselingSummaryModel | None,
        functional_context: FunctionalContextSummary,
    ) -> list[str]:
        if summary is None:
            return [
                "Resumo pratico ainda nao gerado para este medicamento.",
                "Revisar bula/fonte cadastrada antes de orientar efeitos especificos.",
            ]
        points: list[str] = []
        if summary.patient_friendly_summary:
            points.append(summary.patient_friendly_summary)
        for effect in (summary.main_adverse_effects or [])[:5]:
            points.append(f"Orientar sobre {label_for_effect(effect).lower()}.")
        points.extend(functional_context.personalized_warnings)
        if not functional_context.personalized_warnings:
            points.extend(functional_context.generic_warnings[:2])
        if summary.requires_review:
            points.append("Resumo pendente de revisao profissional; nao apresentar como validado.")
        return points

    def source_label(self, summary: MedicationCounselingSummaryModel | None) -> str | None:
        if summary is None:
            return None
        return (
            f"{summary.source_name} [{summary.jurisdiction}, "
            f"{summary.validation_status}, {summary.source_version or 'sem versao'}]"
        )

    def _generic_warnings(self, summary: MedicationCounselingSummaryModel | None) -> list[str]:
        if summary is None:
            return ["Dados funcionais desconhecidos; manter orientacao geral."]
        warnings: list[str] = []
        if summary.driving_warning:
            warnings.append("Cautela ao dirigir ate saber como o paciente reage.")
        if summary.machine_operation_warning or summary.sedation_attention_warning:
            warnings.append("Cautela ao operar maquinas ou tarefas de alta atencao.")
        if summary.work_at_height_warning or summary.fall_risk_warning:
            warnings.append("Cautela em trabalho em altura, risco de queda ou atividade de risco.")
        if summary.blood_pressure_warning:
            warnings.append("Orientar levantar devagar e observar tontura/queda de pressao.")
        if not warnings:
            warnings.append("Sem alerta funcional especifico extraido dos trechos disponiveis.")
        return warnings

    def _has_activity_relevant_risk(self, summary: MedicationCounselingSummaryModel | None) -> bool:
        if summary is None:
            return False
        effects = set(summary.sleep_effects or []) | set(summary.main_adverse_effects or [])
        return bool(
            summary.driving_warning
            or summary.machine_operation_warning
            or summary.work_at_height_warning
            or summary.fall_risk_warning
            or summary.sedation_attention_warning
            or summary.blood_pressure_warning
            or effects
            & {
                "tontura",
                "sedacao",
                "sonolencia",
                "alteracao_atencao_reflexos",
                "hipotensao",
                "hipotensao_ortostatica",
            }
        )
