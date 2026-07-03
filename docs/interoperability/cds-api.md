# CDS API Demonstrativa

Endpoint:

```http
POST /api/cds/prescription-check
```

Permissoes: `admin`, `medico`, `enfermagem`.

## Entrada

```json
{
  "patient": {},
  "medication_request": {},
  "allergies": [],
  "conditions": [],
  "current_medications": [],
  "observations": [],
  "persist": false
}
```

## Saida

```json
{
  "status": "bloqueado",
  "risk_level": "critico",
  "alerts": [],
  "cards": [],
  "audit_id": "demo-1",
  "educational_notice": "..."
}
```

O endpoint usa o motor deterministico, nao chama IA automaticamente e nao salva dados clinicos permanentes quando `persist=false`.

