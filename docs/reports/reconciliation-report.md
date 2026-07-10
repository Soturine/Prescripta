# Relatório de Reconciliação Clínica

O relatório de reconciliação usa o lote de importação e a reconciliação granular.

Endpoint:

```txt
GET /api/reports/imports/{import_id}/reconciliation.pdf
```

Exportações:

```txt
GET /api/exports/imports/{import_id}.json
GET /api/exports/imports/{import_id}.csv
```

Conteúdo:

- lote, origem e tipo da importação;
- consentimento;
- status do lote;
- itens novos, duplicados, conflitos e possíveis matches;
- decisão por item, revisor, data e justificativa;
- evidências e timeline.

Integrações reais seguem fora do escopo. O fluxo permanece assistido e exige
revisão humana.
