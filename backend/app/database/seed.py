from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.database.models import (
    ActiveIngredientModel,
    ClinicalVocabularyModel,
    DrugProductModel,
    MedicationKnowledgeSourceModel,
    MedicationModel,
    PatientIdentifierModel,
    PatientModel,
    UserModel,
)
from app.domain.user import UserRole
from app.services.clinical_profile import normalize_patient_payload
from app.services.controlled_vocabulary import VOCABULARY
from app.services.normalizer import normalize_text
from app.services.patient_identifier_service import hash_identifier, mask_identifier

BULARIO_URL = "https://consultas.anvisa.gov.br/#/bulario/"
DCB_URL = "https://www.gov.br/anvisa/pt-br/assuntos/farmacopeia/dcb"


def seed_demo_data(db: Session) -> None:
    ingredients = _seed_active_ingredients(db)
    _seed_drug_products(db, ingredients)
    _seed_knowledge_sources(db, ingredients)
    _seed_clinical_vocabulary(db)
    _seed_medications(db, ingredients)
    _seed_patients(db)
    _seed_patient_identifiers(db)
    _normalize_existing_patients(db)
    _link_existing_medications(db, ingredients)
    _seed_users(db)
    db.commit()


def _seed_active_ingredients(db: Session) -> dict[str, ActiveIngredientModel]:
    specs = [
        {
            "dcb_name": "dipirona",
            "synonyms": ["metamizol", "dipirona sodica", "dipirona monoidratada"],
            "therapeutic_classes": ["analgesico", "antitermico"],
            "common_brands": ["Novalgina", "Anador", "Dorflex", "Neosaldina", "Lisador"],
            "jurisdiction": "BR",
            "source": "manual_curated",
            "validation_status": "curated",
        },
        {
            "dcb_name": "ibuprofeno",
            "synonyms": ["ibuprofeno arginina"],
            "therapeutic_classes": ["anti-inflamatorio nao esteroidal"],
            "common_brands": ["Ibuvida", "Ibuvvida"],
            "jurisdiction": "BR",
            "source": "manual_curated",
            "validation_status": "curated",
        },
        {
            "dcb_name": "nimesulida",
            "synonyms": [],
            "therapeutic_classes": ["anti-inflamatorio nao esteroidal"],
            "common_brands": ["Nimesulida Demo"],
            "jurisdiction": "BR",
            "source": "manual_curated",
            "validation_status": "curated",
        },
        {
            "dcb_name": "paracetamol",
            "synonyms": ["acetaminofeno"],
            "therapeutic_classes": ["analgesico", "antitermico"],
            "common_brands": ["Paracetamol Demo"],
            "jurisdiction": "BR",
            "source": "demo_seed",
            "validation_status": "demo",
        },
        {
            "dcb_name": "rifampicina",
            "synonyms": ["rifampin"],
            "therapeutic_classes": ["antimicrobiano rifamicina"],
            "common_brands": ["Rifampicina Demo"],
            "jurisdiction": "BR",
            "source": "manual_curated",
            "validation_status": "demo",
        },
        {
            "dcb_name": "rifabutina",
            "synonyms": [],
            "therapeutic_classes": ["antimicrobiano rifamicina"],
            "common_brands": ["Rifabutina Demo"],
            "jurisdiction": "BR",
            "source": "manual_curated",
            "validation_status": "demo",
        },
    ]
    ingredients: dict[str, ActiveIngredientModel] = {}
    for spec in specs:
        normalized_name = normalize_text(spec["dcb_name"])
        ingredient = db.scalar(
            select(ActiveIngredientModel).where(
                ActiveIngredientModel.normalized_name == normalized_name
            )
        )
        if ingredient is None:
            ingredient = ActiveIngredientModel(
                dcb_name=spec["dcb_name"],
                normalized_name=normalized_name,
                synonyms=spec["synonyms"],
                therapeutic_classes=spec["therapeutic_classes"],
                common_brands=spec["common_brands"],
                jurisdiction=spec["jurisdiction"],
                source=spec["source"],
                validation_status=spec["validation_status"],
            )
            db.add(ingredient)
            db.flush()
        else:
            ingredient.synonyms = spec["synonyms"]
            ingredient.therapeutic_classes = spec["therapeutic_classes"]
            ingredient.common_brands = spec["common_brands"]
            ingredient.jurisdiction = spec["jurisdiction"]
            ingredient.source = spec["source"]
            ingredient.validation_status = spec["validation_status"]
        ingredients[normalized_name] = ingredient
    return ingredients


