from collections.abc import Iterable
from typing import Any

from app.domain.alert import RiskLevel
from app.domain.clinical_intelligence import PsychotropicRiskSignal
from app.services.normalizer import normalize_text

CLASSES: dict[str, set[str]] = {
    "ssri": {"sertralina", "fluoxetina", "escitalopram", "citalopram", "paroxetina", "fluvoxamina"},
    "snri": {"venlafaxina", "desvenlafaxina", "duloxetina"},
    "tca": {"amitriptilina", "nortriptilina", "clomipramina", "imipramina"},
    "maoi": {"tranilcipromina", "fenelzina", "selegilina", "moclobemida"},
    "antidepressant": {"bupropiona", "trazodona", "mirtazapina"},
    "stimulant": {"metilfenidato", "lisdexanfetamina", "anfetamina"},
    "benzodiazepine": {"diazepam", "clonazepam", "alprazolam", "lorazepam", "midazolam"},
    "z_drug": {"zolpidem", "zopiclona", "eszopiclona"},
    "opioid": {"morfina", "fentanil", "tramadol", "metadona", "oxicodona", "codeina"},
    "gabapentinoid": {"gabapentina", "pregabalina"},
    "antipsychotic": {
        "quetiapina",
        "risperidona",
        "haloperidol",
        "clozapina",
        "olanzapina",
        "ziprasidona",
    },
    "anticholinergic": {"amitriptilina", "clomipramina", "biperideno", "prometazina"},
    "qt": {"metadona", "haloperidol", "ziprasidona", "citalopram", "escitalopram"},
}
CLASSES["serotonergic"] = (
    CLASSES["ssri"]
    | CLASSES["snri"]
    | CLASSES["tca"]
    | CLASSES["maoi"]
    | {"tramadol", "linezolida", "litio", "erva de sao joao", "sumatriptana"}
)
CLASSES["sedative"] = (
    CLASSES["benzodiazepine"]
    | CLASSES["z_drug"]
    | CLASSES["opioid"]
    | CLASSES["gabapentinoid"]
    | {"quetiapina", "prometazina"}
)


