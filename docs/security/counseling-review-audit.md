# Auditoria de Resumos e Reconciliacao

Eventos auditados na v0.7.0:

- `medication_counseling.generate`
- `medication_counseling.review`
- `patient.functional_profile.update`
- `clinical_reconciliation.item.accepted`
- `clinical_reconciliation.item.rejected`
- `clinical_reconciliation.safe_items.accepted`

## Permissoes

- Admin e medico: gerar/revisar resumos, editar perfil funcional e decidir reconciliacao.
- Enfermagem: visualizar orientacoes e importacoes conforme regras existentes.
- Auditor: visualizar importacoes/reconciliacao e auditoria; nao decide item.

## Dados sensiveis

Nao registrar senha, credencial de portal ou dado real de paciente. Os seeds e exemplos permanecem demonstrativos.

## IA

Geracao por IA ou fallback fica `pending_review` e exige revisao humana para `curated` ou `validated`. A IA nao altera status da prescricao, risco, bloqueio ou recomendacao final.