def _seed_drug_products(
    db: Session,
    ingredients: dict[str, ActiveIngredientModel],
) -> None:
    specs = [
        ("dipirona", "Novalgina", "Sanofi Demo", "500 mg/mL", "gotas", ["oral"]),
        ("dipirona", "Anador", "Demo", "500 mg", "comprimido", ["oral"]),
        ("dipirona", "Dorflex", "Demo", "demonstrativo", "comprimido", ["oral"]),
        ("dipirona", "Neosaldina", "Demo", "demonstrativo", "comprimido", ["oral"]),
        ("dipirona", "Lisador", "Demo", "demonstrativo", "comprimido", ["oral"]),
        ("ibuprofeno", "Ibuvvida", "Demo", "400 mg", "comprimido", ["oral"]),
        ("nimesulida", "Nimesulida Demo", "Demo", "100 mg", "comprimido", ["oral"]),
    ]
    for active_name, commercial_name, manufacturer, concentration, form, routes in specs:
        ingredient = ingredients[normalize_text(active_name)]
        existing = db.scalar(
            select(DrugProductModel).where(
                DrugProductModel.active_ingredient_id == ingredient.id,
                DrugProductModel.commercial_name == commercial_name,
            )
        )
        if existing is None:
            db.add(
                DrugProductModel(
                    active_ingredient_id=ingredient.id,
                    commercial_name=commercial_name,
                    manufacturer=manufacturer,
                    concentration=concentration,
                    pharmaceutical_form=form,
                    allowed_routes=routes,
                    bula_url=BULARIO_URL,
                    source="demo_seed",
                    validation_status="demo",
                )
            )


def _seed_knowledge_sources(
    db: Session,
    ingredients: dict[str, ActiveIngredientModel],
) -> None:
    specs = [
        (
            "dipirona",
            "DCB - Denominacoes Comuns Brasileiras",
            "dcb",
            "BR",
            DCB_URL,
            ["nomenclatura", "principio ativo"],
            "curated",
            "curated",
        ),
        (
            "dipirona",
            "Anvisa - Bulario Eletronico",
            "anvisa_bulario",
            "BR",
            BULARIO_URL,
            ["bula", "contraindicacoes", "advertencias"],
            "pending_review",
            "pending_review",
        ),
        (
            "ibuprofeno",
            "DCB - Denominacoes Comuns Brasileiras",
            "dcb",
            "BR",
            DCB_URL,
            ["nomenclatura", "principio ativo"],
            "curated",
            "curated",
        ),
        (
            "ibuprofeno",
            "Anvisa - Bulario Eletronico",
            "anvisa_bulario",
            "BR",
            BULARIO_URL,
            ["bula", "advertencias"],
            "pending_review",
            "pending_review",
        ),
        (
            "nimesulida",
            "Base interna demonstrativa",
            "manual_curated",
            "BR",
            None,
            ["cautela renal", "cautela hepatica", "cautela gastrointestinal"],
            "demo",
            "demo",
        ),
        (
            "dipirona",
            "Referencia internacional demonstrativa",
            "external_reference",
            "US",
            None,
            ["diferenca regulatoria"],
            "demo",
            "demo",
        ),
    ]
    for (
        active_name,
        source_name,
        source_type,
        jurisdiction,
        source_url,
        sections,
        confidence,
        validation_status,
    ) in specs:
        ingredient = ingredients[normalize_text(active_name)]
        existing = db.scalar(
            select(MedicationKnowledgeSourceModel).where(
                MedicationKnowledgeSourceModel.active_ingredient_id == ingredient.id,
                MedicationKnowledgeSourceModel.source_name == source_name,
                MedicationKnowledgeSourceModel.source_type == source_type,
                MedicationKnowledgeSourceModel.jurisdiction == jurisdiction,
            )
        )
        if existing is None:
            db.add(
                MedicationKnowledgeSourceModel(
                    active_ingredient_id=ingredient.id,
                    source_name=source_name,
                    source_type=source_type,
                    jurisdiction=jurisdiction,
                    source_url=source_url,
                    retrieved_at=datetime.now(UTC),
                    version="v0.5.0-demo",
                    evidence_sections=sections,
                    confidence_level=confidence,
                    validation_status=validation_status,
                    reviewer="Prescripta demo",
                )
            )


