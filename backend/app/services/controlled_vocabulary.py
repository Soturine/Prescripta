from __future__ import annotations

from dataclasses import dataclass

from app.services.normalizer import normalize_text


@dataclass(frozen=True)
class VocabularyEntry:
    category: str
    code: str
    label: str
    severity_weight: int = 0
    description: str | None = None

    @property
    def normalized_label(self) -> str:
        return normalize_text(self.label)


VOCABULARY: tuple[VocabularyEntry, ...] = (
    VocabularyEntry("renal", "sem_informacao", "Sem informação"),
    VocabularyEntry("renal", "sem_doenca_renal_conhecida", "Sem doença renal conhecida"),
    VocabularyEntry("renal", "doenca_renal_cronica", "Doença renal crônica", 2),
    VocabularyEntry("renal", "drc_estagio_1", "Doença renal crônica estágio 1", 1),
    VocabularyEntry("renal", "drc_estagio_2", "Doença renal crônica estágio 2", 1),
    VocabularyEntry("renal", "drc_estagio_3", "Doença renal crônica estágio 3", 2),
    VocabularyEntry("renal", "drc_estagio_4", "Doença renal crônica estágio 4", 3),
    VocabularyEntry("renal", "drc_estagio_5", "Doença renal crônica estágio 5", 3),
    VocabularyEntry("renal", "hemodialise", "Hemodiálise", 3),
    VocabularyEntry("renal", "transplante_renal", "Transplante renal", 2),
    VocabularyEntry("renal", "calculo_renal_recorrente", "Cálculo renal recorrente", 1),
    VocabularyEntry("renal", "funcao_renal_a_revisar", "Função renal a revisar", 1),
    VocabularyEntry("hepatic", "sem_informacao", "Sem informação"),
    VocabularyEntry("hepatic", "sem_doenca_hepatica_conhecida", "Sem doença hepática conhecida"),
    VocabularyEntry("hepatic", "esteatose_hepatica", "Esteatose hepática", 1),
    VocabularyEntry("hepatic", "hepatite", "Hepatite", 2),
    VocabularyEntry("hepatic", "cirrose", "Cirrose", 3),
    VocabularyEntry("hepatic", "insuficiencia_hepatica", "Insuficiência hepática", 3),
    VocabularyEntry("hepatic", "enzimas_hepaticas_alteradas", "Enzimas hepáticas alteradas", 2),
    VocabularyEntry("hepatic", "funcao_hepatica_a_revisar", "Função hepática a revisar", 1),
    VocabularyEntry("cardiac", "sem_informacao", "Sem informação"),
    VocabularyEntry("cardiac", "sem_doenca_cardiaca_conhecida", "Sem doença cardíaca conhecida"),
    VocabularyEntry("cardiac", "arritmia", "Arritmia", 2),
    VocabularyEntry("cardiac", "insuficiencia_cardiaca", "Insuficiência cardíaca", 3),
    VocabularyEntry("cardiac", "doenca_arterial_coronariana", "Doença arterial coronariana", 2),
    VocabularyEntry("cardiac", "historico_de_infarto", "Histórico de infarto", 2),
    VocabularyEntry("cardiac", "hipertensao", "Hipertensão", 1),
    VocabularyEntry(
        "cardiac",
        "risco_cardiovascular_a_revisar",
        "Risco cardiovascular a revisar",
        1,
    ),
    VocabularyEntry("gastrointestinal", "sem_informacao", "Sem informação"),
    VocabularyEntry(
        "gastrointestinal",
        "sem_historico_gastrointestinal_conhecido",
        "Sem histórico gastrointestinal conhecido",
    ),
    VocabularyEntry("gastrointestinal", "gastrite", "Gastrite", 1),
    VocabularyEntry("gastrointestinal", "ulcera", "Úlcera", 2),
    VocabularyEntry(
        "gastrointestinal",
        "sangramento_gastrointestinal",
        "Sangramento gastrointestinal",
        3,
    ),
    VocabularyEntry("gastrointestinal", "refluxo_importante", "Refluxo importante", 1),
    VocabularyEntry(
        "gastrointestinal",
        "doenca_inflamatoria_intestinal",
        "Doença inflamatória intestinal",
        2,
    ),
    VocabularyEntry(
        "gastrointestinal",
        "historico_gastrointestinal_a_revisar",
        "Histórico gastrointestinal a revisar",
        1,
    ),
    VocabularyEntry("metabolic", "diabetes_tipo_1", "Diabetes tipo 1", 2),
    VocabularyEntry("metabolic", "diabetes_tipo_2", "Diabetes tipo 2", 2),
    VocabularyEntry("metabolic", "obesidade", "Obesidade", 1),
    VocabularyEntry("metabolic", "dislipidemia", "Dislipidemia", 1),
    VocabularyEntry("pregnancy_lactation", "nao_se_aplica", "Não se aplica"),
    VocabularyEntry("pregnancy_lactation", "nao_informado", "Não informado"),
    VocabularyEntry("pregnancy_lactation", "gestante", "Gestante", 2),
    VocabularyEntry("pregnancy_lactation", "lactante", "Lactante", 2),
    VocabularyEntry(
        "pregnancy_lactation",
        "possibilidade_a_confirmar",
        "Possibilidade a confirmar",
        1,
    ),
)

