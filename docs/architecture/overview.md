# Visão geral da arquitetura

O Prescripta é um monorepo com API FastAPI, aplicação React/TypeScript e persistência SQLAlchemy. PostgreSQL é o alvo operacional da stack Compose; SQLite e auto-seed existem apenas para desenvolvimento local e demonstração.

## Camadas

- `backend/app/domain`: contratos de domínio, decisões, dose, paciente e medicamento;
- `backend/app/services`: regras determinísticas, autorização, Research, Evidence e AI Task Router;
- `backend/app/repositories`: queries, paginação, instituição e escopo por objeto;
- `backend/app/reports`: EvidenceBundle, snapshot, PDF/JSON/CSV e narrativa controlada;
- `backend/app/integrations`: adapters demonstrativos, consentimento e reconciliação;
- `backend/migrations`: schema versionado por Alembic;
- `frontend/src`: shell responsivo, páginas, contratos, sessão e cliente HTTP;
- `frontend/src/i18n`: resolução de locale e catálogos PT-BR/EN-US;
- `docker-compose.yml`: PostgreSQL, migração one-shot, backend e frontend sem root.

## Fluxo de decisão

```text
request tipado
  → capacidade + instituição + relação/purpose por paciente
  → paciente/medicamento resolvidos no servidor
  → motores determinísticos + dose + psychotropic + policy
  → ClinicalDecisionEnvelope + coverage + abstention
  → snapshot canônico + hash + eventos na mesma transação
  → apresentação localizada, relatório ou explicação por audit_id
```

`ClinicalDecisionOrchestrator` é a agregação autorizada de status. CRITICAL ou hard block vence indicação favorável; cobertura insuficiente nunca vira verde. Override cria outro evento e não reescreve a decisão. Locale traduz apresentação, nunca valor canônico, unidade, código ou autorização.

## Runtime em containers

```text
navegador → nginx sem root :8080 → FastAPI sem root :8000 → PostgreSQL interno
                                      ↑
                                migrate one-shot
```

As imagens têm bases fixadas por digest e builds multi-stage. O runtime usa filesystem somente leitura, `tmpfs`, `cap_drop: ALL`, `no-new-privileges`, healthchecks e limites. A readiness não depende de provider de IA. O socket Docker não é montado nos serviços.

## Segurança e consistência

O backend é a fonte real de autorização. Sessão usa cookie HttpOnly; login tem lockout persistente e MFA TOTP opcional. Produção falha no startup com segredo demo, SQLite, auto-seed, CORS local ou criptografia ausente para IA externa. Relatórios verificam o hash do snapshot imutável. Estado do circuit breaker de IA fica no banco para compartilhamento entre workers.

## Três pilares

```text
Medication Safety       Research & RWE              Evidence Intelligence
regras determinísticas  protocolo/versionamento     fontes e vínculos
dose/workflows           cohort DSL + attrition      concept sets/provenance
decisão + snapshot       aggregates + snapshot       AI Task Router controlado
             └──────── JSON canônico, auditoria e autorização ────────┘
```

Research usa somente dados sintéticos, saída aggregate-first e definições revisadas imutáveis. IA propõe estruturas e explicações; nunca executa consulta, conta pacientes, modifica objeto ou decide validade.

## Limites

O projeto é educacional, sem validação clínica ou regulatória. Adapters têm compatibilidade parcial. Busca lexical não é RAG validado. OIDC/BFF, WORM, DLP, pentest, validação de rulesets, validade epidemiológica e operação institucional continuam externos.
