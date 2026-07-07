from __future__ import annotations

from dataclasses import dataclass

from app.services.normalizer import normalize_text


@dataclass(frozen=True)
class AdverseEffectCategory:
    category: str
    code: str
    label: str


ADVERSE_EFFECT_TAXONOMY: tuple[AdverseEffectCategory, ...] = (
    AdverseEffectCategory("sleep_attention", "insonia", "Insonia"),
    AdverseEffectCategory("sleep_attention", "sonolencia", "Sonolencia"),
    AdverseEffectCategory("sleep_attention", "sedacao", "Sedacao"),
    AdverseEffectCategory(
        "sleep_attention", "alteracao_atencao_reflexos", "Alteracao de atencao/reflexos"
    ),
    AdverseEffectCategory("sleep_attention", "tontura", "Tontura"),
    AdverseEffectCategory("sleep_attention", "confusao", "Confusao"),
    AdverseEffectCategory("sleep_attention", "fadiga", "Fadiga"),
    AdverseEffectCategory("daily_activity", "dirigir", "Dirigir"),
    AdverseEffectCategory("daily_activity", "operar_maquinas", "Operar maquinas"),
    AdverseEffectCategory("daily_activity", "trabalho_em_altura", "Trabalho em altura"),
    AdverseEffectCategory("daily_activity", "atividade_de_risco", "Atividade de risco"),
    AdverseEffectCategory("daily_activity", "risco_de_queda", "Risco de queda"),
    AdverseEffectCategory("daily_activity", "cuidador_responsavel", "Cuidador responsavel"),
    AdverseEffectCategory("daily_activity", "rotina_alta_atencao", "Rotina que exige alta atencao"),
    AdverseEffectCategory("mood_behavior", "alteracao_humor", "Alteracao de humor"),
    AdverseEffectCategory("mood_behavior", "ansiedade", "Ansiedade"),
    AdverseEffectCategory("mood_behavior", "irritabilidade", "Irritabilidade"),
    AdverseEffectCategory("mood_behavior", "piora_psiquiatrica", "Piora psiquiatrica"),
    AdverseEffectCategory("mood_behavior", "agitacao", "Agitacao"),
    AdverseEffectCategory("mood_behavior", "apatia", "Apatia"),
    AdverseEffectCategory("mood_behavior", "risco_serotoninergico", "Risco serotoninergico"),
    AdverseEffectCategory("appetite_weight", "alteracao_apetite", "Alteracao de apetite"),
    AdverseEffectCategory("appetite_weight", "aumento_apetite", "Aumento de apetite"),
    AdverseEffectCategory("appetite_weight", "reducao_apetite", "Reducao de apetite"),
    AdverseEffectCategory("appetite_weight", "ganho_peso", "Ganho de peso"),
    AdverseEffectCategory("appetite_weight", "perda_peso", "Perda de peso"),
    AdverseEffectCategory("appetite_weight", "alteracao_glicemica", "Alteracao glicemica"),
    AdverseEffectCategory("sexual_reproductive", "baixa_libido", "Baixa libido"),
    AdverseEffectCategory("sexual_reproductive", "disfuncao_sexual", "Disfuncao sexual"),
    AdverseEffectCategory(
        "sexual_reproductive", "alteracao_ejaculatoria", "Alteracao ejaculatoria"
    ),
    AdverseEffectCategory(
        "sexual_reproductive",
        "erecao_persistente_dolorosa",
        "Erecao persistente/dolorosa",
    ),
    AdverseEffectCategory(
        "sexual_reproductive", "alteracao_ciclo_menstrual", "Alteracao do ciclo menstrual"
    ),
    AdverseEffectCategory("sexual_reproductive", "contracepcao", "Contracepcao"),
    AdverseEffectCategory("sexual_reproductive", "gestacao_lactacao", "Gestacao/lactacao"),
    AdverseEffectCategory("sexual_reproductive", "fertilidade_a_revisar", "Fertilidade a revisar"),
    AdverseEffectCategory("neurologic", "dor_cabeca", "Dor de cabeca"),
    AdverseEffectCategory("neurologic", "tremor", "Tremor"),
    AdverseEffectCategory("neurologic", "convulsao", "Convulsao"),
    AdverseEffectCategory("neurologic", "parestesia", "Parestesia"),
    AdverseEffectCategory("neurologic", "vertigem", "Vertigem"),
    AdverseEffectCategory("temperature_autonomic", "hipotermia", "Hipotermia"),
    AdverseEffectCategory("temperature_autonomic", "hipertermia", "Hipertermia"),
    AdverseEffectCategory("temperature_autonomic", "sudorese", "Sudorese"),
    AdverseEffectCategory("temperature_autonomic", "calafrios", "Calafrios"),
    AdverseEffectCategory("cardiovascular_pressure", "hipotensao", "Hipotensao/queda de pressao"),
    AdverseEffectCategory(
        "cardiovascular_pressure", "hipotensao_ortostatica", "Hipotensao ortostatica"
    ),
    AdverseEffectCategory("cardiovascular_pressure", "palpitacao", "Palpitacao"),
    AdverseEffectCategory("cardiovascular_pressure", "arritmia", "Arritmia"),
    AdverseEffectCategory("cardiovascular_pressure", "sinccope_desmaio", "Sincope/desmaio"),
    AdverseEffectCategory("cardiovascular_pressure", "sincope_desmaio", "Sincope/desmaio"),
    AdverseEffectCategory("gastrointestinal", "nausea", "Nausea"),
    AdverseEffectCategory("gastrointestinal", "vomito", "Vomito"),
    AdverseEffectCategory("gastrointestinal", "diarreia", "Diarreia"),
    AdverseEffectCategory("gastrointestinal", "constipacao", "Constipacao"),
    AdverseEffectCategory("gastrointestinal", "dor_abdominal", "Dor abdominal"),
    AdverseEffectCategory(
        "gastrointestinal", "sangramento_gastrointestinal", "Sangramento gastrointestinal"
    ),
    AdverseEffectCategory("renal_hepatic", "cautela_renal", "Cautela renal"),
    AdverseEffectCategory("renal_hepatic", "cautela_hepatica", "Cautela hepatica"),
    AdverseEffectCategory("renal_hepatic", "toxicidade_renal", "Toxicidade renal"),
    AdverseEffectCategory("renal_hepatic", "toxicidade_hepatica", "Toxicidade hepatica"),
    AdverseEffectCategory("renal_hepatic", "monitoramento_renal", "Monitoramento renal"),
    AdverseEffectCategory("renal_hepatic", "monitoramento_hepatico", "Monitoramento hepatico"),
    AdverseEffectCategory("red_flags", "procurar_atendimento", "Procurar atendimento"),
    AdverseEffectCategory("red_flags", "reacao_alergica", "Reacao alergica"),
    AdverseEffectCategory("red_flags", "falta_de_ar", "Falta de ar"),
    AdverseEffectCategory("red_flags", "inchaco_importante", "Inchaco importante"),
    AdverseEffectCategory("red_flags", "desmaio", "Desmaio"),
    AdverseEffectCategory("red_flags", "sangramento_importante", "Sangramento importante"),
    AdverseEffectCategory(
        "red_flags", "dor_intensa_persistente", "Dor intensa/persistente"
    ),
)

