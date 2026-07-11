# CDS API Demonstrativa

Endpoint:

```http
POST /api/cds/prescription-check
```

Permissoes: `admin`, `médico`, `enfermagem`.

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

O endpoint usa o motor deterministico, não chama IA automaticamente e não salva dados clínicos permanentes quando `persist=false`.

