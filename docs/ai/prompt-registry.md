# Registro De Prompts

Os prompts de relatório ficam versionados por tipo:

| Tipo | Prompt v0.8.1 |
| --- | --- |
| Prescrição técnica | `report_prescription_analysis_v0.8.1` |
| Orientações ao paciente | `report_patient_guidance_v0.8.1` |
| Reconciliação | `report_reconciliation_v0.8.1` |
| Auditoria | `report_audit_v0.8.1` |

## Regras

- Prompt recebe apenas `ReportEvidenceBundle`.
- IA deve retornar JSON validado por `ReportNarrativeSchema`.
- `extra="forbid"` bloqueia campos reservados ou inesperados.
- `cited_source_ids` precisa existir no bundle.
- IA não pode alterar risco, status, dose, duração, bloqueio, fonte ou decisão.
- Falha, JSON inválido, fonte inventada ou prompt injection acionam fallback
  determinístico.

## Localização

- Templates runtime: `backend/app/reports/templates.py`
- Arquivos de referência: `backend/app/reports/prompts/`
- Composer: `backend/app/reports/ai_report_composer.py`