def _seed_clinical_vocabulary(db: Session) -> None:
    for entry in VOCABULARY:
        existing = db.scalar(
            select(ClinicalVocabularyModel).where(
                ClinicalVocabularyModel.category == entry.category,
                ClinicalVocabularyModel.code == entry.code,
            )
        )
        if existing is None:
            db.add(
                ClinicalVocabularyModel(
                    category=entry.category,
                    code=entry.code,
                    label=entry.label,
                    normalized_label=entry.normalized_label,
                    severity_weight=entry.severity_weight,
                    description=entry.description,
                    is_active=True,
                )
            )
        else:
            existing.label = entry.label
            existing.normalized_label = entry.normalized_label
            existing.severity_weight = entry.severity_weight
            existing.description = entry.description
            existing.is_active = True


def _seed_medications(
    db: Session,
    ingredients: dict[str, ActiveIngredientModel],
) -> None:
    has_medications = db.scalar(select(MedicationModel.id).limit(1))
    if has_medications:
        return

    db.add_all(
        [
            MedicationModel(
                active_ingredient_id=ingredients["dipirona"].id,
                brand_name="Novalgina Demo",
                active_ingredient="dipirona",
                commercial_aliases=["Novalgina", "Anador", "Dorflex", "Neosaldina", "Lisador"],
                therapeutic_class="analgesico antitermico",
                therapeutic_classes=["analgesico", "antitermico"],
                source_jurisdiction="BR",
                evidence_source_type="manual_curated",
                validation_status="curated",
                concentration="500 mg/mL",
                pharmaceutical_form="gotas",
                evidence_source_url=BULARIO_URL,
                max_daily_dose_mg=4000,
                max_duration_days=5,
                max_cumulative_dose_mg=12000,
                continuous_use=False,
                monitoring_required=False,
                condition_specific_limits={"hepatico": 2000},
                allowed_routes=["oral"],
                contraindications=["alergia a dipirona"],
                hepatic_caution=True,
                elderly_caution=True,
                mechanism_of_action="Inibicao demonstrativa de vias de dor/febre.",
                absorption_notes="Absorcao oral demonstrativa.",
                distribution_notes="Distribuicao sistemica demonstrativa.",
                metabolism_organs=["hepatico"],
                elimination_organs=["renal"],
                renal_elimination_level="moderado",
                hepatic_metabolism_level="moderado",
                pharmacodynamic_notes="Analgesia e antitermia demonstrativas.",
                pharmacokinetic_notes="Metabolismo hepatico e eliminacao renal demonstrativos.",
                clinical_interpretation="Revisar funcao hepatica/renal em uso prolongado.",
                organs_involved=["hepatico", "renal"],
                relevant_adverse_effects=["reacao alergica demonstrativa"],
                structured_contraindications=["alergia"],
                therapeutic_action="analgesia e antitermico",
                alternative_group="analgesia",
                related_medications=["paracetamol", "ibuprofeno"],
                knowledge_source="DCB/Anvisa/manual_curated demonstrativo v0.5.0",
                notes="Seed educacional centrado em principio ativo e aliases comerciais.",
            ),
            MedicationModel(
                active_ingredient_id=ingredients["ibuprofeno"].id,
                brand_name="Ibuvida",
                active_ingredient="ibuprofeno",
                commercial_aliases=["Ibuvida", "Ibuvvida"],
                therapeutic_class="anti-inflamatorio nao esteroidal",
                therapeutic_classes=["anti-inflamatorio nao esteroidal"],
                source_jurisdiction="BR",
                evidence_source_type="manual_curated",
                validation_status="curated",
                concentration="400 mg",
                pharmaceutical_form="comprimido",
                evidence_source_url=BULARIO_URL,
                max_daily_dose_mg=2400,
                max_duration_days=5,
                max_cumulative_dose_mg=7200,
                continuous_use=False,
                monitoring_required=True,
                monitoring_notes=(
                    "Revisar funcao renal e sinais gastrointestinais se uso prolongado."
                ),
                condition_specific_limits={"renal": 1200, "gastrointestinal": 1200},
                allowed_routes=["oral"],
                contraindications=["ulcera ativa", "doenca renal grave"],
                renal_caution=True,
                gastrointestinal_caution=True,
                elderly_caution=True,
                mechanism_of_action="Inibicao de COX demonstrativa.",
                absorption_notes="Absorcao oral demonstrativa.",
                distribution_notes="Ligacao proteica demonstrativa.",
                metabolism_organs=["hepatico"],
                elimination_organs=["renal"],
                renal_elimination_level="moderado",
                hepatic_metabolism_level="moderado",
                cyp_interactions=["cyp2c9_a_revisar"],
                pharmacodynamic_notes="Efeito anti-inflamatorio e analgesico demonstrativo.",
                pharmacokinetic_notes="Metabolismo hepatico e eliminacao renal demonstrativos.",
                clinical_interpretation="Cautela renal/gastrointestinal em perfis de risco.",
                organs_involved=["renal", "gastrointestinal"],
                relevant_adverse_effects=["sangramento gastrointestinal", "gastrite"],
                structured_contraindications=["renal", "gastrointestinal"],
                therapeutic_action="analgesia e anti-inflamatorio",
                alternative_group="analgesia anti-inflamatoria",
                related_medications=["paracetamol", "nimesulida"],
                knowledge_source="DCB/Anvisa/manual_curated demonstrativo v0.5.0",
                notes="Medicamento demonstrativo inspirado em regra comum de dose maxima.",
            ),
            MedicationModel(
                active_ingredient_id=ingredients["nimesulida"].id,
                brand_name="Nimesulida Demo",
                active_ingredient="nimesulida",
                commercial_aliases=["Nimesulida Demo"],
                therapeutic_class="anti-inflamatorio nao esteroidal",
                therapeutic_classes=["anti-inflamatorio nao esteroidal"],
                source_jurisdiction="BR",
                evidence_source_type="manual_curated",
                validation_status="demo",
                concentration="100 mg",
                pharmaceutical_form="comprimido",
                max_daily_dose_mg=200,
                max_duration_days=5,
                max_cumulative_dose_mg=1000,
                continuous_use=False,
                monitoring_required=True,
                monitoring_notes="Revisar funcao hepatica antes de uso prolongado.",
                condition_specific_limits={"hepatico": 100},
                allowed_routes=["oral"],
                contraindications=["doenca hepatica"],
                renal_caution=True,
                hepatic_caution=True,
                gastrointestinal_caution=True,
                elderly_caution=True,
                mechanism_of_action="Acao anti-inflamatoria demonstrativa.",
                metabolism_organs=["hepatico"],
                elimination_organs=["renal"],
                renal_elimination_level="moderado",
                hepatic_metabolism_level="alto",
                pharmacodynamic_notes="Efeito anti-inflamatorio demonstrativo.",
                pharmacokinetic_notes="Metabolismo hepatico relevante demonstrativo.",
                clinical_interpretation="Cautela hepatica e revisao profissional.",
                organs_involved=["renal", "hepatico", "gastrointestinal"],
                relevant_adverse_effects=["hepatotoxicidade demonstrativa", "dispepsia"],
                structured_contraindications=["hepatico"],
                therapeutic_action="analgesia e anti-inflamatorio",
                alternative_group="analgesia anti-inflamatoria",
                related_medications=["ibuprofeno", "paracetamol"],
                knowledge_source="Base interna demonstrativa v0.5.0",
                notes="Seed educacional para cautela renal, hepatica e gastrointestinal.",
            ),
            MedicationModel(
                active_ingredient_id=ingredients["paracetamol"].id,
                brand_name="Paracetamol Demo",
                active_ingredient="paracetamol",
                commercial_aliases=["Paracetamol Demo"],
                therapeutic_class="analgesico antitermico",
                therapeutic_classes=["analgesico", "antitermico"],
                source_jurisdiction="BR",
                evidence_source_type="demo_seed",
                validation_status="demo",
                max_daily_dose_mg=3000,
                max_duration_days=7,
                max_cumulative_dose_mg=12000,
                continuous_use=False,
                monitoring_required=True,
                monitoring_notes="Revisar funcao hepatica quando houver risco ou uso prolongado.",
                condition_specific_limits={"hepatico": 1500},
                allowed_routes=["oral"],
                contraindications=["doenca hepatica grave"],
                hepatic_caution=True,
                mechanism_of_action="Analgesia central demonstrativa.",
                metabolism_organs=["hepatico"],
                elimination_organs=["renal"],
                renal_elimination_level="baixo",
                hepatic_metabolism_level="alto",
                pharmacodynamic_notes="Analgesia e antitermia demonstrativas.",
                pharmacokinetic_notes="Metabolismo hepatico relevante demonstrativo.",
                clinical_interpretation="Cautela hepatica em dose acumulada.",
                organs_involved=["hepatico"],
                relevant_adverse_effects=["hepatotoxicidade demonstrativa"],
                structured_contraindications=["hepatico"],
                therapeutic_action="analgesia",
                alternative_group="analgesia anti-inflamatoria",
                related_medications=["ibuprofeno", "nimesulida"],
                knowledge_source="Base interna demonstrativa v0.5.0",
                notes="Seed educacional para alternativa avaliada.",
            ),
            MedicationModel(
                brand_name="Clarimicina",
                active_ingredient="claritromicina",
                therapeutic_class="macrolideo",
                max_daily_dose_mg=1000,
                allowed_routes=["oral", "intravenosa"],
                contraindications=["arritmia grave"],
                notes="Seed educacional para testar interacoes.",
            ),
            MedicationModel(
                brand_name="Metfor",
                active_ingredient="metformina",
                therapeutic_class="antidiabetico",
                max_daily_dose_mg=2550,
                allowed_routes=["oral"],
                contraindications=["doenca renal grave", "acidose metabolica"],
                notes="Seed educacional para contraindicacao por comorbidade.",
            ),
            MedicationModel(
                brand_name="Sertral",
                active_ingredient="sertralina",
                therapeutic_class="inibidor seletivo da recaptacao de serotonina",
                max_daily_dose_mg=200,
                max_duration_days=365,
                max_cumulative_dose_mg=73000,
                continuous_use=True,
                monitoring_required=True,
                monitoring_notes=(
                    "Monitorar resposta, eventos adversos e associacoes serotoninergicas."
                ),
                allowed_routes=["oral"],
                contraindications=["uso de imao"],
                mechanism_of_action="Inibicao seletiva da recaptacao de serotonina demonstrativa.",
                hepatic_metabolism_level="moderado",
                neuropsychiatric_cautions=["risco_serotoninergico", "uso_imao"],
                notes="Seed educacional para interacoes demonstrativas.",
            ),
            MedicationModel(
                active_ingredient_id=ingredients["rifampicina"].id,
                brand_name="Rifampicina Demo",
                active_ingredient="rifampicina",
                commercial_aliases=["Rifampicina Demo"],
                therapeutic_class="antimicrobiano rifamicina",
                therapeutic_classes=["antimicrobiano rifamicina"],
                source_jurisdiction="BR",
                evidence_source_type="manual_curated",
                validation_status="demo",
                max_daily_dose_mg=600,
                max_duration_days=180,
                max_cumulative_dose_mg=108000,
                monitoring_required=True,
                monitoring_notes="Regra demonstrativa: revisar interacoes e contracepcao hormonal.",
                allowed_routes=["oral"],
                contraindications=[],
                hepatic_caution=True,
                mechanism_of_action="Rifamicina com inducao enzimatica demonstrativa.",
                metabolism_organs=["hepatico"],
                elimination_organs=["biliar fecal"],
                hepatic_metabolism_level="alto",
                cyp_interactions=["inducao_enzimatica_a_revisar"],
                reproductive_cautions=["uso_anticoncepcional_hormonal"],
                knowledge_source="Base interna demonstrativa v0.6.0",
                notes="Nao generalizar para todos os antibioticos.",
            ),
            MedicationModel(
                active_ingredient_id=ingredients["rifabutina"].id,
                brand_name="Rifabutina Demo",
                active_ingredient="rifabutina",
                commercial_aliases=["Rifabutina Demo"],
                therapeutic_class="antimicrobiano rifamicina",
                therapeutic_classes=["antimicrobiano rifamicina"],
                source_jurisdiction="BR",
                evidence_source_type="manual_curated",
                validation_status="demo",
                max_daily_dose_mg=300,
                max_duration_days=180,
                max_cumulative_dose_mg=54000,
                monitoring_required=True,
                monitoring_notes="Regra demonstrativa: revisar interacoes e contracepcao hormonal.",
                allowed_routes=["oral"],
                contraindications=[],
                hepatic_caution=True,
                mechanism_of_action="Rifamicina com inducao enzimatica demonstrativa.",
                metabolism_organs=["hepatico"],
                elimination_organs=["biliar fecal"],
                hepatic_metabolism_level="alto",
                cyp_interactions=["inducao_enzimatica_a_revisar"],
                reproductive_cautions=["uso_anticoncepcional_hormonal"],
                knowledge_source="Base interna demonstrativa v0.6.0",
                notes="Nao generalizar para todos os antibioticos.",
            ),
        ]
    )


