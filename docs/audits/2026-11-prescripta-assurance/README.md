# Auditoria de assurance 2026-11

Início: 2026-11-08. Baseline `83d4beca06743fce30c242b71bc8425973083b38`. Escopo e método: auditoria
independente do repositório, revalidação dos achados PRE-01..12, triagem de Security/Dependabot e
dogfood com Derivanta Framework, Derivanta Engine e Assertiva.

Prescripta continua sendo uma demonstração sintética e educacional; nada aqui altera essa finalidade.

## Documentos

- [FINDINGS_REGISTER.md](FINDINGS_REGISTER.md) — registro mestre de achados, estado e evidência.
- [DEPENDABOT_PR_TRIAGE.md](DEPENDABOT_PR_TRIAGE.md) — decisão por PR do Dependabot e configuração.

Os demais documentos previstos (cobertura, arquitetura, segurança, Dependabot, UX, dogfood, relatório
final) são acrescentados conforme cada checkpoint é concluído; ausência significa "ainda não feito".

## Checkpoints publicados

| CP / slice | Escopo | Testes e resultados | SHA | Remote | Runs CI | Risco residual |
|---|---|---|---|---|---|---|
| CP-A | PRE-01, 02, 03, 04, 06, 09; Gitleaks; OpenAPI next | SQLite 298 passed / 3 skipped; PostgreSQL 17: scope 2/2, CDS+idade 22/22; ruff ok; OpenAPI compat ok; Gitleaks histórico 0 | [`e1f82e7`](https://github.com/Soturine/Prescripta/commit/e1f82e7bc9b8818648f262453c94319bf84e3279) | origin/main | CI [`42499758271`](https://github.com/Soturine/Prescripta/actions/runs/42499758271): repository-quality, backend ubuntu, frontend, frontend-visual, **postgres** ✓; backend Windows ✗ (NEW-07). Security [`42499758248`](https://github.com/Soturine/Prescripta/actions/runs/42499758248): secret-scan ✓ (antes ✗), CodeQL ✓, dependency ✗ (pré-existente). Container [`42499758273`](https://github.com/Soturine/Prescripta/actions/runs/42499758273) ✗ (pré-existente, PRE-10c) | dependências e imagens tratadas no CP-B |
| CP-B | PRE-10a/c, NEW-03/07/08; PRs #65, #66, #67; Dependabot config | backend 298 passed (lock novo); pip-audit 0; npm 0 high; Vitest 92/92 + cobertura; E2E 19 passed/2 skipped incl. visual+axe; smoke de containers OK; Trivy backend/frontend 0 | [`54614c0`](https://github.com/Soturine/Prescripta/commit/54614c04f42e1928ead82ed4d6d6805e0022ef7a) | origin/main | **Todos verdes**: CI [`42502107178`](https://github.com/Soturine/Prescripta/actions/runs/42502107178) (8/8 jobs incl. Windows, postgres, smoke, release-readiness), Security [`42502107207`](https://github.com/Soturine/Prescripta/actions/runs/42502107207) (4/4), Container [`42502107382`](https://github.com/Soturine/Prescripta/actions/runs/42502107382) | zlib aceito até 2026-11-22; #37/#39–#42 adiadas; Dependabot abriu #68–#70 |
| CP-C | PRE-05 revogação de sessão | backend 303 passed / 3 skipped; sessão 5/5 (4 falham sem o fix); Alembic round trip + check PG 17; E2E sessão 5/5; OpenAPI compat ok | [`5144d4e`](https://github.com/Soturine/Prescripta/commit/5144d4e) | origin/main | CI [`42502610730`](https://github.com/Soturine/Prescripta/actions/runs/42502610730), Security [`42502610718`](https://github.com/Soturine/Prescripta/actions/runs/42502610718), Container [`42502610711`](https://github.com/Soturine/Prescripta/actions/runs/42502610711): todos verdes | sem revogação global; CSRF continua via SameSite Lax |
| CP-D | NEW-04, NEW-06, NEW-10 (config) | backend 318 passed / 3 skipped; controles negativos dos três; literal/alternativas/sessão em PG 7/7 | (preenchido após o push) | origin/main | (preenchido após o push) | — |

## Bloqueios

- Instalar/executar Derivanta Engine e Assertiva a partir dos checkouts foi negado pelo classificador
  de permissões do ambiente. Dogfood real: BLOCKED até autorização explícita.
