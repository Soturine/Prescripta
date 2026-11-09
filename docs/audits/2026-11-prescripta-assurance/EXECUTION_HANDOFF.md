# Estado de retomada da auditoria

Atualizado em 2026-11-08. Autocontido: retomar daqui sem refazer checkpoints publicados.

## Identidade

- Repositório: `Soturine/Prescripta`, branch `main`, push direto permitido (ruleset só bloqueia
  deleção e non-fast-forward). Autor local: `Soturine <souzaramos2001@gmail.com>`; sem co-autor de IA.
- Baseline da auditoria: `83d4beca06743fce30c242b71bc8425973083b38` (v1.0.0 + docs).
- Checkpoints publicados: A–J (ver README) e preparação da candidata `6508221`; CP-K (dogfood real,
  mutação, acessibilidade por perfil) ver README.
- Ferramentas (checkouts irmãos): `Derivanta@218761d` (sem alteração); `Derivanta-Engine` em
  `d413e53` (`origin/main`, correção ENG-01); `Assertiva` em `2618d95` no `main` e correção AS-02 na
  branch `fix/dogfood-prescripta-collect-cause` (`9885dde`, sem PR nem merge).
- Venvs das ferramentas: `../Derivanta-Engine/.venv`, `../Assertiva/.venv` (o venv da Assertiva não
  tem o extra de desenvolvimento completo; `coverage` foi instalado à parte). Regras de permissão em
  `.claude/settings.local.json` (ignorado pelo Git).
- Evidência bruta do dogfood: fora do repositório, em `../Prescripta-audit-evidence/2026-11-08/`
  (hashes em `dogfood/RUN_MANIFEST.json`).

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

Merge das PRs Dependabot (classificador); Dependabot alerts (admin); `assertiva --mutate` e Playwright
via Assertiva. Nunca contornar.

## Próximos passos

1. Release (só depois do dogfood e da auditoria): qualificar o SHA final (CI, Security, Container,
   Qualification), conferir SBOM, checksums, provenance e exceções vigentes (zlib vence em
   2026-11-22), tag anotada e GitHub Release. Até lá a v1.1.0 é candidata não publicada.
2. Backlog depois da v1.1.0 (não bloqueia): ver a classificação de pendências no README da
   auditoria (CP-L).
