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
                    therapeutic_class="anti-inflamatorio nao esteroidal",
                    max_daily_dose_mg=2400,
                    allowed_routes=["oral"],
                    contraindications=["ulcera ativa", "doenca renal grave"],
                    notes="Medicamento demonstrativo inspirado em regra comum de dose maxima.",
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

    db.commit()
