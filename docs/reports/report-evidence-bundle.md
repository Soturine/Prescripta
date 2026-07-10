# ReportEvidenceBundle

`ReportEvidenceBundle` é o pacote oficial de dados usado por relatórios e,
quando habilitado, pela narrativa de IA.

Regras:

- deve ser serializável em JSON;
- possui hash estável;
- minimiza dados sensíveis por padrão;
- não envia banco inteiro para IA;
- não inclui API Key ou segredo;
- contém fontes, jurisdição e status de validação;
- mantém regras disparadas e alertas já calculados pelo motor determinístico.

Campos principais:

- `report_type`;
- `report_mode`;
- `report_version`;
- `patient_context`;
- `prescription_result`;
- `reconciliation_result`;
- `audit_result`;
- `rules_fired`;
- `sources`;
- `ai_context`;
- `metadata`.

O hash aparece em `GeneratedReport`, preview, PDF e exportações.
