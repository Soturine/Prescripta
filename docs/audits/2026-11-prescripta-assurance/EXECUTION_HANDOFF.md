# Estado de retomada da auditoria

Atualizado em 2026-11-08. Autocontido: retomar daqui sem refazer checkpoints publicados.

## Identidade

- Repositório: `Soturine/Prescripta`, branch `main`, push direto permitido (ruleset só bloqueia
  deleção e non-fast-forward). Autor local: `Soturine <souzaramos2001@gmail.com>`; sem co-autor de IA.
- Baseline da auditoria: `83d4beca06743fce30c242b71bc8425973083b38` (v1.0.0 + docs).
- Checkpoints publicados: A `e1f82e7`, B `54614c0`, C `5144d4e`, D `5315c4c`, E `3c20cde`,
  F `1c92ee8`, G `f016896`, H `4bd77bb` (CI/Security/Container verdes de B a G; H ver README).
- Ferramentas (checkouts irmãos, sem alterações): `Derivanta@218761d`,
  `Derivanta-Engine@17fa564`, `Assertiva@2618d95`.

## Ambiente local

- Python `.venv` do projeto (lock atual da PR #67 instalado); Node 24.11 / npm 11.6; Playwright 1.64.
- PostgreSQL descartável: container Docker `prescripta-audit-pg` (porta 55432, usuário
  `prescripta`, senha `prescripta_audit`), bancos `prescripta_audit` (migrado por Alembic até
  `b11a2c3d4e50`) e `prescripta_fullsuite`/`prescripta_ci_sim` (harness).
- Porta 8080 do host ocupada por NVIDIA Broadcast: rodar o smoke com
  `PRESCRIPTA_FRONTEND_PORT=8088` e cópia do script com `127.0.0.1:8088`.
- pytest precisa de `--basetemp` dentro do scratchpad (o diretório temporário padrão é negado).

## Comandos de gate usados

```text
backend:  ../.venv/Scripts/python -m pytest -q -p no:cacheprovider --basetemp=<scratch>
PG suite: PRESCRIPTA_TEST_DATABASE_URL=postgresql+psycopg://prescripta:prescripta_audit@localhost:55432/prescripta_fullsuite <mesmo pytest>
lint:     ../.venv/Scripts/python -m ruff check . --no-cache ; npm run lint ; npx tsc --noEmit
frontend: npx vitest run ; node ../scripts/check_i18n_catalogs.mjs
e2e:      PRESCRIPTA_PYTHON=<.venv python> npx playwright test
openapi:  python scripts/generate_openapi_snapshot.py --output docs/api/openapi-next.json ; python scripts/check_openapi_compatibility.py --config docs/api/openapi-policy.json
secrets:  docker run zricethezav/gitleaks:v8.24.3 git /repo --log-opts="<prev>..HEAD"
texto:    powershell -File scripts/check-text-quality.ps1
```

## Bloqueios (ver OPEN_BLOCKERS.md)

Instalação/execução de Derivanta Engine e Assertiva; merge/rebase de PRs Dependabot; habilitar
Dependabot alerts. Nunca contornar.

## Próximos passos

1. Release: decidir SemVer (mudança de sessão exige novo login; contrato CDS aditivo; nova migração
   `b11a2c3d4e50`) → atualizar `VERSION`, `CHANGELOG`, `docs/releases/`, `docs/release-policy.json`
   (sem mexer no baseline Alembic), rodar Qualification no SHA final, tag anotada, workflow de
   provenance, publicar draft só se autorizado. Com dogfood BLOCKED, preferir pré-release.
2. Revisão visual real em navegador (jornadas por perfil, mobile, EN-US) com capturas.
3. PRE-11: confrontar claims de release/README com runs reais.
4. Plano/índice de `json_array_contains` em PostgreSQL; supressão de células pequenas no Research.
5. Reconsultar PRs Dependabot (#68–#70 e majors).
