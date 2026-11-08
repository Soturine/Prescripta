# Triagem das PRs do Dependabot — 2026-11-08

Inventário reconsultado em 2026-11-08 (`gh pr list`): as mesmas oito PRs, nenhuma nova. Todas
`MERGEABLE`. A integração foi feita por commit controlado em `main` (PRs agrupadas conflitam
textualmente com edições de workflow da auditoria); cada linha aponta a PR de origem.

| PR | Objeto | Decisão | Motivo e prova |
|---:|---|---|---|
| [#67](https://github.com/Soturine/Prescripta/pull/67) | 45 updates Python (patch/minor), incl. FastAPI 0.141→0.162, SQLAlchemy 2.0→2.1, Pydantic 2.13→2.14, PyJWT 2.13→2.15.1, httpx2/httpcore2 2.9→2.16, certifi, dnspython | **INTEGRADA** (lockfiles copiados da branch da PR) | pip-audit 2.10.1 no lock da PR: **0** (antes: 24 registros/5 pacotes, incluindo `PYSEC-2026-4146` sem versão de correção listada). Suíte backend em venv isolado: 298 passed / 3 skipped (igual ao baseline corrigido). O CI da PR falhou apenas porque o snapshot OpenAPI mudou: Pydantic 2.14 deixou de emitir `pattern` em campos Decimal-string (34 linhas; documentação de schema, sem mudança de validação runtime; gate de compatibilidade sem quebras). Também sobe `packaging` para 26.3, o que resolve a falha do job Windows (pipx da imagem do runner exige ≥26.3). |
| [#65](https://github.com/Soturine/Prescripta/pull/65) | 19 updates npm (patch/minor), incl. axios 1.20.0, zod 4.6.7, React 19.3, Playwright 1.64 | **INTEGRADA** + `npm audit fix` não-breaking | Remove os HIGH de runtime **axios** e **zod**. `npm audit fix` (sem `--force`) corrigiu os HIGH restantes de build (vite 7.3.7, brace-expansion, source-map-js, follow-redirects). Resultado: 0 high/critical, 13 moderate de tooling (eslint/typescript-eslint/vitest) cujas "correções" sugeridas são *downgrades* major — não aplicadas. Playwright 1.64 deixa de aninhar `fsevents@2.3.2`; a política de install scripts foi **reduzida** (entrada removida). Gates: build, lint 0 warnings, Vitest 92/92 + cobertura, i18n, CDP, E2E 19 passed / 2 skipped incluindo `@visual` (Windows, sem atualizar snapshots) e axe. |
| [#66](https://github.com/Soturine/Prescripta/pull/66) | setup-python 7.1.0, setup-node 7.1.0, upload-artifact 7.0.2, codeql-action 4.39.1 | **INTEGRADA** (substituição dos SHAs) | Cada SHA conferido contra a tag de release via API do GitHub: 5/5 coincidem. Diff aplicado idêntico ao da PR (contagem por action). |
| [#41](https://github.com/Soturine/Prescripta/pull/41) | vite 7 → 8 | **DEFERRED** | Major. O HIGH do vite foi resolvido em 7.3.7. Exige validar plugin-react 6 junto (#40); sem ganho de segurança imediato. |
| [#40](https://github.com/Soturine/Prescripta/pull/40) | @vitejs/plugin-react 5 → 6 | **DEFERRED** | Peer exige `vite ^8`; acoplada a #41. |
| [#39](https://github.com/Soturine/Prescripta/pull/39) | typescript 5.9 → 7.0 | **BLOCKED** | `typescript-eslint` declara peer `typescript >=4.8.4 <6.1.0`; lint quebraria. Aguardar suporte upstream. |
| [#42](https://github.com/Soturine/Prescripta/pull/42) | lucide-react 0.562 → 1.30 | **DEFERRED** | Major de biblioteca de ícones usada em toda a navegação; exige revisão visual completa e não traz correção de segurança. |
| [#37](https://github.com/Soturine/Prescripta/pull/37) | websockets 16 → 17 | **DEFERRED** | Não é superada por #67 (que mantém 16.0). Dependência transitiva de `uvicorn[standard]`; o app não tem rotas WebSocket. Boot com 17.0.1 testado: health 200, sem avisos. Sem correção de segurança; baixo valor. |

As PRs integradas serão fechadas pelo Dependabot ao detectar as versões em `main`; as DEFERRED/BLOCKED
permanecem abertas como lembrete.

## Configuração (`.github/dependabot.yml`)

Problema observado: um único grupo `"*"` por ecossistema junta correções de segurança com dezenas
de upgrades. Em #67, o snapshot OpenAPI (FastAPI) manteve o patch do PyJWT parado desde 2026-11-02.
Além disso, **Dependabot alerts e security updates estão desabilitados** no repositório (API: 403
"Dependabot alerts are disabled"; `automated-security-fixes.enabled=false`).

Alteração: grupos `*-security` (`applies-to: security-updates`) separados de `*-compatible`
(`applies-to: version-updates`). Só têm efeito quando alerts/security updates forem habilitados —
decisão de configuração do repositório, pendente do mantenedor.

## PRs abertas após a integração (2026-11-08)

O Dependabot fechou #65, #66 e #67 como superadas e abriu, sobre `54614c0`:

| PR | Objeto | Recomendação | Evidência |
|---:|---|---|---|
| [#68](https://github.com/Soturine/Prescripta/pull/68) | codeql-action 4.39.1 → 4.39.3 | **MERGE** | SHA `33d7b85…` conferido contra a tag v4.39.3; CI da PR totalmente verde (incl. release-readiness). |
| [#69](https://github.com/Soturine/Prescripta/pull/69) | 10 npm patch/minor (axios 1.21, i18next, react-router-dom 7.18.5, tailwind 4.3.4, eslint 10.14…) | **MERGE após rebase** | CI da PR verde nos jobs concluídos; construída antes de `5144d4e`. |
| [#70](https://github.com/Soturine/Prescripta/pull/70) | 10 Python patch/minor (SQLAlchemy 2.1.8, Pydantic 2.14.3, psycopg 3.3.8…) | **MERGE após rebase** | CI da PR verde; Pydantic pode alterar o snapshot OpenAPI, por isso rebase antes do merge. |

O merge destas PRs pelo agente foi **bloqueado pelo classificador de permissões** do ambiente
("merge without review"); a decisão fica com o mantenedor. O fix do secret-scan em PRs (NEW-02) foi
confirmado remotamente: `secret-scan=SUCCESS` nas três.