ENTRY_BY_CATEGORY_CODE = {(entry.category, entry.code): entry for entry in VOCABULARY}
ENTRY_BY_CODE = {entry.code: entry for entry in VOCABULARY}

GENERIC_VALUE_MAP = {
    ("renal", "renal"): "funcao_renal_a_revisar",
    ("renal", "rim"): "funcao_renal_a_revisar",
    ("renal", "rins"): "funcao_renal_a_revisar",
    ("renal", "problema renal"): "funcao_renal_a_revisar",
    ("renal", "doenca renal"): "doenca_renal_cronica",
    ("hepatic", "hepatico"): "funcao_hepatica_a_revisar",
    ("hepatic", "hepatica"): "funcao_hepatica_a_revisar",
    ("hepatic", "figado"): "funcao_hepatica_a_revisar",
    ("cardiac", "cardiaco"): "risco_cardiovascular_a_revisar",
    ("cardiac", "cardiaca"): "risco_cardiovascular_a_revisar",
    ("cardiac", "cardiovascular"): "risco_cardiovascular_a_revisar",
    ("gastrointestinal", "gastrointestinal"): "historico_gastrointestinal_a_revisar",
    ("gastrointestinal", "estomago"): "historico_gastrointestinal_a_revisar",
    ("gastrointestinal", "sangramento gastrointestinal"): "sangramento_gastrointestinal",
}

CATEGORY_FIELD_MAP = {
    "renal_condition": "renal",
    "hepatic_condition": "hepatic",
    "cardiac_condition": "cardiac",
    "gastrointestinal_history": "gastrointestinal",
}


def entries_for_category(category: str) -> list[VocabularyEntry]:
    return [entry for entry in VOCABULARY if entry.category == category]


def normalize_clinical_code(category: str, value: str | None) -> str | None:
    if not value:
        return None
    if (category, value) in ENTRY_BY_CATEGORY_CODE:
        return value

    normalized = normalize_text(value)
    mapped = GENERIC_VALUE_MAP.get((category, normalized))
    if mapped:
        return mapped

    for entry in entries_for_category(category):
        if normalized in {normalize_text(entry.code), entry.normalized_label}:
            return entry.code
    return "sem_informacao"


def normalize_patient_clinical_fields(values: dict) -> dict:
    normalized = dict(values)
    for field, category in CATEGORY_FIELD_MAP.items():
        if field in normalized:
            normalized[field] = normalize_clinical_code(category, normalized[field])
    return normalized


def label_for_code(code: str | None) -> str:
    if not code:
        return ""
    entry = ENTRY_BY_CODE.get(code)
    return entry.label if entry else code


def category_for_patient_field(field: str) -> str | None:
    return CATEGORY_FIELD_MAP.get(field)
