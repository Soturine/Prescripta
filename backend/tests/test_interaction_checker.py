from app.domain.alert import RiskLevel
from app.domain.medication import Medication
from app.services.interaction_checker import check_interactions


def test_alerts_when_demo_interaction_matches_current_medication() -> None:
    medication = Medication(
        id=1,
        brand_name="Ibuvida",
        active_ingredient="ibuprofeno",
        therapeutic_class="anti-inflamatorio",
        max_daily_dose_mg=2400,
        allowed_routes=["oral"],
        contraindications=[],
    )

    alerts = check_interactions(medication, ["varfarina"])

    assert alerts
    assert alerts[0].severity == RiskLevel.CRITICAL
    assert alerts[0].code == "DRUG_INTERACTION"
