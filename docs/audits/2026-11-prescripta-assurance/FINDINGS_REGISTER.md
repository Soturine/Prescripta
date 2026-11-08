# Registro de achados — auditoria 2026-11

Baseline: `main` @ `83d4beca06743fce30c242b71bc8425973083b38` (v1.0.0 + docs). Ambiente: Windows 10,
Python 3.12.6 (`.venv`), Node 24.11.1 / npm 11.6.2, PostgreSQL 17-alpine descartável em Docker.

Estados: `NEW`, `IN_PROGRESS`, `FIXED` (corrigido, teste local), `VERIFIED` (corrigido + controle
negativo + gate relevante), `DEFERRED`, `FALSE_POSITIVE`, `BLOCKED`, `UNKNOWN`. Níveis de evidência:
OBSERVED / REPRODUCED / VERIFIED / INFERRED / NOT_EXECUTED.

## Achados originais (PRE)

| ID | Tipo | Sev. | Estado | Causa confirmada | Evidência | Teste / controle negativo |
|---|---|---|---|---|---|---|
| PRE-01 | bug | alta | VERIFIED (local) | `RiskEngine` elevava +1 nível para ≥65, o orquestrador recalculava `max(findings)` e descartava a elevação; no próprio motor, `elderly_caution` recalculava `max(alerts)` e **reduzia** CRITICAL→HIGH (não monotônico). | REPRODUCED: tabela 18 cenários (idade 64/65/70 × base × cautela) antes/depois. Ex.: 65/baixo: motor `moderado` × orquestrador `baixo`; 65/alto: `critico/bloqueado` sem cautela, `alto/atencao` com cautela. | `tests/test_age_risk_composition.py` (Hypothesis: monotonicidade e +1 com teto; paridade motor×orquestrador). Sem o fix do orquestrador: 3 falhas. |
| PRE-02 | bug | alta | VERIFIED (local) | Com >1 cadastro para o termo, a rota escolhia o menor ID se compartilhassem `active_ingredient_id`. | REPRODUCED com duas apresentações (100 mg / 500 mg). | `test_ambiguous_presentations_fail_closed_with_candidates` falha no baseline. |
| PRE-03 | bug (contrato enganoso) | alta | VERIFIED (local) | `observations` aceito e só contado na auditoria. | OBSERVED no código; nenhuma interpretação adicionada (sem semântica clínica validada). | `test_observations_are_declared_not_evaluated` falha no baseline; lista limitada a 100. |
| PRE-04 | bug | média/alta | VERIFIED (SQLite + PostgreSQL 17) | Consulta-depois-insere sem tratar `IntegrityError`; além disso `AuditService` com `auto_commit=True` confirmava a auditoria antes do insert idempotente → 500 com auditoria órfã. | REPRODUCED inserindo a linha concorrente na janela entre consulta e insert. | `test_idempotency_race_replays_or_conflicts_without_orphan_audit[True/False]` falham no baseline; passam em SQLite e PostgreSQL. Concorrência multi-thread real: NOT_EXECUTED. |
| PRE-05 | risk | média | IN_PROGRESS | — | — | — |
| PRE-06 | bug (authz/disponibilidade) | **alta** (reclassificada) | VERIFIED (SQLite + PostgreSQL 17) | `JSON.contains()` compila para `LIKE '%x%'`: substring no SQLite; no PostgreSQL `json ~~ text` não existe. | REPRODUCED: `GET /api/patients` como médico em PostgreSQL → **500**; após o fix → 200. SQLite listava pacientes com `patient.read.extra`, `xpatient.read` e JSON escalar. | `tests/test_object_scope_json_membership.py` (lista ≡ checagem por objeto, 7 casos, 2 dialetos); sem o fix: SQLite `{1,2,3,4,7} != {1,7}`, PG `UndefinedFunction`. Adicionado ao job `postgres` do CI. |
| PRE-07 | debt | média | NEW | — | — | — |
| PRE-08 | debt | baixa | NEW | — | — | — |
| PRE-09 | doc drift | média | VERIFIED (local) | Doc citava perfis; rota exige `prescription.check` (medicine, nursing, pharmacy). | OBSERVED. Nenhuma permissão adicionada ao admin. | `tests/test_cds_docs_matrix.py`; falha quando a doc diverge. |
| PRE-10a | supply chain | alta | IN_PROGRESS | pip-audit: 24 registros / 5 pacotes; `PYSEC-2026-4146` (PyJWT) sem versão de correção. | REPRODUCED localmente (pip-audit 2.10.1). | — |
| PRE-10b | false positive | — | FALSE_POSITIVE (VERIFIED) | Valores sintéticos `fhir-idempotency-1`, `test-test-test`, `break-uow-v088` (doc). | Gitleaks 8.24.3 histórico completo: 3 achados → 0 com 3 fingerprints exatos; controle sem eles: 3. | — |
| PRE-10c | risk | alta | IN_PROGRESS | Exceção CVE-2026-14456 expirada em 2026-09-07; Trivy bloqueia o Container. | OBSERVED no run do PR #67. | — |
| PRE-11 | doc/gate drift | média | IN_PROGRESS | ver NEW-01. | — | — |
| PRE-12 | hipóteses | — | IN_PROGRESS | ver itens individuais quando confirmados. | — | — |