class PsychotropicSafetyService:
    """Sinais heurísticos: não diagnostica e não altera o risco final da prescrição."""

    def evaluate(
        self,
        medication: Any,
        patient: Any,
        current_medications: Iterable[str] | None = None,
        functional_profile: Any | None = None,
    ) -> list[PsychotropicRiskSignal]:
        def get(obj: Any, key: str, default: Any = None) -> Any:
            return obj.get(key, default) if isinstance(obj, dict) else getattr(obj, key, default)

        new = normalize_text(
            str(get(medication, "active_ingredient", get(medication, "name", medication)))
        )
        current = {
            normalize_text(str(item))
            for item in (current_medications or get(patient, "current_medications", []) or [])
        }
        all_meds = current | {new}
        factors = {
            normalize_text(str(item))
            for item in (get(patient, "comorbidities", []) or [])
            + (get(patient, "mental_health_factors", []) or [])
            + (get(patient, "reproductive_gynecologic_factors", []) or [])
        }
        for field in (
            "renal_condition",
            "hepatic_condition",
            "cardiac_condition",
            "clinical_notes",
        ):
            value = get(patient, field)
            if value:
                factors.add(normalize_text(str(value)))
        signals: list[PsychotropicRiskSignal] = []

        def has_factor(*terms: str) -> bool:
            return any(any(normalize_text(term) in value for term in terms) for value in factors)

        def meds(kind: str) -> set[str]:
            return {item for item in all_meds if any(term in item for term in CLASSES[kind])}

        def add(
            code: str,
            title: str,
            severity: RiskLevel,
            mechanism: str,
            involved: set[str] | None = None,
            missing: list[str] | None = None,
            recommendation: str = (
                "Revisar indicação, associação, dose, monitoramento e alternativas com "
                "profissional habilitado."
            ),
        ) -> None:
            signals.append(
                PsychotropicRiskSignal(
                    code=code,
                    title=title,
                    description=(
                        f"Sinal determinístico de {title.lower()}; não representa diagnóstico."
                    ),
                    severity=severity,
                    mechanism=mechanism,
                    interacting_medications=sorted(involved or []),
                    patient_factors=sorted(factors)[:12],
                    missing_data=missing or [],
                    recommendation=recommendation,
                )
            )

        serotonergic = meds("serotonergic")
        if meds("maoi") and (meds("ssri") | meds("snri") | meds("tca")):
            add(
                "SEROTONERGIC_MAOI_COMBINATION",
                "Combinação serotoninérgica com IMAO",
                RiskLevel.CRITICAL,
                "excesso serotoninérgico",
                serotonergic,
            )
        elif len(serotonergic) >= 2:
            code = "SEROTONERGIC_POLYPHARMACY"
            for term, specific in (
                ("tramadol", "SEROTONERGIC_TRAMADOL"),
                ("linezolida", "SEROTONERGIC_LINEZOLID"),
                ("litio", "SEROTONERGIC_LITHIUM"),
                ("tript", "SEROTONERGIC_TRIPTAN"),
                ("erva de sao joao", "SEROTONERGIC_ST_JOHNS_WORT"),
            ):
                if any(term in med for med in serotonergic):
                    code = specific
                    break
            add(
                code,
                "Risco serotoninérgico a revisar",
                RiskLevel.HIGH,
                "efeito serotoninérgico aditivo",
                serotonergic,
            )
        antidepressants = meds("ssri") | meds("snri") | meds("tca") | meds("antidepressant")
        if antidepressants and has_factor("bipolar", "mania", "hipomania"):
            add(
                "ANTIDEPRESSANT_BIPOLAR_MANIA",
                "Antidepressivo e histórico bipolar/maniforme",
                RiskLevel.HIGH,
                "possível ativação de humor",
                antidepressants,
            )
            stabilizers = {"litio", "valproato", "carbamazepina", "lamotrigina"} & all_meds
            if not stabilizers:
                add(
                    "ANTIDEPRESSANT_WITHOUT_MOOD_STABILIZER",
                    "Estabilizador de humor não informado",
                    RiskLevel.MODERATE,
                    "contexto terapêutico incompleto",
                    antidepressants,
                    ["estabilizador de humor"],
                )
        elif antidepressants and not any(
            any(term in f for term in ("bipolar", "mania", "hipomania", "depress", "ansiedade"))
            for f in factors
        ):
            add(
                "MISSING_MENTAL_HEALTH_HISTORY",
                "Histórico mínimo de saúde mental ausente",
                RiskLevel.LOW,
                "dados insuficientes",
                antidepressants,
                [
                    "Há histórico de mania, hipomania, transtorno bipolar ou internação "
                    "psiquiátrica?"
                ],
            )
        if meds("stimulant") and has_factor("mania", "hipomania", "psicose", "esquizofrenia"):
            add(
                "STIMULANT_MANIA_PSYCHOSIS",
                "Estimulante com mania ou psicose",
                RiskLevel.HIGH,
                "atividade dopaminérgica/estimulante",
                meds("stimulant"),
            )
        if "bupropiona" in all_meds and has_factor("epileps", "convuls"):
            add(
                "BUPROPION_SEIZURE_HISTORY",
                "Bupropiona e histórico convulsivo",
                RiskLevel.HIGH,
                "redução do limiar convulsivo",
                {"bupropiona"},
            )
        if "bupropiona" in all_meds and has_factor("anorexia", "bulimia", "transtorno alimentar"):
            add(
                "BUPROPION_EATING_DISORDER",
                "Bupropiona e transtorno alimentar",
                RiskLevel.HIGH,
                "risco convulsivo aumentado",
                {"bupropiona"},
            )
        if "tramadol" in all_meds and has_factor("epileps", "convuls"):
            add(
                "TRAMADOL_SEIZURE_HISTORY",
                "Tramadol e histórico convulsivo",
                RiskLevel.HIGH,
                "redução do limiar convulsivo",
                {"tramadol"},
            )
        sedatives = meds("sedative")
        alcohol = has_factor("alcool") or bool(
            get(functional_profile or {}, "frequent_alcohol_use", False)
        )
        if meds("benzodiazepine") and meds("opioid"):
            add(
                "BENZODIAZEPINE_OPIOID",
                "Benzodiazepínico com opioide",
                RiskLevel.CRITICAL,
                "depressão aditiva do sistema nervoso central e respiratória",
                sedatives,
            )
        if alcohol and sedatives:
            add(
                "SEDATIVE_ALCOHOL",
                "Sedativo com uso de álcool",
                RiskLevel.HIGH,
                "depressão aditiva do sistema nervoso central",
                sedatives | {"álcool"},
            )
        if meds("gabapentinoid") and meds("opioid"):
            add(
                "GABAPENTINOID_OPIOID",
                "Gabapentinoide com opioide",
                RiskLevel.HIGH,
                "sedação e depressão respiratória aditivas",
                sedatives,
            )
        if sedatives and (
            has_factor("dpoc", "apneia", "insuficiencia respiratoria")
            or (get(patient, "age") or 0) >= 65
        ):
            add(
                "SEDATIVE_RESPIRATORY_ELDERLY",
                "Sedativo com vulnerabilidade respiratória ou idade avançada",
                RiskLevel.HIGH,
                "maior sensibilidade a sedação",
                sedatives,
            )
        if sedatives and any(
            bool(get(functional_profile or {}, field, False))
            for field in ("professional_driver", "operates_machinery", "works_at_height")
        ):
            add(
                "SEDATIVE_HIGH_RISK_ACTIVITY",
                "Sedativo e atividade de risco",
                RiskLevel.HIGH,
                "prejuízo psicomotor",
                sedatives,
            )
        qt_meds = meds("qt")
        if qt_meds and (has_factor("qt", "arritmia") or len(qt_meds) >= 2):
            add(
                "QT_PROLONGATION_CONTEXT",
                "Cautela de QT/arritmia",
                RiskLevel.HIGH,
                "potencial efeito aditivo no intervalo QT",
                qt_meds,
            )
        if "litio" in all_meds:
            if has_factor("renal"):
                add(
                    "LITHIUM_RENAL_DISEASE",
                    "Lítio e condição renal",
                    RiskLevel.HIGH,
                    "eliminação renal e possível acúmulo",
                    {"litio"},
                )
            interactions = {
                m
                for m in all_meds
                if any(
                    t in m
                    for t in (
                        "ibuprofeno",
                        "diclofenaco",
                        "naproxeno",
                        "losartana",
                        "enalapril",
                        "captopril",
                        "hidroclorotiazida",
                        "furosemida",
                    )
                )
            }
            if interactions:
                add(
                    "LITHIUM_INTERACTION",
                    "Lítio com AINE, IECA/BRA ou diurético",
                    RiskLevel.HIGH,
                    "possível alteração da depuração do lítio",
                    interactions | {"litio"},
                )
        if "valproato" in all_meds and (
            get(patient, "pregnancy_or_lactation") is True
            or has_factor("gestacao", "gravidez", "lactacao")
        ):
            add(
                "VALPROATE_REPRODUCTIVE_CONTEXT",
                "Valproato em contexto gestacional/reprodutivo",
                RiskLevel.CRITICAL,
                "risco reprodutivo relevante",
                {"valproato"},
            )
        if "valproato" in all_meds and has_factor("hepat"):
            add(
                "VALPROATE_HEPATIC_DISEASE",
                "Valproato e condição hepática",
                RiskLevel.HIGH,
                "metabolismo e toxicidade hepática",
                {"valproato"},
            )
        if "carbamazepina" in all_meds and has_factor("contracept", "anticoncepc"):
            add(
                "CARBAMAZEPINE_HORMONAL_CONTRACEPTIVE",
                "Carbamazepina e contraceptivo hormonal",
                RiskLevel.HIGH,
                "indução enzimática",
                {"carbamazepina"},
            )
        if meds("antipsychotic") and (
            get(patient, "diabetes", False) or has_factor("diabetes", "metabol", "obesidade")
        ):
            add(
                "ANTIPSYCHOTIC_METABOLIC_RISK",
                "Antipsicótico e risco metabólico",
                RiskLevel.MODERATE,
                "efeitos metabólicos dependentes do fármaco",
                meds("antipsychotic"),
            )
        if meds("anticholinergic") and has_factor(
            "glaucoma", "retencao urinaria", "hiperplasia prostatica", "demencia", "delirium"
        ):
            add(
                "ANTICHOLINERGIC_VULNERABILITY",
                "Carga anticolinérgica em contexto vulnerável",
                RiskLevel.HIGH,
                "efeito antimuscarínico",
                meds("anticholinergic"),
            )
        if "lamotrigina" in all_meds and has_factor("rash", "reacao cutanea", "stevens"):
            add(
                "LAMOTRIGINE_CUTANEOUS_HISTORY",
                "Lamotrigina e histórico de reação cutânea",
                RiskLevel.HIGH,
                "reação cutânea grave exige avaliação imediata",
                {"lamotrigina"},
            )
        if "clozapina" in all_meds:
            add(
                "CLOZAPINE_MONITORING_CONTEXT",
                "Clozapina e monitoramento obrigatório a revisar",
                RiskLevel.HIGH,
                "perfil hematológico, metabólico, cardíaco e convulsivo",
                {"clozapina"},
                ["monitoramento laboratorial vigente"],
            )
        if "metadona" in all_meds and (meds("benzodiazepine") or alcohol):
            add(
                "METHADONE_CNS_DEPRESSANTS",
                "Metadona com depressor do sistema nervoso central",
                RiskLevel.CRITICAL,
                "depressão respiratória e sedação aditivas",
                {"metadona"} | meds("benzodiazepine") | ({"álcool"} if alcohol else set()),
            )
        unique: dict[str, PsychotropicRiskSignal] = {}
        for signal in signals:
            unique.setdefault(signal.deduplication_key, signal)
        return list(unique.values())


PsychotropicSafetyEngine = PsychotropicSafetyService
