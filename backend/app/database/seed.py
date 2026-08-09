from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.database.models import (
    ActiveIngredientModel,
    ClinicalVocabularyModel,
    DrugProductModel,
    InstitutionalClinicalProtocolModel,
    InstitutionalClinicalProtocolVersionModel,
    MedicationCounselingSummaryModel,
    MedicationKnowledgeSourceModel,
    MedicationModel,
    PatientAccessGrantModel,
    PatientClinicalTimelineEventModel,
    PatientFunctionalProfileModel,
    PatientIdentifierModel,
    PatientModel,
    ResearchStudyModel,
    SpecialtyModel,
    UserModel,
)
from app.domain.user import ROLE_PROFESSION, UserRole
from app.schemas.clinical_protocol_schema import (
    InstitutionalClinicalProtocolCreate,
    InstitutionalClinicalProtocolVersionCreate,
    ProtocolVersionReviewRequest,
)
from app.schemas.pharmacy_schema import PharmacyInterventionCreate
from app.schemas.research_schema import (
    AnalysisPlanCreate,
    CohortDefinitionCreate,
    CohortReviewRequest,
    CohortRunRequest,
    ConceptSetCreate,
    ConceptSetReviewRequest,
    OutcomeDefinitionCreate,
    OutcomeReviewRequest,
    ResearchReviewRequest,
    ResearchStudyCreate,
    StudyProtocolVersionCreate,
)
from app.services.capability_policy import allowed_capabilities
from app.services.clinical_profile import normalize_patient_payload
from app.services.controlled_vocabulary import VOCABULARY
from app.services.data_quality_service import DataQualityService
from app.services.institutional_protocol_service import (
    InstitutionalClinicalProtocolService,
)
from app.services.normalizer import normalize_text
from app.services.patient_identifier_service import hash_identifier, mask_identifier
from app.services.pharmacy_workflow_service import PharmacyWorkflowService
from app.services.research_analysis_service import ResearchAnalysisService
from app.services.research_service import ResearchService

BULARIO_URL = "https://consultas.anvisa.gov.br/#/bulario/"
DCB_URL = "https://www.gov.br/anvisa/pt-br/assuntos/farmacopeia/dcb"


def seed_demo_data(db: Session) -> None:
    ingredients = _seed_active_ingredients(db)
    _seed_drug_products(db, ingredients)
    _seed_knowledge_sources(db, ingredients)
    _seed_clinical_vocabulary(db)
    _seed_medications(db, ingredients)
    _seed_v084_medications(db, ingredients)
    db.flush()
    _seed_patients(db)
    db.flush()
    _seed_functional_profiles(db)
    db.flush()
    _seed_patient_identifiers(db)
    _normalize_existing_patients(db)
    _link_existing_medications(db, ingredients)
    db.flush()
    _seed_counseling_summaries(db)
    db.flush()
    _seed_specialties(db)
    db.flush()
    _seed_users(db)
    db.flush()
    _seed_demo_patient_access(db)
    db.flush()
    _seed_v088_workflows(db)
    db.commit()