## Achados novos

| ID | Tipo | Sev. | Estado | Descrição | Evidência |
|---|---|---|---|---|---|
| NEW-01 | risk (gate ignorado) | alta | OBSERVED | O Security **agendado** falha toda semana desde 2026-08-10 (13 runs seguidos), inclusive antes da release v1.0.0. `secret-scan` só varre o histórico completo no `schedule`; push/PR varrem o intervalo novo. | `gh run list --workflow Security --event schedule`: último sucesso 2026-08-03 (`30798477141`). |
| NEW-02 | bug de gate | alta | FIXED | `gitleaks-action` v3 exige `GITHUB_TOKEN` em PRs; o secret-scan falhava em todo PR sem varrer nada. | Run `41435117076`: "GITHUB_TOKEN is now required to scan pull requests". |
| NEW-03 | risk (falha mascarada) | alta | IN_PROGRESS | `npm audit` do frontend tem 6 HIGH (axios, zod em runtime; vite, brace-expansion, source-map-js, follow-redirects em build/node) mas o job agendado parava antes, no pip-audit. | npm audit local: 13 moderate / 6 high. |
| NEW-04 | bug (latente) | baixa | NEW | `AlternativeService._candidates` usa `repository.list()` com `limit=50` padrão: alternativas ignoram cadastros além dos 50 primeiros por nome. | OBSERVED no código. |
| NEW-05 | debt (harness) | média | FIXED | A suíte backend só roda em SQLite; nenhum teste de autorização rodava em PostgreSQL. `PRESCRIPTA_TEST_DATABASE_URL` (opt-in) roda a suíte inteira em PostgreSQL. | PG: 279 passed / 2 failed / 3 skipped; as 2 falhas são do harness (view `research_aggregate_comparisons` só existe via Alembic). |
| NEW-06 | debt | baixa | NEW | `audit_repository` usa `ilike(f"%{x}%")` sem escapar `%`/`_` do filtro do usuário (curinga, não injeção). | OBSERVED. |

## Decisões que exigem revisão humana

- PRE-01: teto `alto` para elevação apenas por idade. Antes, o motor base podia bloquear (CRITICAL)
  por idade; o caminho principal (orquestrador) nunca bloqueava. A decisão aumenta o nível em todos
  os casos não críticos do caminho principal e remove o bloqueio por idade isolada do caminho de
  alternativas. Constante `AGE_ELEVATION_CEILING` em `risk_engine.py`.
