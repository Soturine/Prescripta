# Visão geral da arquitetura

O Prescripta é um monorepo com API FastAPI, aplicação React/TypeScript e persistência SQLAlchemy.
PostgreSQL é o alvo fora do modo local; SQLite e auto-seed existem apenas para desenvolvimento/demo.

## Camadas

- `backend/app/domain`: contratos de domínio imutáveis, decisão, dose, paciente e medicamento;
- `backend/app/services`: regras determinísticas, orquestração, autorização e casos de uso;
- `backend/app/repositories`: queries, paginação e escopo de objetos;
- `backend/app/reports`: EvidenceBundle, snapshot, PDF/JSON/CSV e narrativa controlada;
- `backend/app/integrations`: adapters demonstrativos, consentimento e reconciliação;
- `backend/app/knowledge`: índice lexical versionado e citações por chunk;
- `backend/app/api/routes`: transporte HTTP e dependências de autenticação;
- `backend/migrations`: schema versionado por Alembic;
- `frontend/src`: interface, contratos, estado de sessão e cliente HTTP.

## Fluxo de decisão

```text
request tipado
  → capacidade + instituição + relação/purpose por paciente
  → paciente/medicamento resolvidos no servidor
  → motores determinísticos + dose + psychotropic + policy
  → ClinicalDecisionEnvelope + coverage + abstention
  → snapshot canônico + hash + eventos (uma transação)
  → relatório ou explicação por audit_id
```

`ClinicalDecisionOrchestrator` é a única agregação autorizada de status. CRITICAL ou hard block vence
qualquer indicação favorável; cobertura insuficiente nunca vira verde. Override é outro evento, não
reescrita da decisão: crítico/hard block é não-overrideable e aprovação exige segundo usuário.

## Segurança e consistência

O backend é a fonte real de autorização. Repositórios aplicam instituição, capacidade e relação clínica
ativa (grant, care team, episode ou break-glass) com finalidade explícita; rotas por ID retornam
404 quando o objeto não pertence ao escopo. Sessão usa cookie HttpOnly, login tem lockout persistente e
MFA TOTP opcional. Produção falha no startup com segredo demo, SQLite, auto-seed, CORS local ou
criptografia ausente para IA externa.

Checagem, audit e snapshot usam uma unidade de trabalho. Relatórios de prescrição não consultam o
cadastro vivo: verificam `sha256-canonical-json-v1` e leem apenas o snapshot imutável. Estado do circuit
breaker de IA fica no banco para ser compartilhado por workers.

## Limites

O projeto é educacional, sem validação clínica/regulatória. Não é FHIR, SMART ou CDS Hooks conforme;
os adapters são compatibilidade parcial. A busca lexical não é RAG validado. Infraestrutura produtiva,
OIDC/BFF, WORM, DLP, pentest, validação de rulesets e operação institucional continuam externas.
