from __future__ import annotations

from app.reports.schemas import PRESCRIPTA_VERSION

LEGAL_NOTICE = (
    "Prescripta e um sistema educacional de apoio a prescricao segura. "
    "Nao e dispositivo medico validado e nao substitui avaliacao clinica, bula, "
    "protocolo institucional ou decisao profissional."
)

REPORT_TITLES = {
    "prescription_analysis": "Relatorio Tecnico de Prescricao",
    "patient_guidance": "Orientacoes ao Paciente",
    "reconciliation": "Relatorio de Reconciliacao Clinica",
    "audit": "Relatorio de Auditoria",
}

PROMPT_VERSIONS = {
    "prescription_analysis": "report_prescription_analysis_v0.8.1",
    "patient_guidance": "report_patient_guidance_v0.8.1",
    "reconciliation": "report_reconciliation_v0.8.1",
    "audit": "report_audit_v0.8.1",
}

REPORT_FOOTER = f"{LEGAL_NOTICE} Versao Prescripta: {PRESCRIPTA_VERSION}."


def prompt_for_report_type(report_type: str) -> str:
    prompt_version = PROMPT_VERSIONS.get(report_type, "report_generic_v0.8.1")
    return f"""
Voce e o AIReportComposer do Prescripta.
Prompt version: {prompt_version}.

Tarefa:
- Gerar apenas secoes narrativas em JSON valido.
- Usar somente informacoes presentes no ReportEvidenceBundle.
- Citar apenas source_ids presentes no bundle quando preencher cited_source_ids.
- Nao inventar fonte, efeito adverso, contraindicacao, interacao, regra, dose ou decisao.
- Nao alterar risco final, status final, bloqueio, severidade, dose, duracao, regra ou fonte.
- Nao substituir avaliacao profissional.
- Usar linguagem profissional no resumo tecnico.
- Usar linguagem simples e nao alarmista no campo patient_guidance.
- Nao retornar HTML nem Markdown perigoso.

Retorne JSON com exatamente estas chaves:
executive_summary, professional_explanation, patient_guidance, evidence_summary,
missing_data_note, functional_context_note, reconciliation_summary,
safety_counseling_summary, limitations_note, human_review_note, source_note,
confidence, requires_human_review, warnings, cited_source_ids.
""".strip()
