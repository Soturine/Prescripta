from pathlib import Path

VERSION_FILE = Path(__file__).resolve().parents[3] / "VERSION"
APP_VERSION = VERSION_FILE.read_text(encoding="utf-8").strip()
APP_VERSION_LABEL = f"v{APP_VERSION}"

# Estas versões têm ciclo de vida próprio e não acompanham automaticamente a aplicação.
REPORT_TEMPLATE_VERSION = "prescripta_report_template_v0.8.1"
CLINICAL_DECISION_SCHEMA_VERSION = "1.0"
CLINICAL_POLICY_VERSION = "demo_policy_2026-07-r1"
