# Registro De Prompts

Este registro lista prompts versionados usados ou preparados pelo Prescripta.
Cada prompt deve declarar objetivo, entrada, saida JSON, campos proibidos,
regras de seguranca, fallback e teste esperado.

## v0.8.3

| Modulo | Prompt | Arquivo |
| --- | --- | --- |
| Checagem de prescrição | `prescription_explanation_v0.8.3` | `backend/app/ai/prompts/prescription_explanation_v0.8.3.md` |
| Orientação ao paciente | `patient_guidance_v0.8.3` | `backend/app/ai/prompts/patient_guidance_v0.8.3.md` |
| Relatorios | `report_narrative_v0.8.3` | `backend/app/ai/prompts/report_narrative_v0.8.3.md` |
| Protocolos | `protocol_explanation_v0.8.3` | `backend/app/ai/prompts/protocol_explanation_v0.8.3.md` |
| Medicamentos | `medication_knowledge_extraction_v0.8.3` | `backend/app/ai/prompts/medication_knowledge_extraction_v0.8.3.md` |
| Laudos/documentos | `clinical_document_extraction_v0.8.3` | `backend/app/ai/prompts/clinical_document_extraction_v0.8.3.md` |
| Histórico do paciente | `patient_history_summary_v0.8.3` | `backend/app/ai/prompts/patient_history_summary_v0.8.3.md` |
| Auditoria | `audit_summary_v0.8.3` | `backend/app/ai/prompts/audit_summary_v0.8.3.md` |

## v0.8.2

Explicacao de protocolos rapidos usa instrucao runtime em
`EmergencyProtocolService`. A resposta aceita apenas narrativa e referencias
existentes nos passos do protocolo.

## v0.8.1

| Tipo | Prompt |
| --- | --- |
| Prescrição tecnica | `report_prescription_analysis_v0.8.1` |
| Orientacoes ao paciente | `report_patient_guidance_v0.8.1` |
| Reconciliacao | `report_reconciliation_v0.8.1` |
| Auditoria | `report_audit_v0.8.1` |

## Regras Globais

- Prompt recebe apenas bundle minimizado do modulo.
- IA deve retornar JSON validado.
- Campos inesperados ou reservados acionam fallback.
- Fontes citadas precisam existir no bundle.
- IA não altera risco, status, dose, duracao, bloqueio, fonte, protocolo ou
  decisão.
- Dado extraido entra como `pending_review`.
- Dado identificavel não deve ser enviado por padrao.

## Localizacao

- Prompts v0.8.3: `backend/app/ai/prompts/`
- Relatorios runtime: `backend/app/reports/templates.py`
- Composer de relatório: `backend/app/reports/ai_report_composer.py`
