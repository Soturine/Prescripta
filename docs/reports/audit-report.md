# Relatório de Auditoria

O relatório de auditoria consolida eventos conforme filtros.

Endpoint:

```txt
GET /api/reports/audit-events/pdf
```

Exportações:

```txt
GET /api/exports/audit-events.json
GET /api/exports/audit-events.csv
```

Filtros aceitos incluem usuário, paciente, medicamento, risco, status, provider,
modelo, fonte, jurisdição, ação, data inicial, data final e texto livre.

O relatório mostra total de eventos, eventos críticos, eventos de IA, eventos de
relatório/exportação e hash do bundle usado.
