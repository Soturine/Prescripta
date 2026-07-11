from __future__ import annotations

from app.reports.schemas import PRESCRIPTA_VERSION

LEGAL_NOTICE = (
    "Prescripta é um sistema educacional de apoio à prescrição segura. "
    "Não é dispositivo médico validado e não substitui avaliação clínica, bula, "
    "protocolo institucional ou decisão profissional."
)

REPORT_TITLES = {
    "prescription_analysis": "Relatório Técnico de Prescrição",
    "patient_guidance": "Orientações ao Paciente",
    "reconciliation": "Relatório de Reconciliação Clínica",
    "audit": "Relatório de Auditoria",
}

PROMPT_VERSIONS = {
    "prescription_analysis": "report_prescription_analysis_v0.8.1",
    "patient_guidance": "report_patient_guidance_v0.8.1",
    "reconciliation": "report_reconciliation_v0.8.1",
    "audit": "report_audit_v0.8.1",
}

REPORT_FOOTER = f"{LEGAL_NOTICE} Versão Prescripta: {PRESCRIPTA_VERSION}."


def prompt_for_report_type(report_type: str) -> str:
    prompt_version = PROMPT_VERSIONS.get(report_type, "report_generic_v0.8.1")
    return f"""
Você é o AIReportComposer do Prescripta.
Prompt version: {prompt_version}.

Tarefa:
- Gerar apenas seções narrativas em JSON válido.
- Usar somente informações presentes no ReportEvidenceBundle.
- Citar apenas source_ids presentes no bundle quando preencher cited_source_ids.
- Não inventar fonte, efeito adverso, contraindicação, interação, regra, dose ou decisão.
- Não alterar risco final, status final, bloqueio, severidade, dose, duração, regra ou fonte.
- Não substituir avaliação profissional.
- Usar linguagem profissional no resumo técnico.
- Usar linguagem simples e não alarmista no campo patient_guidance.
- Não retornar HTML nem Markdown perigoso.

Retorne JSON com exatamente estas chaves:
executive_summary, professional_explanation, patient_guidance, evidence_summary,
missing_data_note, functional_context_note, reconciliation_summary,
safety_counseling_summary, limitations_note, human_review_note, source_note,
confidence, requires_human_review, warnings, cited_source_ids.
""".strip()