ENTRY_BY_CODE = {entry.code: entry for entry in ADVERSE_EFFECT_TAXONOMY}
ENTRY_BY_CATEGORY = {
    category: [entry for entry in ADVERSE_EFFECT_TAXONOMY if entry.category == category]
    for category in {entry.category for entry in ADVERSE_EFFECT_TAXONOMY}
}

ALIASES = {
    "sonolencia": "sonolencia",
    "sono": "sonolencia",
    "sedacao": "sedacao",
    "sedativo": "sedacao",
    "insomnia": "insonia",
    "insonia": "insonia",
    "tontura": "tontura",
    "vertigem": "vertigem",
    "confusao": "confusao",
    "fadiga": "fadiga",
    "alteracao de atencao": "alteracao_atencao_reflexos",
    "reflexos": "alteracao_atencao_reflexos",
    "dirigir": "dirigir",
    "direcao": "dirigir",
    "operar maquinas": "operar_maquinas",
    "maquinas": "operar_maquinas",
    "trabalho em altura": "trabalho_em_altura",
    "atividade de risco": "atividade_de_risco",
    "risco de queda": "risco_de_queda",
    "quedas": "risco_de_queda",
    "humor": "alteracao_humor",
    "ansiedade": "ansiedade",
    "irritabilidade": "irritabilidade",
    "agitacao": "agitacao",
    "risco serotoninergico": "risco_serotoninergico",
    "apetite": "alteracao_apetite",
    "ganho de peso": "ganho_peso",
    "perda de peso": "perda_peso",
    "glicemia": "alteracao_glicemica",
    "libido": "baixa_libido",
    "disfuncao sexual": "disfuncao_sexual",
    "alteracao ejaculatoria": "alteracao_ejaculatoria",
    "ejaculacao": "alteracao_ejaculatoria",
    "contracepcao": "contracepcao",
    "gestacao": "gestacao_lactacao",
    "lactacao": "gestacao_lactacao",
    "dor de cabeca": "dor_cabeca",
    "cefaleia": "dor_cabeca",
    "tremor": "tremor",
    "convulsao": "convulsao",
    "parestesia": "parestesia",
    "hipotermia": "hipotermia",
    "hipertermia": "hipertermia",
    "sudorese": "sudorese",
    "calafrios": "calafrios",
    "hipotensao": "hipotensao",
    "queda de pressao": "hipotensao",
    "hipotensao ortostatica": "hipotensao_ortostatica",
    "pressao ao levantar": "hipotensao_ortostatica",
    "palpitacao": "palpitacao",
    "arritmia": "arritmia",
    "sincope": "sincope_desmaio",
    "desmaio": "desmaio",
    "nausea": "nausea",
    "vomito": "vomito",
    "diarreia": "diarreia",
    "constipacao": "constipacao",
    "dor abdominal": "dor_abdominal",
    "sangramento gastrointestinal": "sangramento_gastrointestinal",
    "renal": "cautela_renal",
    "hepatica": "cautela_hepatica",
    "hepatotoxicidade": "toxicidade_hepatica",
    "toxicidade renal": "toxicidade_renal",
    "monitoramento renal": "monitoramento_renal",
    "monitoramento hepatico": "monitoramento_hepatico",
    "procurar atendimento": "procurar_atendimento",
    "reacao alergica": "reacao_alergica",
    "falta de ar": "falta_de_ar",
    "inchaco": "inchaco_importante",
    "sangramento importante": "sangramento_importante",
    "dor intensa": "dor_intensa_persistente",
}


def taxonomy_snapshot() -> list[dict]:
    return [
        {"category": item.category, "code": item.code, "label": item.label}
        for item in ADVERSE_EFFECT_TAXONOMY
    ]


def is_supported_code(code: str) -> bool:
    return code in ENTRY_BY_CODE


def category_for_code(code: str) -> str | None:
    entry = ENTRY_BY_CODE.get(code)
    return entry.category if entry else None


def normalize_effect_code(value: str) -> str | None:
    raw = value.strip()
    if raw in ENTRY_BY_CODE:
        return raw
    normalized = normalize_text(raw).replace("_", " ")
    if normalized in ENTRY_BY_CODE:
        return normalized
    alias = ALIASES.get(normalized)
    if alias in ENTRY_BY_CODE:
        return alias
    return None


def normalize_effect_list(values: list[str] | None) -> list[str]:
    normalized: list[str] = []
    seen: set[str] = set()
    for value in values or []:
        code = normalize_effect_code(str(value))
        if not code or code in seen:
            continue
        seen.add(code)
        normalized.append(code)
    return normalized


def label_for_effect(code: str) -> str:
    entry = ENTRY_BY_CODE.get(code)
    return entry.label if entry else code