def _seed_patients(db: Session) -> None:
    has_patients = db.scalar(select(PatientModel.id).limit(1))
    if has_patients:
        return

    db.add_all(
        [
            PatientModel(
                name="Ana Exemplo",
                age=34,
                weight_kg=68,
                height_cm=168,
                allergies=["dipirona"],
                comorbidities=["asma"],
                current_medications=["losartana"],
                mental_health_factors=[],
                reproductive_gynecologic_factors=["uso_anticoncepcional_hormonal"],
            ),
            PatientModel(
                name="Carlos Demonstracao",
                age=72,
                weight_kg=81,
                height_cm=174,
                allergies=["ibuprofeno"],
                comorbidities=["doenca renal grave"],
                current_medications=[
                    "varfarina",
                    "sinvastatina",
                    "omeprazol",
                    "hidroclorotiazida",
                    "metoprolol",
                ],
                renal_condition="funcao_renal_a_revisar",
                cardiac_condition="risco_cardiovascular_a_revisar",
                gastrointestinal_history="historico_gastrointestinal_a_revisar",
                hypertension=True,
                diabetes=False,
                mental_health_factors=["uso_isrs"],
                reproductive_gynecologic_factors=[],
                adverse_reactions=["sangramento gastrointestinal"],
                clinical_notes="Perfil demonstrativo para triagem rapida e cautela renal.",
                clinical_profile_completeness_score=89,
            ),
        ]
    )


