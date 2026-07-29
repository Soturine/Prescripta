# Linha do Tempo da Decisão

A linha do tempo organiza os passos que levaram ao relatório ou evento auditado.

Para prescrição:

1. Prescrição criada ou avaliada.
2. Regras determinísticas executadas.
3. Alertas disparados.
4. Fontes consultadas.
5. Narrativa assistida ou fallback.
6. Relatório gerado.

Para reconciliação:

1. Importação clínica criada.
2. Consentimento registrado.
3. Reconciliação granular criada.
4. Relatório de reconciliação gerado.

Para auditoria:

1. Filtros aplicados.
2. Eventos agregados.
3. Relatório de auditoria gerado.

Endpoints:

```txt
GET /api/reports/prescriptions/{audit_id}/timeline
GET /api/audit/{event_id}/timeline
```
