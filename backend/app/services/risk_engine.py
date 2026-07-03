from app.domain.alert import Alert, PrescriptionStatus, RiskLevel
from app.domain.medication import Medication
from app.domain.patient import Patient
from app.domain.prescription import PrescriptionInput, PrescriptionResult
from app.services.allergy_checker import check_allergies
from app.services.clinical_context_graph import build_clinical_context_graph
from app.services.controlled_vocabulary import label_for_code
from app.services.dose_calculator import check_max_daily_dose
from app.services.interaction_checker import check_interactions
from app.services.normalizer import has_any_match, normalize_terms
from app.services.text import any_token_matches, normalize_text

RISK_ORDER = [
    RiskLevel.LOW,
    RiskLevel.MODERATE,
    RiskLevel.HIGH,
    RiskLevel.CRITICAL,
]


def _max_risk(alerts: list[Alert]) -> RiskLevel:
    if not alerts:
        return RiskLevel.LOW
    return max((alert.severity for alert in alerts), key=lambda level: RISK_ORDER.index(level))


def _increase_risk(level: RiskLevel) -> RiskLevel:
    index = min(RISK_ORDER.index(level) + 1, len(RISK_ORDER) - 1)
    return RISK_ORDER[index]


def _status_for_risk(level: RiskLevel) -> PrescriptionStatus:
    if level == RiskLevel.CRITICAL:
        return PrescriptionStatus.BLOCKED
    if level in {RiskLevel.MODERATE, RiskLevel.HIGH}:
        return PrescriptionStatus.ATTENTION
    return PrescriptionStatus.RELEASED


def _recommendation(status: PrescriptionStatus) -> str:
    if status == PrescriptionStatus.BLOCKED:
        return "Não prosseguir sem revisão humana e ajuste da prescrição."
    if status == PrescriptionStatus.ATTENTION:
        return "Revisar alertas antes de liberar a prescrição."
    return "Nenhum risco relevante foi identificado pelas regras cadastradas."