def _seed_patient_identifiers(db: Session) -> None:
    if db.scalar(select(PatientIdentifierModel.id).limit(1)):
        return
    patients = list(db.scalars(select(PatientModel).order_by(PatientModel.id)))
    for patient in patients:
        value = f"DEMO-{patient.id:05d}"
        db.add(
            PatientIdentifierModel(
                patient_id=patient.id,
                identifier_type="internal_record_number",
                identifier_value_hash=hash_identifier("internal_record_number", value),
                issuing_system="prescripta_demo",
                display_masked=mask_identifier("internal_record_number", value),
                is_primary=True,
            )
        )


def _normalize_existing_patients(db: Session) -> None:
    for patient in db.scalars(select(PatientModel)):
        values = {
            "allergies": list(patient.allergies or []),
            "comorbidities": list(patient.comorbidities or []),
            "current_medications": list(patient.current_medications or []),
            "renal_condition": patient.renal_condition,
            "hepatic_condition": patient.hepatic_condition,
            "cardiac_condition": patient.cardiac_condition,
            "gastrointestinal_history": patient.gastrointestinal_history,
            "hypertension": patient.hypertension,
            "diabetes": patient.diabetes,
            "pregnancy_or_lactation": patient.pregnancy_or_lactation,
            "adverse_reactions": list(patient.adverse_reactions or []),
            "clinical_notes": patient.clinical_notes,
        }
        normalized = normalize_patient_payload(values)
        for field, value in normalized.items():
            if hasattr(patient, field):
                setattr(patient, field, value)


