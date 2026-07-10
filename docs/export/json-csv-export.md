# Exportação JSON/CSV

Exportações da v0.8.0 são estruturadas, versionadas e auditadas.

Endpoints:

```txt
GET /api/exports/prescriptions/{audit_id}.json
GET /api/exports/prescriptions/{audit_id}.csv
GET /api/exports/imports/{import_id}.json
GET /api/exports/imports/{import_id}.csv
GET /api/exports/audit-events.json
GET /api/exports/audit-events.csv
GET /api/exports/reports/{report_id}.json
```

Regras:

- JSON inclui `export_type`, `export_version`, `generated_at` e `data`.
- CSV usa cabeçalhos claros e achata objetos quando necessário.
- Exportação registra auditoria.
- Exportação anonimizada está disponível para prescrição e importação.
- API Keys, tokens e segredos não são exportados.

Permissões:

- `admin`, `medico` e `auditor` podem exportar dados clínicos conforme rota.
- `admin` e `auditor` podem exportar auditoria.
