# Auditoria de assurance 2026-11

Início: 2026-11-08. Baseline `83d4beca06743fce30c242b71bc8425973083b38`. Escopo e método: auditoria
independente do repositório, revalidação dos achados PRE-01..12, triagem de Security/Dependabot e
dogfood com Derivanta Framework, Derivanta Engine e Assertiva.

Prescripta continua sendo uma demonstração sintética e educacional; nada aqui altera essa finalidade.

## Documentos

- [FINDINGS_REGISTER.md](FINDINGS_REGISTER.md) — registro mestre de achados, estado e evidência.

Os demais documentos previstos (cobertura, arquitetura, segurança, Dependabot, UX, dogfood, relatório
final) são acrescentados conforme cada checkpoint é concluído; ausência significa "ainda não feito".

## Checkpoints publicados

| CP / slice | Escopo | Testes e resultados | SHA | Remote | Runs CI | Risco residual |
|---|---|---|---|---|---|---|
| CP-A | PRE-01, 02, 03, 04, 06, 09; Gitleaks; OpenAPI next | SQLite 298 passed / 3 skipped; PostgreSQL 17: scope 2/2, CDS+idade 22/22; ruff ok; OpenAPI compat ok; Gitleaks histórico 0 | (preenchido após o push) | origin/main | (preenchido após o push) | pip-audit, npm audit e Trivy ainda falham (CP-B) |

## Bloqueios

- Instalar/executar Derivanta Engine e Assertiva a partir dos checkouts foi negado pelo classificador
  de permissões do ambiente. Dogfood real: BLOCKED até autorização explícita.
