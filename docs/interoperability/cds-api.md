# CDS API Demonstrativa

Endpoint:

```http
POST /api/cds/prescription-check
```

API própria e demonstrativa. Não implementa HL7 CDS Hooks (sem discovery, hooks, prefetch ou
feedback); os `cards` apenas se inspiram no formato.

## Autorização

O acesso é por capacidade, não por perfil: a rota exige `prescription.check`. A tabela abaixo é
verificada contra `PROFESSION_CAPABILITY_TEMPLATES` por `backend/tests/test_cds_docs_matrix.py`;
grants individuais podem acrescentar ou remover a capacidade de um usuário.

<!-- cds-capability-matrix:start -->
| Profissão (template) | `prescription.check` |
|---|---|
| administration | não |
| medicine | sim |
| nursing | sim |
| pharmacy | sim |
| psychology | não |
| audit | não |
| research | não |
| clinical_safety | não |
<!-- cds-capability-matrix:end -->

Administração não recebe a capacidade por padrão (separação entre gestão e decisão clínica).

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

- `medication_request.medication_id` identifica a apresentação exata. Quando só o princípio ativo
  (ou nome/alias) é informado e ele resolve para mais de um cadastro, a API responde `409` com
  `code = ambiguous_medication` e a lista `candidates` (id, nome, concentração, forma); nunca
  escolhe uma apresentação arbitrariamente.
- `observations` (até 100 itens) é aceito por compatibilidade, mas **não é interpretado** pelo
  motor. A resposta declara isso em `observations_evaluation` e acrescenta um card de aviso.
- `persist=true` é rejeitado; importação persistente usa o fluxo com consentimento e reconciliação.
- `Idempotency-Key` (opcional) é escopado por usuário. A mesma chave com o mesmo conteúdo reproduz
  a resposta original; com conteúdo diferente responde `409 idempotency_key_reused`. Em requisições
  concorrentes, a perdedora reproduz a vencedora (ou recebe 409) sem deixar auditoria órfã.

## Saída

```json
{
  "decision": {},
  "coverage_status": "covered",
  "status": "atencao",
  "risk_level": "moderado",
  "alerts": [],
  "cards": [],
  "audit_id": "cds-1",
  "idempotency_key": "auto-…",
  "educational_notice": "...",
  "observations_evaluation": {
    "status": "none_received",
    "received_count": 0,
    "evaluated_count": 0,
    "reason": null
  }
}
```

O endpoint usa o motor determinístico, não chama IA automaticamente e não salva dados clínicos
permanentes. Ausência de alerta não indica segurança; consulte `decision.coverage`.
