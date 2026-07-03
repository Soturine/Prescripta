from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.database.models import MedicationModel, PatientModel, UserModel
from app.domain.user import UserRole


def seed_demo_data(db: Session) -> None:
    has_medications = db.scalar(select(MedicationModel.id).limit(1))
    has_patients = db.scalar(select(PatientModel.id).limit(1))
    has_users = db.scalar(select(UserModel.id).limit(1))

    if not has_medications:
        db.add_all(
            [
                MedicationModel(
                    brand_name="Ibuvida",
                    active_ingredient="ibuprofeno",
                    therapeutic_class="anti-inflamatório não esteroidal",
                    max_daily_dose_mg=2400,
                    max_duration_days=5,
                    max_cumulative_dose_mg=7200,
                    condition_specific_limits={"renal": 1200, "gastrointestinal": 1200},
                    allowed_routes=["oral"],
                    contraindications=["ulcera ativa", "doenca renal grave"],
                    renal_caution=True,
                    gastrointestinal_caution=True,
                    elderly_caution=True,
                    metabolism_organs=["hepatico"],
                    elimination_organs=["renal"],
                    organs_involved=["renal", "gastrointestinal"],
                    relevant_adverse_effects=["sangramento gastrointestinal", "gastrite"],
                    structured_contraindications=["renal", "gastrointestinal"],
                    therapeutic_action="analgesia e anti-inflamatório",
                    alternative_group="analgesia anti-inflamatoria",
                    related_medications=["paracetamol", "nimesulida"],
                    knowledge_source="Base interna demonstrativa v0.4.0",
                    notes="Medicamento demonstrativo inspirado em regra comum de dose máxima.",
                ),
                MedicationModel(
                    brand_name="Nimesulida Demo",
                    active_ingredient="nimesulida",
                    therapeutic_class="anti-inflamatório não esteroidal",
                    max_daily_dose_mg=200,
                    max_duration_days=5,
                    max_cumulative_dose_mg=1000,
                    condition_specific_limits={"hepatico": 100},
                    allowed_routes=["oral"],
                    contraindications=["doenca hepatica"],
                    hepatic_caution=True,
                    gastrointestinal_caution=True,
                    elderly_caution=True,
                    metabolism_organs=["hepatico"],
                    elimination_organs=["renal"],
                    organs_involved=["hepatico", "gastrointestinal"],
                    relevant_adverse_effects=["hepatotoxicidade demonstrativa", "dispepsia"],
                    structured_contraindications=["hepatico"],
                    therapeutic_action="analgesia e anti-inflamatório",
                    alternative_group="analgesia anti-inflamatoria",
                    related_medications=["ibuprofeno", "paracetamol"],
                    knowledge_source="Base interna demonstrativa v0.4.0",
                    notes="Seed educacional para cautela hepática e duração.",
                ),
                MedicationModel(
                    brand_name="Paracetamol Demo",
                    active_ingredient="paracetamol",
                    therapeutic_class="analgésico antitérmico",
                    max_daily_dose_mg=3000,
                    max_duration_days=7,
                    max_cumulative_dose_mg=12000,
                    condition_specific_limits={"hepatico": 1500},
                    allowed_routes=["oral"],
                    contraindications=["doenca hepatica grave"],
                    hepatic_caution=True,
                    metabolism_organs=["hepatico"],
                    elimination_organs=["renal"],
                    organs_involved=["hepatico"],
                    relevant_adverse_effects=["hepatotoxicidade demonstrativa"],
                    structured_contraindications=["hepatico"],
                    therapeutic_action="analgesia",
                    alternative_group="analgesia anti-inflamatoria",
                    related_medications=["ibuprofeno", "nimesulida"],
                    knowledge_source="Base interna demonstrativa v0.4.0",
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
                    therapeutic_class="antidiabético",
                    max_daily_dose_mg=2550,
                    allowed_routes=["oral"],
                    contraindications=["doenca renal grave", "acidose metabolica"],
                    notes="Seed educacional para contraindicação por comorbidade.",
                ),
                MedicationModel(
                    brand_name="Sertral",
                    active_ingredient="sertralina",
                    therapeutic_class="inibidor seletivo da recaptacao de serotonina",
                    max_daily_dose_mg=200,
                    allowed_routes=["oral"],
                    contraindications=["uso de imao"],
                    notes="Seed educacional para interacoes demonstrativas.",
                ),
            ]
        )

    if not has_patients:
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
                ),
                PatientModel(
                    name="Carlos Demonstração",
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
                    renal_condition="renal",
                    cardiac_condition="cardiaco",
                    gastrointestinal_history="gastrointestinal",
                    hypertension=True,
                    diabetes=False,
                    adverse_reactions=["sangramento gastrointestinal"],
                    clinical_notes="Perfil demonstrativo para triagem rápida e cautela renal.",
                    clinical_profile_completeness_score=89,
                ),
            ]
        )

    if not has_users:
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
                    name="Médico Demonstração",
                    email="medico@prescripta.local",
                    hashed_password=hash_password("Medico@12345"),
                    role=UserRole.MEDICO.value,
                    is_active=True,
                ),
                UserModel(
                    name="Enfermagem Demonstração",
                    email="enfermagem@prescripta.local",
                    hashed_password=hash_password("Enfermagem@12345"),
                    role=UserRole.ENFERMAGEM.value,
                    is_active=True,
                ),
                UserModel(
                    name="Auditor Demonstração",
                    email="auditor@prescripta.local",
                    hashed_password=hash_password("Auditor@12345"),
                    role=UserRole.AUDITOR.value,
                    is_active=True,
                ),
            ]
        )

    db.commit()
