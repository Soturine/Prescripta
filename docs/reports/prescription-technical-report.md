# Relatório Técnico de Prescrição

O relatório técnico usa uma checagem registrada em `PrescriptionAuditModel`.

Endpoint principal:

```txt
GET /api/reports/prescriptions/{audit_id}/pdf
```

Preview:

```txt
GET /api/reports/prescriptions/{audit_id}/preview
```

Conteúdo:

- paciente ou referência anonimizada;
- medicamento, princípio ativo e alias comercial quando disponível;
- dose por administração, frequência, dose diária e dose acumulada;
- status final e risco final;
- alertas e regras disparadas;
- perfil funcional e dados faltantes;
- fontes, jurisdição e status de validação;
- narrativa assistida ou fallback;
- hash do `ReportEvidenceBundle`;
- versão do template e aviso legal.

A IA não altera nenhum campo decisório. Ela apenas compõe texto validado.