class RiskEngine:
    def evaluate(
        self,
        patient: Patient,
        medication: Medication,
        prescription: PrescriptionInput,
    ) -> PrescriptionResult:
        alerts: list[Alert] = []
        alerts.extend(check_allergies(patient, medication))
        alerts.extend(check_max_daily_dose(medication, prescription))
        alerts.extend(check_interactions(medication, patient.current_medications))
        alerts.extend(self._check_polypharmacy(patient))
        alerts.extend(self._check_contraindications(patient, medication))
        alerts.extend(self._check_route(medication, prescription))
        alerts.extend(self._check_duration_and_cumulative_dose(medication, prescription))
        alerts.extend(self._check_exposure_and_monitoring(medication, prescription))
        alerts.extend(self._check_condition_specific_limits(patient, medication, prescription))
        alerts.extend(self._check_patient_medication_context(patient, medication))
        alerts.extend(self._check_pharmacokinetic_profile(patient, medication))
        alerts.extend(self._check_neuropsychiatric_context(patient, medication))
        alerts.extend(self._check_reproductive_gynecologic_context(patient, medication))
        alerts.extend(self._check_adverse_history(patient, medication))
        alerts.extend(self._check_profile_completeness(patient))

        risk_level = _max_risk(alerts)
        if self._is_elderly(patient):
            alerts.append(
                Alert(
                    code="AGE_RISK",
                    title="Fator de risco por idade",
                    description="Paciente com idade igual ou superior a 65 anos.",
                    severity=RiskLevel.LOW,
                    recommendation="Aplicar revisão cuidadosa da prescrição.",
                )
            )
            risk_level = _increase_risk(risk_level)
            if medication.elderly_caution:
                alerts.append(
                    Alert(
                        code="ELDERLY_CAUTION",
                        title="Cautela em paciente idoso",
                        description="Medicamento possui cautela demonstrativa para idosos.",
                        severity=RiskLevel.HIGH,
                        recommendation="Revisar dose, duração e monitoramento antes de prosseguir.",
                    )
                )
                risk_level = _max_risk(alerts)

        status = _status_for_risk(risk_level)
        dose_summary = self._dose_summary(medication, prescription)
        compatibility = self._compatibility(patient, medication, alerts, status)
        graph = build_clinical_context_graph(
            patient,
            medication,
            prescription,
            [alert.to_dict() for alert in alerts],
        )
        return PrescriptionResult(
            status=status,
            risk_level=risk_level,
            alerts=alerts,
            recommendation=_recommendation(status),
            human_review_required=status != PrescriptionStatus.RELEASED,
            dose_summary=dose_summary,
            compatibility=compatibility,
            clinical_context_graph=graph,
        )

    def _check_polypharmacy(self, patient: Patient) -> list[Alert]:
        if len(patient.current_medications) < 5:
            return []
        return [
            Alert(
                code="POLYPHARMACY",
                title="Polifarmácia identificada",
                description="Paciente usa cinco ou mais medicamentos contínuos.",
                severity=RiskLevel.MODERATE,
                recommendation="Revisar necessidade, duplicidades e risco cumulativo.",
            )
        ]

    def _check_contraindications(self, patient: Patient, medication: Medication) -> list[Alert]:
        if not any_token_matches(patient.comorbidities, medication.contraindications):
            return []
        return [
            Alert(
                code="CONTRAINDICATION",
                title="Contraindicação por comorbidade",
                description="Comorbidade do paciente coincide com contraindicação cadastrada.",
                severity=RiskLevel.HIGH,
                recommendation="Revisar a prescrição e considerar alternativa terapêutica.",
            )
        ]

    def _check_route(self, medication: Medication, prescription: PrescriptionInput) -> list[Alert]:
        informed_route = normalize_text(prescription.route)
        allowed_routes = [normalize_text(route) for route in medication.allowed_routes]
        if informed_route in allowed_routes:
            return []
        return [
            Alert(
                code="INVALID_ROUTE",
                title="Via não permitida",
                description="Via informada não consta nas vias permitidas do medicamento.",
                severity=RiskLevel.HIGH,
                recommendation="Ajustar a via de administração antes de prosseguir.",
            )
        ]

    def _check_duration_and_cumulative_dose(
        self, medication: Medication, prescription: PrescriptionInput
    ) -> list[Alert]:
        alerts: list[Alert] = []
        if medication.max_duration_days and prescription.duration_days is None:
            alerts.append(
                Alert(
                    code="MISSING_DURATION",
                    title="Duração não informada",
                    description="Medicamento possui limitação demonstrativa de duração.",
                    severity=RiskLevel.LOW,
                    recommendation="Informar duração planejada para estimar dose acumulada.",
                )
            )
            return alerts

        if prescription.duration_days and medication.max_duration_days:
            if prescription.duration_days > medication.max_duration_days:
                alerts.append(
                    Alert(
                        code="DURATION_LIMIT_EXCEEDED",
                        title="Duração acima do limite demonstrativo",
                        description=(
                            f"Duração planejada: {prescription.duration_days} dias. "
                            f"Limite demonstrativo: {medication.max_duration_days} dias."
                        ),
                        severity=RiskLevel.HIGH,
                        recommendation="Revisar necessidade, duração e monitoramento.",
                    )
                )

        cumulative = self._cumulative_dose(prescription)
        if (
            cumulative is not None
            and medication.max_cumulative_dose_mg
            and cumulative > medication.max_cumulative_dose_mg
        ):
            alerts.append(
                Alert(
                    code="CUMULATIVE_DOSE_EXCEEDED",
                    title="Dose acumulada acima do limite demonstrativo",
                    description=(
                        f"Dose acumulada estimada: {cumulative:g} mg. "
                        f"Limite demonstrativo: {medication.max_cumulative_dose_mg:g} mg."
                    ),
                    severity=RiskLevel.HIGH,
                    recommendation="Revisar duração, dose diária e alternativa terapêutica.",
                )
            )
        return alerts

    def _check_exposure_and_monitoring(
        self, medication: Medication, prescription: PrescriptionInput
    ) -> list[Alert]:
        alerts: list[Alert] = []
        if medication.continuous_use and prescription.duration_days is None:
            alerts.append(
                Alert(
                    code="CONTINUOUS_USE_REVIEW",
                    title="Uso contÃ­nuo exige plano de revisÃ£o",
                    description=(
                        "Medicamento marcado como uso contÃ­nuo ou prolongado sem duraÃ§Ã£o "
                        "planejada informada."
                    ),
                    severity=RiskLevel.LOW,
                    recommendation="Confirmar plano terapÃªutico, reavaliaÃ§Ã£o e monitoramento.",
                )
            )
        if medication.monitoring_required:
            alerts.append(
                Alert(
                    code="MONITORING_REQUIRED",
                    title="Monitoramento laboratorial ou clÃ­nico necessÃ¡rio",
                    description=(
                        medication.monitoring_notes
                        or "Medicamento possui monitoramento demonstrativo cadastrado."
                    ),
                    severity=RiskLevel.MODERATE,
                    recommendation=(
                        "Registrar parametros de monitoramento antes de uso prolongado."
                    ),
                )
            )
        if (
            prescription.duration_days is not None
            and prescription.duration_days > 30
            and (medication.monitoring_required or medication.continuous_use)
        ):
            alerts.append(
                Alert(
                    code="PROLONGED_USE_REVIEW",
                    title="Uso prolongado a revisar",
                    description=(
                        f"DuraÃ§Ã£o planejada: {prescription.duration_days} dias. "
                        "Uso prolongado pode exigir seguimento mesmo com dose diÃ¡ria baixa."
                    ),
                    severity=RiskLevel.MODERATE,
                    recommendation="Revisar duraÃ§Ã£o, benefÃ­cio, risco acumulado e seguimento.",
                )
            )
        return alerts

    def _check_condition_specific_limits(
        self, patient: Patient, medication: Medication, prescription: PrescriptionInput
    ) -> list[Alert]:
        alerts: list[Alert] = []
        daily_total = prescription.daily_total_mg
        limits = medication.condition_specific_limits or {}
        patient_conditions = normalize_terms(
            [
                patient.renal_condition or "",
                patient.hepatic_condition or "",
                patient.cardiac_condition or "",
                patient.gastrointestinal_history or "",
                *patient.comorbidities,
            ]
        )
        for condition in patient_conditions:
            limit = limits.get(condition)
            if limit and daily_total > float(limit):
                alerts.append(
                    Alert(
                        code="CONDITION_SPECIFIC_LIMIT_EXCEEDED",
                        title="Limite por quadro clínico excedido",
                        description=(
                            f"Para o contexto {condition}, o limite demonstrativo "
                            f"é {limit:g} mg/dia. "
                            f"Dose diária calculada: {daily_total:g} mg."
                        ),
                        severity=RiskLevel.HIGH,
                        recommendation="Revisar limite específico antes de prosseguir.",
                    )
                )
        return alerts

    def _check_patient_medication_context(
        self, patient: Patient, medication: Medication
    ) -> list[Alert]:
        alerts: list[Alert] = []
        checks = [
            (
                medication.renal_caution and bool(patient.renal_condition),
                "RENAL_CAUTION",
                "Cautela renal",
                "Paciente possui histórico renal e medicamento tem cautela renal demonstrativa.",
            ),
            (
                medication.hepatic_caution and bool(patient.hepatic_condition),
                "HEPATIC_CAUTION",
                "Cautela hepática",
                (
                    "Paciente possui histórico hepático e medicamento tem cautela "
                    "hepática demonstrativa."
                ),
            ),
            (
                medication.cardiac_caution and bool(patient.cardiac_condition),
                "CARDIAC_CAUTION",
                "Cautela cardíaca",
                (
                    "Paciente possui histórico cardíaco e medicamento tem cautela "
                    "cardíaca demonstrativa."
                ),
            ),
            (
                medication.gastrointestinal_caution and bool(patient.gastrointestinal_history),
                "GASTROINTESTINAL_CAUTION",
                "Cautela gastrointestinal",
                "Histórico gastrointestinal pode aumentar risco demonstrativo do medicamento.",
            ),
        ]
        for should_alert, code, title, description in checks:
            if should_alert:
                alerts.append(
                    Alert(
                        code=code,
                        title=title,
                        description=description,
                        severity=RiskLevel.HIGH,
                        recommendation="Revisar perfil clínico e monitoramento profissional.",
                    )
                )
        return alerts

    def _check_pharmacokinetic_profile(
        self, patient: Patient, medication: Medication
    ) -> list[Alert]:
        alerts: list[Alert] = []
        renal_level = normalize_text(medication.renal_elimination_level).replace(" ", "_")
        hepatic_level = normalize_text(medication.hepatic_metabolism_level).replace(" ", "_")
        high_levels = {"alto", "critico_revisar", "critico"}
        if patient.renal_condition and renal_level in high_levels:
            alerts.append(
                Alert(
                    code="RENAL_ELIMINATION_REVIEW",
                    title="EliminaÃ§Ã£o renal relevante",
                    description=(
                        "Perfil farmacocinÃ©tico indica eliminaÃ§Ã£o renal relevante e o "
                        "paciente possui fator renal cadastrado."
                    ),
                    severity=RiskLevel.HIGH,
                    recommendation="Revisar funÃ§Ã£o renal, dose, intervalo e monitoramento.",
                )
            )
        if patient.hepatic_condition and hepatic_level in high_levels:
            alerts.append(
                Alert(
                    code="HEPATIC_METABOLISM_REVIEW",
                    title="MetabolizaÃ§Ã£o hepÃ¡tica relevante",
                    description=(
                        "Perfil farmacocinÃ©tico indica metabolismo hepÃ¡tico relevante e o "
                        "paciente possui fator hepÃ¡tico cadastrado."
                    ),
                    severity=RiskLevel.HIGH,
                    recommendation=(
                        "Revisar funcao hepatica, dose, interacoes e monitoramento."
                    ),
                )
            )
        return alerts

    def _check_neuropsychiatric_context(
        self, patient: Patient, medication: Medication
    ) -> list[Alert]:
        alerts: list[Alert] = []
        cautions = set(normalize_terms(medication.neuropsychiatric_cautions or []))
        patient_factors = set(normalize_terms(patient.mental_health_factors or []))
        patient_terms = set(normalize_terms(patient.comorbidities or []))
        current = set(normalize_terms(patient.current_medications or []))
        therapeutic_terms = set(
            normalize_terms([medication.therapeutic_class, *(medication.therapeutic_classes or [])])
        )
        active = normalize_text(medication.active_ingredient)
        is_serotonergic = bool(
            cautions & {"risco serotoninergico", "uso isrs"}
            or active in {"sertralina", "fluoxetina", "paroxetina", "escitalopram"}
            or "serotonina" in normalize_text(medication.therapeutic_class)
            or "inibidor seletivo da recaptacao de serotonina" in therapeutic_terms
        )
        patient_serotonergic = bool(
            patient_factors & {"uso isrs", "risco serotoninergico"}
            or current
            & {
                "sertralina",
                "fluoxetina",
                "paroxetina",
                "escitalopram",
                "citalopram",
                "venlafaxina",
                "duloxetina",
            }
        )
        if is_serotonergic and patient_serotonergic:
            alerts.append(
                Alert(
                    code="SEROTONERGIC_REVIEW",
                    title="Risco serotoninÃ©rgico demonstrativo",
                    description=(
                        "Paciente jÃ¡ possui fator ou medicamento serotoninÃ©rgico e a nova "
                        "prescriÃ§Ã£o tambÃ©m tem cautela cadastrada."
                    ),
                    severity=RiskLevel.MODERATE,
                    recommendation="Revisar associaÃ§Ã£o, dose, sinais de alerta e alternativas.",
                )
            )

        patient_uses_imao = bool(
            "uso imao" in patient_factors
            or current & {"imao", "fenelzina", "tranilcipromina", "selegilina"}
        )
        if patient_uses_imao and (
            is_serotonergic or bool(cautions & {"uso imao", "interacao imao"})
        ):
            alerts.append(
                Alert(
                    code="IMAO_INTERACTION_REVIEW",
                    title="Uso de IMAO exige revisÃ£o",
                    description=(
                        "Paciente possui uso de IMAO e o medicamento novo tem cautela "
                        "demonstrativa de interaÃ§Ã£o."
                    ),
                    severity=RiskLevel.HIGH,
                    recommendation="Revisar interaÃ§Ã£o em fonte validada antes de prosseguir.",
                )
            )

        seizure_history = bool(
            "epilepsia convulsoes" in patient_factors
            or patient_terms & {"epilepsia", "convulsao", "convulsoes"}
        )
        if seizure_history and bool(cautions & {"limiar convulsivo", "epilepsia convulsoes"}):
            alerts.append(
                Alert(
                    code="SEIZURE_THRESHOLD_REVIEW",
                    title="HistÃ³rico convulsivo a revisar",
                    description=(
                        "Paciente possui histÃ³rico de convulsÃµes e o medicamento tem cautela "
                        "demonstrativa de limiar convulsivo."
                    ),
                    severity=RiskLevel.MODERATE,
                    recommendation="Revisar risco neuropsiquiÃ¡trico com fonte validada.",
                )
            )

        central_depressants = {
            "benzodiazepinico",
            "diazepam",
            "clonazepam",
            "alprazolam",
            "zolpidem",
            "opioide",
            "morfina",
            "tramadol",
        }
        if bool(cautions & {"risco sedacao"}) and bool(current & central_depressants):
            alerts.append(
                Alert(
                    code="SEDATION_REVIEW",
                    title="SedaÃ§Ã£o/depressÃ£o do SNC a revisar",
                    description=(
                        "Medicamento possui cautela de sedaÃ§Ã£o e o paciente usa depressor do "
                        "SNC demonstrativo."
                    ),
                    severity=RiskLevel.MODERATE,
                    recommendation=(
                        "Revisar risco de sedacao, quedas e orientacoes ao paciente."
                    ),
                )
            )

        if patient_factors and cautions and not {
            "SEROTONERGIC_REVIEW",
            "IMAO_INTERACTION_REVIEW",
            "SEIZURE_THRESHOLD_REVIEW",
            "SEDATION_REVIEW",
        }.intersection({alert.code for alert in alerts}):
            alerts.append(
                Alert(
                    code="NEUROPSYCHIATRIC_REVIEW",
                    title="Fator neuropsiquiÃ¡trico a revisar",
                    description=(
                        "Paciente possui fator de saÃºde mental e o medicamento tem cautela "
                        "neuropsiquiÃ¡trica cadastrada."
                    ),
                    severity=RiskLevel.LOW,
                    recommendation=(
                        "Revisar contexto neuropsiquiatrico sem assumir contraindicacao."
                    ),
                )
            )
        return alerts

    def _check_reproductive_gynecologic_context(
        self, patient: Patient, medication: Medication
    ) -> list[Alert]:
        alerts: list[Alert] = []
        patient_factors = set(normalize_terms(patient.reproductive_gynecologic_factors or []))
        cautions = set(normalize_terms(medication.reproductive_cautions or []))
        active = normalize_text(medication.active_ingredient)
        uses_hormonal_contraceptive = bool(
            patient_factors
            & {"uso anticoncepcional hormonal", "diu hormonal", "tratamento hormonal"}
        )
        if active in {"rifampicina", "rifabutina"} and uses_hormonal_contraceptive:
            alerts.append(
                Alert(
                    code="RIFAMYCIN_HORMONAL_CONTRACEPTIVE_REVIEW",
                    title="Rifamicina e contraceptivo hormonal",
                    description=(
                        "Regra demonstrativa especÃ­fica para rifampicina/rifabutina: pode haver "
                        "reduÃ§Ã£o da eficÃ¡cia contraceptiva hormonal. NÃ£o se aplica a todo "
                        "antibiÃ³tico."
                    ),
                    severity=RiskLevel.HIGH,
                    recommendation="Recomendar revisÃ£o profissional e orientaÃ§Ã£o contraceptiva.",
                )
            )

        pregnancy_lactation = bool(
            patient.pregnancy_or_lactation
            or patient_factors & {"gestante", "lactante", "tentando engravidar"}
        )
        if pregnancy_lactation and bool(
            cautions & {"gestante", "lactante", "cautela reprodutiva", "tentando engravidar"}
        ):
            alerts.append(
                Alert(
                    code="REPRODUCTIVE_REVIEW",
                    title="Gestacao/lactacao a revisar",
                    description=(
                        "Paciente possui fator gestacional, lactacional ou reprodutivo e o "
                        "medicamento tem cautela reprodutiva cadastrada."
                    ),
                    severity=RiskLevel.HIGH,
                    recommendation="Revisar fonte validada, trimestre/lactacao e alternativas.",
                )
            )

        if "risco trombotico" in patient_factors and "risco trombotico" in cautions:
            alerts.append(
                Alert(
                    code="THROMBOTIC_REVIEW",
                    title="Risco trombÃ³tico a revisar",
                    description=(
                        "Paciente possui fator trombÃ³tico e medicamento tem cautela trombÃ³tica "
                        "cadastrada."
                    ),
                    severity=RiskLevel.MODERATE,
                    recommendation="Revisar risco individual e fonte validada antes de prosseguir.",
                )
            )

        gynecologic_factors = {
            "endometriose",
            "sop",
            "ciclo irregular",
            "quadro ginecologico a revisar",
        }
        if bool(patient_factors & gynecologic_factors) and bool(cautions):
            alerts.append(
                Alert(
                    code="GYNECOLOGIC_REVIEW",
                    title="Quadro ginecolÃ³gico a revisar",
                    description=(
                        "Paciente possui fator ginecolÃ³gico e medicamento tem cautela "
                        "relacionada cadastrada."
                    ),
                    severity=RiskLevel.LOW,
                    recommendation="Revisar contexto ginecolÃ³gico sem assumir contraindicaÃ§Ã£o.",
                )
            )
        return alerts

    def _check_adverse_history(self, patient: Patient, medication: Medication) -> list[Alert]:
        adverse_reactions = patient.adverse_reactions or []
        medication_terms = [
            medication.brand_name,
            medication.active_ingredient,
            medication.therapeutic_class,
            *(medication.relevant_adverse_effects or []),
            *(medication.structured_contraindications or []),
        ]
        if not has_any_match(adverse_reactions, medication_terms):
            return []
        return [
            Alert(
                code="ADVERSE_REACTION_HISTORY",
                title="Reação adversa prévia relacionada",
                description=(
                    "Histórico do paciente coincide com classe, efeito ou medicamento cadastrado."
                ),
                severity=RiskLevel.HIGH,
                recommendation="Revisar histórico antes de considerar a prescrição.",
            )
        ]

    def _check_profile_completeness(self, patient: Patient) -> list[Alert]:
        has_clinical_context = any(
            [
                label_for_code(patient.renal_condition),
                label_for_code(patient.hepatic_condition),
                label_for_code(patient.cardiac_condition),
                label_for_code(patient.gastrointestinal_history),
                patient.hypertension,
                patient.diabetes,
                patient.mental_health_factors,
                patient.reproductive_gynecologic_factors,
                patient.adverse_reactions,
            ]
        )
        if patient.clinical_profile_completeness_score >= 75 or not has_clinical_context:
            return []
        return [
            Alert(
                code="INCOMPLETE_CLINICAL_PROFILE",
                title="Perfil clínico incompleto",
                description="Nem todos os dados clínicos demonstrativos foram revisados.",
                severity=RiskLevel.LOW,
                recommendation=(
                    "Completar triagem antes de interpretar compatibilidade como certeza."
                ),
            )
        ]

    def _dose_summary(self, medication: Medication, prescription: PrescriptionInput) -> dict:
        cumulative = self._cumulative_dose(prescription)
        return {
            "daily_total_mg": prescription.daily_total_mg,
            "duration_days": prescription.duration_days,
            "estimated_cumulative_dose_mg": cumulative,
            "max_daily_dose_mg": medication.max_daily_dose_mg,
            "max_duration_days": medication.max_duration_days,
            "max_cumulative_dose_mg": medication.max_cumulative_dose_mg,
            "continuous_use": medication.continuous_use,
            "monitoring_required": medication.monitoring_required,
            "monitoring_notes": medication.monitoring_notes,
            "exposure_plan": {
                "dose_per_administration_mg": prescription.dose_mg,
                "administrations_per_day": prescription.frequency_per_day,
                "calculated_daily_dose_mg": prescription.daily_total_mg,
                "calculated_cumulative_dose_mg": cumulative,
                "has_missing_duration_for_cumulative_dose": (
                    prescription.duration_days is None
                    and bool(medication.max_cumulative_dose_mg or medication.max_duration_days)
                ),
            },
            "mechanism_profile": {
                "mechanism_of_action": medication.mechanism_of_action,
                "absorption_notes": medication.absorption_notes,
                "distribution_notes": medication.distribution_notes,
                "metabolism_organs": medication.metabolism_organs or [],
                "elimination_organs": medication.elimination_organs or [],
                "renal_elimination_level": medication.renal_elimination_level,
                "hepatic_metabolism_level": medication.hepatic_metabolism_level,
                "cyp_interactions": medication.cyp_interactions or [],
                "pharmacodynamic_notes": medication.pharmacodynamic_notes,
                "pharmacokinetic_notes": medication.pharmacokinetic_notes,
                "clinical_interpretation": medication.clinical_interpretation,
            },
            "condition_specific_limits": medication.condition_specific_limits or {},
        }

    def _compatibility(
        self,
        patient: Patient,
        medication: Medication,
        alerts: list[Alert],
        status: PrescriptionStatus,
    ) -> dict:
        high_or_critical = [
            alert for alert in alerts if alert.severity in {RiskLevel.HIGH, RiskLevel.CRITICAL}
        ]
        moderate = [alert for alert in alerts if alert.severity == RiskLevel.MODERATE]
        if status == PrescriptionStatus.BLOCKED or any(
            alert.severity == RiskLevel.CRITICAL for alert in alerts
        ):
            level = "baixa"
            score = 20
        elif high_or_critical or len(moderate) >= 2:
            level = "moderada"
            score = 55
        elif patient.clinical_profile_completeness_score >= 75:
            level = "alta"
            score = 85
        else:
            level = "moderada"
            score = 65

        patient_factors = [
            factor
            for factor in [
                patient.renal_condition,
                patient.hepatic_condition,
                patient.cardiac_condition,
                patient.gastrointestinal_history,
                "hipertensão" if patient.hypertension else None,
                "diabetes" if patient.diabetes else None,
                *(patient.mental_health_factors or []),
                *(patient.reproductive_gynecologic_factors or []),
                *(patient.adverse_reactions or []),
            ]
            if factor
        ]
        medication_factors = [
            factor
            for factor in [
                "cautela renal" if medication.renal_caution else None,
                "cautela hepática" if medication.hepatic_caution else None,
                "cautela cardíaca" if medication.cardiac_caution else None,
                "cautela gastrointestinal" if medication.gastrointestinal_caution else None,
                "cautela em idosos" if medication.elderly_caution else None,
                f"princípio ativo: {medication.active_ingredient}",
                f"jurisdição da fonte: {medication.source_jurisdiction}",
                f"fonte: {medication.evidence_source_type}",
                f"validação: {medication.validation_status}",
                "uso continuo" if medication.continuous_use else None,
                "monitoramento necessario" if medication.monitoring_required else None,
                medication.mechanism_of_action,
                f"eliminacao renal: {medication.renal_elimination_level}",
                f"metabolizacao hepatica: {medication.hepatic_metabolism_level}",
                *(medication.cyp_interactions or []),
                *(medication.neuropsychiatric_cautions or []),
                *(medication.reproductive_cautions or []),
                *(medication.organs_involved or []),
            ]
            if factor
        ]
        reasons = [alert.title for alert in alerts[:5]]
        return {
            "level": level,
            "score": score,
            "patient_factors_considered": patient_factors,
            "medication_factors_considered": medication_factors,
            "reasons": reasons,
            "review_required": level != "alta" or patient.clinical_profile_completeness_score < 75,
            "educational_notice": "Compatibilidade demonstrativa; requer revisão profissional.",
        }

    def _cumulative_dose(self, prescription: PrescriptionInput) -> float | None:
        if prescription.duration_days is None:
            return None
        return prescription.daily_total_mg * prescription.duration_days

    def _is_elderly(self, patient: Patient) -> bool:
        age = patient.computed_age
        return age is not None and age >= 65