def _link_existing_medications(
    db: Session,
    ingredients: dict[str, ActiveIngredientModel],
) -> None:
    for medication in db.scalars(select(MedicationModel)):
        ingredient = ingredients.get(normalize_text(medication.active_ingredient))
        if ingredient is None:
            continue
        medication.active_ingredient_id = ingredient.id
        if not medication.commercial_aliases:
            medication.commercial_aliases = [
                medication.brand_name,
                *(ingredient.common_brands or []),
            ]
        if not medication.therapeutic_classes:
            medication.therapeutic_classes = ingredient.therapeutic_classes
        medication.source_jurisdiction = medication.source_jurisdiction or "BR"
        medication.evidence_source_type = medication.evidence_source_type or "demo_seed"
        medication.validation_status = medication.validation_status or ingredient.validation_status


def _seed_users(db: Session) -> None:
    has_users = db.scalar(select(UserModel.id).limit(1))
    if has_users:
        return

    db.add_all(
        [
            UserModel(
                name="Admin Prescripta",
                email="admin@prescripta.local",
                hashed_password=hash_password("Admin@12345"),
                role=UserRole.ADMIN.value,
                is_active=True,
            ),
            UserModel(
                name="Medico Demonstracao",
                email="medico@prescripta.local",
                hashed_password=hash_password("Medico@12345"),
                role=UserRole.MEDICO.value,
                is_active=True,
            ),
            UserModel(
                name="Enfermagem Demonstracao",
                email="enfermagem@prescripta.local",
                hashed_password=hash_password("Enfermagem@12345"),
                role=UserRole.ENFERMAGEM.value,
                is_active=True,
            ),
            UserModel(
                name="Auditor Demonstracao",
                email="auditor@prescripta.local",
                hashed_password=hash_password("Auditor@12345"),
                role=UserRole.AUDITOR.value,
                is_active=True,
            ),
        ]
    )