def _v083_active_ingredient_specs() -> list[dict]:
    names_by_class = {
        "analgesico_antitermico": ["acido acetilsalicilico", "codeina", "tramadol"],
        "aine": ["diclofenaco", "naproxeno", "cetoprofeno", "meloxicam", "celecoxibe"],
        "antibiotico": [
            "amoxicilina",
            "azitromicina",
            "ceftriaxona",
            "cefalexina",
            "ciprofloxacino",
            "clindamicina",
            "doxiciclina",
            "metronidazol",
            "sulfametoxazol trimetoprima",
            "levofloxacino",
        ],
        "anti_hipertensivo": [
            "losartana",
            "enalapril",
            "captopril",
            "amlodipino",
            "hidroclorotiazida",
            "furosemida",
            "atenolol",
            "carvedilol",
            "espironolactona",
        ],
        "antidiabetico": ["metformina", "glibenclamida", "insulina regular", "insulina nph"],
        "anticoagulante_antiagregante": ["varfarina", "heparina", "enoxaparina", "clopidogrel"],
        "psicotropico": [
            "fluoxetina",
            "escitalopram",
            "venlafaxina",
            "amitriptilina",
            "bupropiona",
            "diazepam",
            "clonazepam",
            "risperidona",
            "quetiapina",
            "haloperidol",
            "valproato de sodio",
            "carbamazepina",
            "lamotrigina",
            "fenitoina",
        ],
        "respiratorio": ["salbutamol", "budesonida", "prednisona", "dexametasona"],
        "gastrointestinal": ["omeprazol", "pantoprazol", "metoclopramida", "ondansetrona"],
    }
    specs: list[dict] = []
    for therapeutic_class, names in names_by_class.items():
        for name in names:
            specs.append(
                {
                    "dcb_name": name,
                    "synonyms": [],
                    "therapeutic_classes": [therapeutic_class],
                    "common_brands": [],
                    "jurisdiction": "BR",
                    "source": "anvisa_dcb_reference_pending",
                    "validation_status": "pending_review",
                }
            )
    return specs


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
        {
            "dcb_name": "tansulosina",
            "synonyms": ["cloridrato de tansulosina"],
            "therapeutic_classes": ["alfa bloqueador urologico"],
            "common_brands": ["Tansulosina Demo"],
            "jurisdiction": "BR",
            "source": "demo_seed",
            "validation_status": "demo",
        },
        {
            "dcb_name": "sertralina",
            "synonyms": ["cloridrato de sertralina"],
            "therapeutic_classes": ["inibidor seletivo da recaptacao de serotonina"],
            "common_brands": ["Sertral"],
            "jurisdiction": "BR",
            "source": "demo_seed",
            "validation_status": "demo",
        },
        {
            "dcb_name": "litio",
            "synonyms": ["carbonato de litio"],
            "therapeutic_classes": ["estabilizador de humor"],
            "common_brands": ["Litio Demo"],
            "jurisdiction": "BR",
            "source": "demo_seed",
            "validation_status": "demo",
        },
    ]
    specs.extend(_v083_active_ingredient_specs())
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
        ("tansulosina", "Tansulosina Demo", "Demo", "0,4 mg", "capsula", ["oral"]),
        ("sertralina", "Sertral", "Demo", "50 mg", "comprimido", ["oral"]),
        ("litio", "Litio Demo", "Demo", "300 mg", "comprimido", ["oral"]),
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
        (
            "tansulosina",
            "Base interna demonstrativa - tansulosina",
            "rag_demo",
            "BR",
            None,
            ["bula resumida", "eventos adversos", "orientacao pratica"],
            "demo",
            "pending_review",
        ),
        (
            "sertralina",
            "Base interna demonstrativa - sertralina",
            "rag_demo",
            "BR",
            None,
            ["bula resumida", "eventos adversos", "orientacao pratica"],
            "demo",
            "pending_review",
        ),
        (
            "litio",
            "Base interna demonstrativa - litio",
            "rag_demo",
            "BR",
            None,
            ["bula resumida", "monitoramento", "sinais de alerta"],
            "demo",
            "pending_review",
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
        _seed_v07_medications(db, ingredients)
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
    db.flush()
    _seed_v07_medications(db, ingredients)


def _seed_v07_medications(
    db: Session,
    ingredients: dict[str, ActiveIngredientModel],
) -> None:
    specs = [
        MedicationModel(
            active_ingredient_id=ingredients["tansulosina"].id,
            brand_name="Tansulosina Demo",
            active_ingredient="tansulosina",
            commercial_aliases=["Tansulosina Demo"],
            therapeutic_class="alfa bloqueador urologico",
            therapeutic_classes=["alfa bloqueador urologico"],
            source_jurisdiction="BR",
            evidence_source_type="rag_demo",
            validation_status="demo",
            concentration="0,4 mg",
            pharmaceutical_form="capsula",
            max_daily_dose_mg=0.8,
            max_duration_days=365,
            continuous_use=True,
            monitoring_required=True,
            monitoring_notes=(
                "Demo: orientar tontura, hipotensao ortostatica e atividades de risco."
            ),
            condition_specific_limits={},
            allowed_routes=["oral"],
            contraindications=[],
            cardiac_caution=True,
            elderly_caution=True,
            mechanism_of_action="Antagonismo alfa-1 demonstrativo.",
            pharmacodynamic_notes="Pode reduzir pressao ao levantar em demo.",
            clinical_interpretation="Revisar risco de queda, direcao e maquinas.",
            relevant_adverse_effects=[
                "tontura",
                "hipotensao_ortostatica",
                "alteracao_ejaculatoria",
            ],
            reproductive_cautions=["alteracao_ejaculatoria"],
            organs_involved=["cardiovascular", "urologico"],
            therapeutic_action="sintomas urinarios",
            alternative_group="urologia",
            knowledge_source="Base interna demonstrativa v0.7.0",
            notes="Seed demo para orientacao pratica; nao substitui bula.",
        ),
        MedicationModel(
            active_ingredient_id=ingredients["litio"].id,
            brand_name="Litio Demo",
            active_ingredient="litio",
            commercial_aliases=["Litio Demo", "Carbonato de litio demo"],
            therapeutic_class="estabilizador de humor",
            therapeutic_classes=["estabilizador de humor"],
            source_jurisdiction="BR",
            evidence_source_type="rag_demo",
            validation_status="demo",
            concentration="300 mg",
            pharmaceutical_form="comprimido",
            max_daily_dose_mg=1800,
            max_duration_days=365,
            continuous_use=True,
            monitoring_required=True,
            monitoring_notes="Demo: monitoramento renal e sinais neurologicos/autonomicos.",
            condition_specific_limits={"renal": 900},
            allowed_routes=["oral"],
            contraindications=["doenca renal grave"],
            renal_caution=True,
            elderly_caution=True,
            renal_elimination_level="alto",
            relevant_adverse_effects=["tremor", "sudorese", "hipertermia"],
            neuropsychiatric_cautions=["tremor"],
            organs_involved=["renal", "neurologico"],
            therapeutic_action="estabilizacao de humor",
            alternative_group="saude mental",
            knowledge_source="Base interna demonstrativa v0.7.0",
            notes="Seed demo para tremor, temperatura e monitoramento.",
        ),
    ]
    for spec in specs:
        existing = db.scalar(
            select(MedicationModel).where(
                MedicationModel.active_ingredient == spec.active_ingredient,
                MedicationModel.brand_name == spec.brand_name,
            )
        )
        if existing is None:
            db.add(spec)
        else:
            for field in (
                "active_ingredient_id",
                "commercial_aliases",
                "therapeutic_classes",
                "source_jurisdiction",
                "evidence_source_type",
                "validation_status",
                "relevant_adverse_effects",
                "neuropsychiatric_cautions",
                "reproductive_cautions",
                "knowledge_source",
            ):
                setattr(existing, field, getattr(spec, field))


def _seed_v084_medications(db: Session, ingredients: dict[str, ActiveIngredientModel]) -> None:
    common = ["dipirona", "ibuprofeno", "amoxicilina", "losartana", "metformina"]
    psychotropic = [
        "sertralina",
        "fluoxetina",
        "venlafaxina",
        "amitriptilina",
        "bupropiona",
        "diazepam",
        "clonazepam",
        "zolpidem",
        "litio",
        "valproato",
        "carbamazepina",
        "lamotrigina",
        "quetiapina",
        "risperidona",
        "haloperidol",
        "clozapina",
        "metilfenidato",
        "lisdexanfetamina",
    ]
    opioids = ["morfina", "fentanil", "tramadol", "metadona"]
    anesthetics = [
        "lidocaina",
        "bupivacaina",
        "propofol",
        "cetamina",
        "midazolam",
        "rocuronio",
        "succinilcolina",
    ]
    for name in common + psychotropic + opioids + anesthetics:
        normalized = normalize_text(name)
        ingredient = ingredients.get(normalized)
        if ingredient is None:
            ingredient = db.scalar(
                select(ActiveIngredientModel).where(
                    ActiveIngredientModel.normalized_name == normalized
                )
            )
            if ingredient is None:
                ingredient = ActiveIngredientModel(
                    dcb_name=name,
                    normalized_name=normalized,
                    synonyms=[],
                    therapeutic_classes=["demo_pending_review"],
                    common_brands=[],
                    jurisdiction="BR",
                    source="demo_seed",
                    validation_status="pending_review",
                )
                db.add(ingredient)
                db.flush()
            ingredients[normalized] = ingredient
        existing = db.scalar(
            select(MedicationModel).where(MedicationModel.active_ingredient == normalized)
        )
        policy_specialties: list[str] = []
        high_alert = None
        if name in psychotropic:
            policy_specialties = ["psychiatry", "neurology"]
            high_alert = "psychotropic"
        elif name in opioids:
            policy_specialties = ["pain_medicine", "palliative_care", "anesthesiology"]
            high_alert = "opioid_high_potency"
        elif name in anesthetics:
            policy_specialties = ["anesthesiology", "emergency_medicine", "intensive_care"]
            high_alert = "anesthetic_procedural"
        values = {
            "active_ingredient_id": ingredient.id,
            "brand_name": f"{name.title()} Demo",
            "active_ingredient": normalized,
            "commercial_aliases": [],
            "therapeutic_class": "demo pendente de revisão",
            "therapeutic_classes": list(ingredient.therapeutic_classes or []),
            "source_jurisdiction": "BR",
            "evidence_source_type": "demo_seed",
            "validation_status": "pending_review",
            "max_daily_dose_mg": 1000,
            "allowed_routes": ["a_revisar"],
            "contraindications": [],
            "dose_rule_validation_status": "pending_review",
            "dose_calculation_basis": "actual_weight" if name in anesthetics else "fixed",
            "dose_unit": "mg/kg" if name in anesthetics else "mg",
            "recommended_specialty_codes": policy_specialties,
            "requires_institutional_protocol": name in anesthetics,
            "requires_second_review": name in opioids or name in anesthetics,
            "policy_type": "demo_policy",
            "policy_strength": "requires_review" if high_alert else "warning_only",
            "policy_validation_status": "pending_review",
            "high_alert_category": high_alert,
            "psychotropic_class": "pending_classification" if name in psychotropic else None,
            "notes": "Seed educacional; limites e vias exigem curadoria antes de uso.",
        }
        if existing is None:
            db.add(MedicationModel(**values))
        else:
            for field in (
                "recommended_specialty_codes",
                "requires_institutional_protocol",
                "requires_second_review",
                "policy_type",
                "policy_strength",
                "policy_validation_status",
                "high_alert_category",
                "psychotropic_class",
                "dose_rule_validation_status",
            ):
                setattr(existing, field, values[field])


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


def _seed_functional_profiles(db: Session) -> None:
    patient = db.scalar(select(PatientModel).where(PatientModel.name == "Carlos Demonstracao"))
    if patient is None:
        return
    existing = db.scalar(
        select(PatientFunctionalProfileModel).where(
            PatientFunctionalProfileModel.patient_id == patient.id
        )
    )
    if existing is not None:
        return
    db.add(
        PatientFunctionalProfileModel(
            patient_id=patient.id,
            drives_regularly=True,
            professional_driver=False,
            operates_machinery=False,
            works_at_height=False,
            fall_risk_activity=True,
            night_shift=False,
            caregiver_responsibility=False,
            high_attention_activity=True,
            frequent_alcohol_use=None,
            history_of_falls=True,
            low_tolerance_to_sedation_or_dizziness=True,
            source="seed_demo",
            notes="Perfil funcional demonstrativo para v0.7.0.",
            last_reviewed_at=datetime.now(UTC),
        )
    )


def _seed_counseling_summaries(db: Session) -> None:
    specs = [
        {
            "active": "tansulosina",
            "source_id": "kb:medications/tansulosina.md",
            "source_name": "Base interna demonstrativa - tansulosina",
            "main_adverse_effects": [
                "tontura",
                "hipotensao_ortostatica",
                "alteracao_ejaculatoria",
            ],
            "patient_relevant_effects": [
                "tontura",
                "hipotensao_ortostatica",
                "alteracao_ejaculatoria",
            ],
            "activity_warnings": ["dirigir", "operar_maquinas", "trabalho_em_altura"],
            "sleep_effects": ["tontura"],
            "libido_sexual_effects": ["alteracao_ejaculatoria"],
            "neurologic_effects": ["tontura"],
            "blood_pressure_warning": True,
            "driving_warning": True,
            "machine_operation_warning": True,
            "work_at_height_warning": True,
            "fall_risk_warning": True,
            "sedation_attention_warning": True,
            "red_flags": ["desmaio", "reacao_alergica", "procurar_atendimento"],
            "patient_friendly_summary": (
                "Pode causar tontura e queda de pressao ao levantar. Cautela ao dirigir, "
                "operar maquinas ou trabalhar em altura ate saber como reage. Pode causar "
                "alteracoes ejaculatorias."
            ),
            "professional_summary": (
                "Demo v0.7: revisar hipotensao ortostatica, quedas, direcao/maquinas e "
                "efeitos ejaculatorios; resumo pendente de revisao."
            ),
        },
        {
            "active": "sertralina",
            "source_id": "kb:medications/sertralina.md",
            "source_name": "Base interna demonstrativa - sertralina",
            "main_adverse_effects": [
                "insonia",
                "sonolencia",
                "alteracao_apetite",
                "alteracao_humor",
                "baixa_libido",
                "disfuncao_sexual",
                "dor_cabeca",
                "risco_serotoninergico",
            ],
            "patient_relevant_effects": [
                "insonia",
                "sonolencia",
                "alteracao_apetite",
                "baixa_libido",
                "dor_cabeca",
            ],
            "activity_warnings": ["rotina_alta_atencao"],
            "sleep_effects": ["insonia", "sonolencia"],
            "appetite_weight_effects": ["alteracao_apetite"],
            "mood_behavior_effects": ["alteracao_humor", "risco_serotoninergico"],
            "libido_sexual_effects": ["baixa_libido", "disfuncao_sexual"],
            "neurologic_effects": ["dor_cabeca"],
            "headache_warning": True,
            "sedation_attention_warning": True,
            "red_flags": ["agitacao", "procurar_atendimento"],
            "patient_friendly_summary": (
                "Pode alterar sono, apetite, humor, libido/funcao sexual e causar dor de "
                "cabeca. Associacoes serotoninergicas exigem revisao."
            ),
            "professional_summary": (
                "Demo v0.7: orientar sono, apetite, humor, efeitos sexuais, cefaleia e "
                "risco serotoninergico quando combinado."
            ),
        },
        {
            "active": "litio",
            "source_id": "kb:medications/litio.md",
            "source_name": "Base interna demonstrativa - litio",
            "main_adverse_effects": ["tremor", "hipertermia", "sudorese"],
            "patient_relevant_effects": ["tremor", "hipertermia", "sudorese"],
            "activity_warnings": ["atividade_de_risco"],
            "neurologic_effects": ["tremor"],
            "temperature_regulation_effects": ["hipertermia", "sudorese"],
            "renal_effects": ["monitoramento_renal"],
            "tremor_warning": True,
            "sedation_attention_warning": False,
            "red_flags": ["procurar_atendimento", "dor_intensa_persistente"],
            "monitoring_required": ["monitoramento_renal"],
            "patient_friendly_summary": (
                "Demo: observar tremor, sudorese e alteracoes de temperatura. Procurar "
                "atendimento se sintomas forem intensos ou houver piora importante."
            ),
            "professional_summary": (
                "Demo v0.7: revisar tremor, temperatura/sudorese e monitoramento renal."
            ),
        },
    ]
    for spec in specs:
        medication = db.scalar(
            select(MedicationModel).where(MedicationModel.active_ingredient == spec["active"])
        )
        if medication is None:
            continue
        existing = db.scalar(
            select(MedicationCounselingSummaryModel).where(
                MedicationCounselingSummaryModel.medication_id == medication.id,
                MedicationCounselingSummaryModel.source_id == spec["source_id"],
            )
        )
        values = {
            "active_ingredient_id": medication.active_ingredient_id,
            "medication_id": medication.id,
            "source_id": spec["source_id"],
            "jurisdiction": "BR",
            "source_name": spec["source_name"],
            "source_url": None,
            "source_version": "v0.7.0-demo",
            "validation_status": "pending_review",
            "generated_by": "seed_demo",
            "provider_name": "seed_demo",
            "confidence": "medium",
            "requires_review": True,
            "extracted_evidence": [
                {
                    "source_id": spec["source_id"],
                    "source_name": spec["source_name"],
                    "jurisdiction": "BR",
                    "excerpt": spec["patient_friendly_summary"],
                    "validation_status": "demo",
                }
            ],
        }
        list_fields = {
            "main_adverse_effects",
            "patient_relevant_effects",
            "activity_warnings",
            "sleep_effects",
            "appetite_weight_effects",
            "mood_behavior_effects",
            "libido_sexual_effects",
            "neurologic_effects",
            "temperature_regulation_effects",
            "gastrointestinal_effects",
            "renal_effects",
            "hepatic_effects",
            "reproductive_contraceptive_effects",
            "red_flags",
            "monitoring_required",
        }
        for field in (
            "main_adverse_effects",
            "patient_relevant_effects",
            "activity_warnings",
            "driving_warning",
            "machine_operation_warning",
            "work_at_height_warning",
            "fall_risk_warning",
            "sedation_attention_warning",
            "sleep_effects",
            "appetite_weight_effects",
            "mood_behavior_effects",
            "libido_sexual_effects",
            "neurologic_effects",
            "tremor_warning",
            "headache_warning",
            "temperature_regulation_effects",
            "blood_pressure_warning",
            "gastrointestinal_effects",
            "renal_effects",
            "hepatic_effects",
            "reproductive_contraceptive_effects",
            "red_flags",
            "monitoring_required",
            "patient_friendly_summary",
            "professional_summary",
        ):
            values[field] = spec.get(field, [] if field in list_fields else False)
        if existing is None:
            db.add(MedicationCounselingSummaryModel(**values))
        else:
            for field, value in values.items():
                setattr(existing, field, value)


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


def _seed_specialties(db: Session) -> None:
    specs = {
        "general_practice": "Medicina geral",
        "family_medicine": "Medicina de família e comunidade",
        "internal_medicine": "Clínica médica",
        "pediatrics": "Pediatria",
        "geriatrics": "Geriatria",
        "psychiatry": "Psiquiatria",
        "neurology": "Neurologia",
        "anesthesiology": "Anestesiologia",
        "emergency_medicine": "Medicina de emergência",
        "intensive_care": "Medicina intensiva",
        "oncology": "Oncologia",
        "pain_medicine": "Medicina da dor",
        "palliative_care": "Cuidados paliativos",
        "cardiology": "Cardiologia",
        "infectious_disease": "Infectologia",
        "obstetrics_gynecology": "Ginecologia e obstetrícia",
        "surgery": "Cirurgia",
        "other": "Outra especialidade demo",
    }
    for code, name in specs.items():
        if db.scalar(select(SpecialtyModel).where(SpecialtyModel.code == code)) is None:
            db.add(SpecialtyModel(code=code, name=name, demo_only=True))


def _seed_users(db: Session) -> None:
    specs = [
        ("Admin Prescripta", "admin@prescripta.local", "Admin@12345", UserRole.ADMIN, None),
        (
            "Médico geral demo",
            "medico@prescripta.local",
            "Medico@12345",
            UserRole.MEDICO,
            "general_practice",
        ),
        (
            "Anestesiologia demo",
            "anestesia@prescripta.local",
            "Anestesia@12345",
            UserRole.MEDICO,
            "anesthesiology",
        ),
        (
            "Psiquiatria demo",
            "psiquiatria@prescripta.local",
            "Psiquiatria@12345",
            UserRole.MEDICO,
            "psychiatry",
        ),
        (
            "Neurologia demo",
            "neurologia@prescripta.local",
            "Neurologia@12345",
            UserRole.MEDICO,
            "neurology",
        ),
        (
            "Oncologia demo",
            "oncologia@prescripta.local",
            "Oncologia@12345",
            UserRole.MEDICO,
            "oncology",
        ),
        (
            "Enfermagem demonstração",
            "enfermagem@prescripta.local",
            "Enfermagem@12345",
            UserRole.ENFERMAGEM,
            None,
        ),
        (
            "Auditor demonstração",
            "auditor@prescripta.local",
            "Auditor@12345",
            UserRole.AUDITOR,
            None,
        ),
        (
            "Farmácia clínica demonstração",
            "farmacia@prescripta.local",
            "Farmacia@12345",
            UserRole.FARMACEUTICO,
            None,
        ),
        (
            "Psicologia demonstração",
            "psicologia@prescripta.local",
            "Psicologia@12345",
            UserRole.PSICOLOGO,
            None,
        ),
        (
            "Segurança clínica demonstração",
            "safety@prescripta.local",
            "Safety@12345",
            UserRole.CLINICAL_SAFETY_OFFICER,
            None,
        ),
        (
            "Pesquisa RWE demonstração",
            "pesquisa@prescripta.local",
            "Pesquisa@12345",
            UserRole.PESQUISADOR,
            None,
        ),
        (
            "Revisão RWE demonstração",
            "revisao.pesquisa@prescripta.local",
            "RevisaoPesquisa@12345",
            UserRole.PESQUISADOR,
            None,
        ),
    ]
    for name, email, password, role, specialty in specs:
        profession = ROLE_PROFESSION[role]
        capabilities = sorted(
            allowed_capabilities(
                profession,
                specialty_codes=[specialty] if specialty else [],
            )
        )
        user = db.scalar(select(UserModel).where(UserModel.email == email))
        if user is None:
            db.add(
                UserModel(
                    name=name,
                    email=email,
                    hashed_password=hash_password(password),
                    role=role.value,
                    profession=profession.value,
                    capabilities=capabilities,
                    capability_policy_version="explicit-v1",
                    is_active=True,
                    specialty_code=specialty,
                    specialty_codes=[specialty] if specialty else [],
                    credential_type=("crm_demo" if role == UserRole.MEDICO else None),
                    sensitive_data_segments=(
                        ["psychological"]
                        if "patient.sensitive_psychology.read" in capabilities
                        else []
                    ),
                    credential_verification_status="demo_unverified",
                )
            )
        else:
            user.profession = profession.value
            user.capabilities = capabilities
            user.capability_policy_version = "explicit-v1"
            user.specialty_codes = [specialty] if specialty else []
            user.sensitive_data_segments = (
                ["psychological"] if "patient.sensitive_psychology.read" in capabilities else []
            )
            if role == UserRole.MEDICO and not user.specialty_code:
                user.specialty_code = specialty
                user.credential_verification_status = "demo_unverified"


def _seed_demo_patient_access(db: Session) -> None:
    object_capabilities = {
        "patient.read",
        "patient.write",
        "prescription.check",
        "prescription.override",
        "report.read",
        "report.create",
        "patient_guidance.create",
        "reconciliation.review",
        "psychology.context.write",
    }
    patients = list(db.scalars(select(PatientModel)))
    users = list(db.scalars(select(UserModel)))
    for patient in patients:
        for user in users:
            if user.institution_id != patient.institution_id:
                continue
            for capability in sorted(set(user.capabilities or []) & object_capabilities):
                existing = db.scalar(
                    select(PatientAccessGrantModel).where(
                        PatientAccessGrantModel.patient_id == patient.id,
                        PatientAccessGrantModel.user_id == user.id,
                        PatientAccessGrantModel.permission == capability,
                    )
                )
                if existing is None:
                    db.add(
                        PatientAccessGrantModel(
                            patient_id=patient.id,
                            user_id=user.id,
                            institution_id=patient.institution_id,
                            permission=capability,
                            capability=capability,
                            purpose="treatment",
                            reason="deterministic_demo_seed",
                        )
                    )


def _seed_v088_workflows(db: Session) -> None:
    """Cria o vertical slice v0.8.8 somente com fixtures sintéticas e idempotentes."""

    admin = db.scalar(select(UserModel).where(UserModel.email == "admin@prescripta.local"))
    reviewer = db.scalar(select(UserModel).where(UserModel.email == "safety@prescripta.local"))
    researcher = db.scalar(select(UserModel).where(UserModel.email == "pesquisa@prescripta.local"))
    research_reviewer = db.scalar(
        select(UserModel).where(UserModel.email == "revisao.pesquisa@prescripta.local")
    )
    nurse = db.scalar(select(UserModel).where(UserModel.email == "enfermagem@prescripta.local"))
    pharmacist = db.scalar(select(UserModel).where(UserModel.email == "farmacia@prescripta.local"))
    patient = db.scalar(select(PatientModel).order_by(PatientModel.id))
    medication = db.scalar(select(MedicationModel).order_by(MedicationModel.id))
    if any(
        item is None
        for item in (
            admin,
            reviewer,
            researcher,
            research_reviewer,
            nurse,
            pharmacist,
            patient,
            medication,
        )
    ):
        return

    protocol_service = InstitutionalClinicalProtocolService(db)
    protocol = db.scalar(
        select(InstitutionalClinicalProtocolModel).where(
            InstitutionalClinicalProtocolModel.institution_id == admin.institution_id,
            InstitutionalClinicalProtocolModel.code == "nursing-primary-care-v088",
        )
    )
    if protocol is None:
        protocol = protocol_service.create_protocol(
            InstitutionalClinicalProtocolCreate(
                code="nursing-primary-care-v088",
                name="Protocolo demonstrativo de enfermagem v0.8.8",
                program="segurança medicamentosa sintética",
            ),
            admin,
        )
        protocol_version = protocol_service.create_version(
            protocol.id,
            InstitutionalClinicalProtocolVersionCreate(
                version="2026.08-demo",
                effective_from=datetime(2026, 8, 1, tzinfo=UTC),
                effective_until=datetime(2030, 1, 1, tzinfo=UTC),
                source_refs=["fixture:institutional-protocol:v088"],
                clinical_context={
                    "demo_only": True,
                    "condition": "E11-DEMO",
                    "notice": "Não representa protocolo assistencial real.",
                },
                eligible_professions=["nursing"],
                required_capability="nursing.protocol_prescribe",
                required_parameters=["patient_id", "protocol_version_id"],
                contraindications=["outside_demo_scope"],
                requires_second_review=False,
                override_policy={"allowed": False},
                prescribing_scope={
                    "allowed_routes": ["oral"],
                    "dose_min": Decimal("1"),
                    "dose_max": Decimal("1000"),
                    "dose_unit": "mg",
                    "frequency_min_per_day": 1,
                    "frequency_max_per_day": 4,
                    "max_duration_days": 30,
                    "min_age_years": 18,
                    "max_age_years": 120,
                    "constraints": {"demo_only": True},
                },
                medications=[
                    {
                        "medication_id": medication.id,
                        "concept_set_ref": "fixture:medication:v088",
                    }
                ],
                conditions=[
                    {
                        "terminology_system": "CID-10",
                        "terminology_version": "2026-demo",
                        "condition_code": "E11-DEMO",
                        "label": "Condição metabólica sintética",
                    }
                ],
                credentials=[
                    {
                        "credential_type": "coren_demo",
                        "credential_region": "SP",
                        "verification_required": True,
                        "unexpired_required": True,
                    }
                ],
            ),
            admin,
        )
        protocol_service.review_version(
            protocol_version.id,
            ProtocolVersionReviewRequest(
                decision="reviewed_demo",
                note="Revisão humana independente de uma fixture sem uso assistencial.",
            ),
            reviewer,
        )
    else:
        protocol_version = db.scalar(
            select(InstitutionalClinicalProtocolVersionModel)
            .where(InstitutionalClinicalProtocolVersionModel.protocol_id == protocol.id)
            .order_by(InstitutionalClinicalProtocolVersionModel.created_at.desc())
        )

    nurse.credential_type = "coren_demo"
    nurse.credential_code_demo = "COREN-SP-DEMO-088"
    nurse.credential_region = "SP"
    nurse.credential_expires_at = datetime(2030, 1, 1, tzinfo=UTC)
    nurse.credential_verification_status = "verified"
    nurse.institutional_policy = {
        "nursing_prescribing_enabled": True,
        "nursing_protocols": {
            str(protocol.id): {
                "source": "fixture:institutional-protocol:v088",
                "version": getattr(protocol_version, "version", "2026.08-demo"),
                "allowed_medications": [medication.id],
                "allowed_conditions": ["E11-DEMO"],
                "limits": {"demo_only": True, "override_allowed": False},
            }
        },
    }
    db.flush()

    PharmacyWorkflowService(db).create_intervention(
        PharmacyInterventionCreate(
            patient_id=patient.id,
            medication_id=medication.id,
            intervention_type="dose",
            severity="moderate",
            priority="priority",
            problem="Dose sintética requer conferência humana independente.",
            recommendation="Revisar a dimensão e a unidade com o prescritor demonstrativo.",
            source_refs=["fixture:pharmacy-intervention:v088"],
            dose_snapshot={"value": "100", "unit": "mg", "demo_only": True},
            idempotency_key="seed-v088-pharmacy-dose-001",
            cosignature_required=False,
        ),
        pharmacist,
    )

    timeline_specs = (
        {
            "event_type": "diagnosis",
            "title": "Condição metabólica sintética",
            "summary": "Diagnóstico fictício para validar o motor agregado de coortes.",
            "source_ref": "seed-v088:timeline:diagnosis:001",
            "concept_system": "CID-10",
            "concept_code": "E11-DEMO",
            "concept_label": "Condição metabólica sintética",
            "event_date": datetime.now(UTC) - timedelta(days=45),
            "payload": {"demo_only": True},
        },
        {
            "event_type": "measurement",
            "title": "Medição sintética para Data Quality",
            "summary": "Fixture intencional com unidade desconhecida; não é dado clínico real.",
            "source_ref": "seed-v088:timeline:measurement:001",
            "concept_system": "LOINC",
            "concept_code": "LOINC-DEMO-088",
            "concept_label": "Medição sintética",
            "event_date": datetime.now(UTC) - timedelta(days=10),
            "payload": {"amount": 42, "unit": "demo-unknown-unit", "demo_only": True},
        },
    )
    for spec in timeline_specs:
        exists = db.scalar(
            select(PatientClinicalTimelineEventModel.id).where(
                PatientClinicalTimelineEventModel.institution_id == patient.institution_id,
                PatientClinicalTimelineEventModel.source_ref == spec["source_ref"],
            )
        )
        if exists is None:
            db.add(
                PatientClinicalTimelineEventModel(
                    patient_id=patient.id,
                    institution_id=patient.institution_id,
                    source_type="synthetic_fixture",
                    source_system="Prescripta demo v0.8.8",
                    provenance={"demo_only": True, "fixture_version": "v088"},
                    visibility_classification="clinical",
                    validation_status="pending_review",
                    created_by=admin.id,
                    **spec,
                )
            )
    db.flush()

    _seed_legacy_research_v088(db, researcher, research_reviewer)

    existing_study = db.scalar(
        select(ResearchStudyModel).where(
            ResearchStudyModel.institution_id == researcher.institution_id,
            ResearchStudyModel.slug == "seguranca-medicamentosa-sintetica-v090",
        )
    )
    if existing_study is not None:
        return

    research_service = ResearchService(db)
    study = research_service.create_study(
        ResearchStudyCreate(
            title="Estudo sintético de segurança medicamentosa v0.9.0",
            slug="seguranca-medicamentosa-sintetica-v090",
            description="Vertical slice demonstrativo e reprodutível, sem dados reais.",
            research_question=(
                "Qual é o perfil agregado da condição sintética entre pacientes adultos demo?"
            ),
            objective="Demonstrar coorte, attrition, provenance e Data Quality determinísticos.",
            design="retrospective_cohort",
            data_source_classification="synthetic",
        ),
        researcher,
    )
    study_protocol = research_service.create_protocol_version(
        study.id,
        StudyProtocolVersionCreate(
            population={"description": "Pacientes adultos exclusivamente sintéticos"},
            exposure={"description": "Condição codificada na timeline demo"},
            comparator={"description": "Sem comparação causal"},
            outcome={"description": "Presença agregada do evento sintético"},
            index_date={"event": "data_snapshot_marker"},
            washout={"days": 0},
            follow_up={"days": 90},
            censoring={"strategy": "none_demo"},
            inclusion=[{"criterion": "age_gte_18"}],
            exclusion=[],
            covariates=[],
            missing_data_strategy={"strategy": "report_missingness"},
            statistical_plan={"methods": ["descriptive_only"]},
            limitations=["Fixture sem validade clínica ou externa."],
            source_refs=["synthetic-dataset:prescripta:v090"],
        ),
        researcher,
    )
    research_service.review_protocol(
        study_protocol.id,
        ResearchReviewRequest(
            decision="reviewed_demo",
            note="Revisão metodológica humana independente para demonstração sintética.",
        ),
        research_reviewer,
    )
    concept = research_service.create_concept_set(
        ConceptSetCreate(
            name="Condição metabólica sintética v0.9.0",
            domain="condition",
            terminology_versions={"CID-10": "2026-demo"},
            include_descendants=False,
            source_refs=["terminology-fixture:cid10:v090"],
            license_metadata={"fixture": True, "redistribution": "synthetic-only"},
            provenance={"origin": "prescripta-demo-seed", "demo_only": True},
            members=[
                {
                    "terminology_system": "CID-10",
                    "terminology_version": "2026-demo",
                    "concept_code": "E11-DEMO",
                    "label": "Condição metabólica sintética",
                    "excluded": False,
                }
            ],
        ),
        researcher,
    )
    concept_version_id = concept["version"]["id"]
    for decision in ("human_reviewed", "approved_for_demo_study"):
        research_service.review_concept_set(
            concept_version_id,
            ConceptSetReviewRequest(
                decision=decision,
                note="Revisão humana independente da terminologia sintética demonstrativa.",
            ),
            research_reviewer,
        )
    cohort = research_service.create_cohort_version(
        study.id,
        CohortDefinitionCreate(
            name="Adultos com condição sintética",
            definition={
                "all": [
                    {
                        "criterion": "age",
                        "operator": "gte",
                        "value": 18,
                        "label": "Adultos",
                    },
                    {
                        "criterion": "condition",
                        "operator": "exists",
                        "concept_set_version_id": concept_version_id,
                        "label": "Condição metabólica sintética",
                    },
                ],
                "exclude": [],
            },
        ),
        researcher,
    )
    research_service.review_cohort(
        cohort.id,
        CohortReviewRequest(
            decision="reviewed_demo",
            note="DSL e concept set revisados por pessoa independente do autor.",
        ),
        research_reviewer,
    )
    outcome = research_service.create_outcome(
        study.id,
        OutcomeDefinitionCreate(
            name="Condição sintética em até 90 dias",
            domain="condition",
            concept_set_version_ids=[concept_version_id],
            event_qualification={"minimum_events": 1},
            observation_window={"after_index_days": 90},
            temporal_relationship="after_index",
            source_refs=["synthetic-dataset:prescripta:v090"],
            limitations=["Outcome demonstrativo sem validação clínica."],
        ),
        researcher,
    )
    research_service.review_outcome(
        outcome.id,
        OutcomeReviewRequest(
            decision="reviewed_demo",
            note="Outcome sintético revisado de forma independente para a demonstração.",
        ),
        research_reviewer,
    )
    cohort_run = research_service.execute_cohort(
        cohort.id,
        CohortRunRequest(data_snapshot_marker="synthetic-seed-v090-001"),
        researcher,
    )
    DataQualityService(db).run(researcher, study.id)
    analysis_service = ResearchAnalysisService(db)
    plan = analysis_service.create_plan(
        study.id,
        AnalysisPlanCreate(
            cohort_run_id=cohort_run.id,
            objectives=["Descrever a população sintética elegível."],
            variables=[
                {"name": "age_years", "type": "numeric"},
                {"name": "sex", "type": "categorical"},
            ],
            steps=[{"method": "population_count"}, {"method": "baseline_table_1"}],
            descriptive_metrics=[
                "n",
                "missing",
                "mean",
                "sd",
                "median",
                "q1",
                "q3",
                "iqr",
                "min",
                "max",
            ],
            subgroup_definitions=[],
            missing_data_approach="report_only",
            methods=[
                "population_count",
                "numeric_summary",
                "categorical_distribution",
                "prevalence",
                "baseline_table_1",
                "resource_utilization",
            ],
            planned_outputs=[
                "summary_cards",
                "table_1",
                "distribution_chart",
                "attrition_table",
                "research_package",
            ],
            output_specification={"small_cell_threshold": 5, "aggregate_only": True},
            source_refs=["synthetic-dataset:prescripta:v090"],
            limitations=["Fixture sintética sem validade clínica ou externa."],
        ),
        researcher,
    )
    analysis_service.review_plan(
        plan.id,
        ResearchReviewRequest(
            decision="reviewed_demo",
            note="Plano descritivo revisado de forma independente para demonstração.",
        ),
        research_reviewer,
    )
    analysis_run = analysis_service.execute(plan.id, researcher)
    analysis_service.export_package(analysis_run.id, researcher)


def _seed_legacy_research_v088(
    db: Session,
    researcher: UserModel,
    research_reviewer: UserModel,
) -> None:
    existing_study = db.scalar(
        select(ResearchStudyModel).where(
            ResearchStudyModel.institution_id == researcher.institution_id,
            ResearchStudyModel.slug == "seguranca-medicamentosa-sintetica-v088",
        )
    )
    if existing_study is not None:
        return

    research_service = ResearchService(db)
    study = research_service.create_study(
        ResearchStudyCreate(
            title="Estudo sintético de segurança medicamentosa v0.8.8",
            slug="seguranca-medicamentosa-sintetica-v088",
            description="Vertical slice demonstrativo e reprodutível, sem dados reais.",
            research_question=(
                "Qual é o perfil agregado da condição sintética entre pacientes adultos demo?"
            ),
            objective="Demonstrar coorte, attrition, provenance e Data Quality determinísticos.",
            design="retrospective_cohort",
            data_source_classification="synthetic",
        ),
        researcher,
    )
    protocol = research_service.create_protocol_version(
        study.id,
        StudyProtocolVersionCreate(
            population={"description": "Pacientes adultos exclusivamente sintéticos"},
            exposure={"description": "Condição codificada na timeline demo"},
            comparator={"description": "Sem comparação causal"},
            outcome={"description": "Presença agregada do evento sintético"},
            index_date={"event": "data_snapshot_marker"},
            washout={"days": 0},
            follow_up={"days": 90},
            censoring={"strategy": "none_demo"},
            inclusion=[{"criterion": "age_gte_18"}],
            exclusion=[],
            covariates=[],
            missing_data_strategy={"strategy": "report_missingness"},
            statistical_plan={"methods": ["descriptive_only"]},
            limitations=["Fixture sem validade clínica ou externa."],
            source_refs=["synthetic-dataset:prescripta:v088"],
        ),
        researcher,
    )
    research_service.review_protocol(
        protocol.id,
        ResearchReviewRequest(
            decision="reviewed_demo",
            note="Revisão metodológica humana independente para demonstração sintética.",
        ),
        research_reviewer,
    )
    concept = research_service.create_concept_set(
        ConceptSetCreate(
            name="Condição metabólica sintética v0.8.8",
            domain="condition",
            terminology_versions={"CID-10": "2026-demo"},
            include_descendants=False,
            source_refs=["terminology-fixture:cid10:v088"],
            license_metadata={"fixture": True, "redistribution": "synthetic-only"},
            provenance={"origin": "prescripta-demo-seed", "demo_only": True},
            members=[
                {
                    "terminology_system": "CID-10",
                    "terminology_version": "2026-demo",
                    "concept_code": "E11-DEMO",
                    "label": "Condição metabólica sintética",
                    "excluded": False,
                }
            ],
        ),
        researcher,
    )
    concept_version_id = concept["version"]["id"]
    for decision in ("human_reviewed", "approved_for_demo_study"):
        research_service.review_concept_set(
            concept_version_id,
            ConceptSetReviewRequest(
                decision=decision,
                note="Revisão humana independente da terminologia sintética demonstrativa.",
            ),
            research_reviewer,
        )
    cohort = research_service.create_cohort_version(
        study.id,
        CohortDefinitionCreate(
            name="Adultos com condição sintética",
            definition={
                "all": [
                    {
                        "criterion": "age",
                        "operator": "gte",
                        "value": 18,
                        "label": "Adultos",
                    },
                    {
                        "criterion": "condition",
                        "operator": "exists",
                        "concept_set_version_id": concept_version_id,
                        "label": "Condição metabólica sintética",
                    },
                ],
                "exclude": [],
            },
        ),
        researcher,
    )
    research_service.review_cohort(
        cohort.id,
        CohortReviewRequest(
            decision="reviewed_demo",
            note="DSL e concept set revisados por pessoa independente do autor.",
        ),
        research_reviewer,
    )
    research_service.create_outcome(
        study.id,
        OutcomeDefinitionCreate(
            name="Condição sintética em até 90 dias",
            domain="condition",
            concept_set_version_ids=[concept_version_id],
            event_qualification={"minimum_events": 1},
            observation_window={"after_index_days": 90},
            temporal_relationship="after_index",
            source_refs=["synthetic-dataset:prescripta:v088"],
            limitations=["Outcome demonstrativo sem validação clínica."],
        ),
        researcher,
    )
    research_service.execute_cohort(
        cohort.id,
        CohortRunRequest(data_snapshot_marker="synthetic-seed-v088-001"),
        researcher,
    )
    DataQualityService(db).run(researcher)
