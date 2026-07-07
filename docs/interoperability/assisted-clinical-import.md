# Importação Clínica Assistida

A importação clínica assistida recebe dados fictícios FHIR/JSON/CSV, mapeia para registros internos e mantém tudo em `pending_review` até revisão humana.

## O Que A v0.7.1 Fecha

- Visualização de lote importado.
- Consentimento/base legal declarada.
- Registros fonte preservados.
- Reconciliação campo a campo.
- Badges de novo, duplicado, conflito, possível match, aceito e rejeitado.
- Justificativa por aceite/rejeição.
- Aceite em lote apenas de itens sem conflito.
- Auditoria de decisão granular.

## Limite

Não há integração hospitalar real. Qualquer integração real exige API oficial, contrato, governança, segurança, LGPD e validação operacional.

## Endpoints

- `POST /api/integrations/fhir/import-bundle`
- `POST /api/integrations/json/import`
- `POST /api/integrations/csv/import`
- `GET /api/integrations/imports/{id}/reconciliation`
- `POST /api/integrations/imports/{id}/reconciliation/items/{item_id}/accept`
- `POST /api/integrations/imports/{id}/reconciliation/items/{item_id}/reject`
- `POST /api/integrations/imports/{id}/reconciliation/accept-safe`
