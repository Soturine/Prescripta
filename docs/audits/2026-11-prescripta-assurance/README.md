# Auditoria de assurance 2026-11

Início: 2026-11-08. Baseline `83d4beca06743fce30c242b71bc8425973083b38`. Escopo e método: auditoria
independente do repositório, revalidação dos achados PRE-01..12, triagem de Security/Dependabot e
dogfood com Derivanta Framework, Derivanta Engine e Assertiva.

Prescripta continua sendo uma demonstração sintética e educacional; nada aqui altera essa finalidade.

## Documentos

- [FINDINGS_REGISTER.md](FINDINGS_REGISTER.md) — registro mestre de achados, estado e evidência.
- [DEPENDABOT_PR_TRIAGE.md](DEPENDABOT_PR_TRIAGE.md) — decisão por PR do Dependabot e configuração.
- [AUDIT_FINDING_CROSSWALK.md](AUDIT_FINDING_CROSSWALK.md) — mapeamento dos IDs da auditoria original para este registro.
- [EXTERNAL_BENCHMARK_DECISIONS.md](EXTERNAL_BENCHMARK_DECISIONS.md) — Tasy, alertas Anvisa, CDS Hooks e decisões de posicionamento.
- [DOGFOOD_MATRIX.md](DOGFOOD_MATRIX.md) — estado real do dogfood e log agent-led.
- [dogfood/](dogfood/) — [RUN_MANIFEST.json](dogfood/RUN_MANIFEST.json) (comandos, versões, SHAs,
  exit codes, hashes dos relatórios originais), [MUTATION_CONTROL.md](dogfood/MUTATION_CONTROL.md),
  [TOOL_FEEDBACK.md](dogfood/TOOL_FEEDBACK.md) e
  [DERIVANTA_FRAMEWORK_FEEDBACK.md](dogfood/DERIVANTA_FRAMEWORK_FEEDBACK.md).
- [EXECUTION_HANDOFF.md](EXECUTION_HANDOFF.md) — estado de retomada.
- [UI_UX_ACCESSIBILITY_AUDIT.md](UI_UX_ACCESSIBILITY_AUDIT.md) — revisão de UI/UX desta rodada e limites.
- [OPEN_BLOCKERS.md](OPEN_BLOCKERS.md) — ações bloqueadas por permissão e o que as destrava.
- [DUPLICATION_DEAD_CODE_AND_LEGACY.md](DUPLICATION_DEAD_CODE_AND_LEGACY.md) — candidatos a código morto/duplicado e decisão.

Os demais documentos previstos (cobertura, arquitetura, segurança, Dependabot, UX, dogfood, relatório
final) são acrescentados conforme cada checkpoint é concluído; ausência significa "ainda não feito".

## Checkpoints publicados

| CP / slice | Escopo | Testes e resultados | SHA | Remote | Runs CI | Risco residual |
|---|---|---|---|---|---|---|
| CP-A | PRE-01, 02, 03, 04, 06, 09; Gitleaks; OpenAPI next | SQLite 298 passed / 3 skipped; PostgreSQL 17: scope 2/2, CDS+idade 22/22; ruff ok; OpenAPI compat ok; Gitleaks histórico 0 | [`e1f82e7`](https://github.com/Soturine/Prescripta/commit/e1f82e7bc9b8818648f262453c94319bf84e3279) | origin/main | CI [`42499758271`](https://github.com/Soturine/Prescripta/actions/runs/42499758271): repository-quality, backend ubuntu, frontend, frontend-visual, **postgres** ✓; backend Windows ✗ (NEW-07). Security [`42499758248`](https://github.com/Soturine/Prescripta/actions/runs/42499758248): secret-scan ✓ (antes ✗), CodeQL ✓, dependency ✗ (pré-existente). Container [`42499758273`](https://github.com/Soturine/Prescripta/actions/runs/42499758273) ✗ (pré-existente, PRE-10c) | dependências e imagens tratadas no CP-B |
| CP-B | PRE-10a/c, NEW-03/07/08; PRs #65, #66, #67; Dependabot config | backend 298 passed (lock novo); pip-audit 0; npm 0 high; Vitest 92/92 + cobertura; E2E 19 passed/2 skipped incl. visual+axe; smoke de containers OK; Trivy backend/frontend 0 | [`54614c0`](https://github.com/Soturine/Prescripta/commit/54614c04f42e1928ead82ed4d6d6805e0022ef7a) | origin/main | **Todos verdes**: CI [`42502107178`](https://github.com/Soturine/Prescripta/actions/runs/42502107178) (8/8 jobs incl. Windows, postgres, smoke, release-readiness), Security [`42502107207`](https://github.com/Soturine/Prescripta/actions/runs/42502107207) (4/4), Container [`42502107382`](https://github.com/Soturine/Prescripta/actions/runs/42502107382) | zlib aceito até 2026-11-22; #37/#39–#42 adiadas; Dependabot abriu #68–#70 |
| CP-C | PRE-05 revogação de sessão | backend 303 passed / 3 skipped; sessão 5/5 (4 falham sem o fix); Alembic round trip + check PG 17; E2E sessão 5/5; OpenAPI compat ok | [`5144d4e`](https://github.com/Soturine/Prescripta/commit/5144d4e) | origin/main | CI [`42502610730`](https://github.com/Soturine/Prescripta/actions/runs/42502610730), Security [`42502610718`](https://github.com/Soturine/Prescripta/actions/runs/42502610718), Container [`42502610711`](https://github.com/Soturine/Prescripta/actions/runs/42502610711): todos verdes | sem revogação global; CSRF continua via SameSite Lax |
| CP-D | NEW-04, NEW-06, NEW-10 (config) | backend 318 passed / 3 skipped; controles negativos dos três; literal/alternativas/sessão em PG 7/7 | [`5315c4c`](https://github.com/Soturine/Prescripta/commit/5315c4c) | origin/main | CI [`42503272737`](https://github.com/Soturine/Prescripta/actions/runs/42503272737), Security [`42503272821`](https://github.com/Soturine/Prescripta/actions/runs/42503272821), Container [`42503272686`](https://github.com/Soturine/Prescripta/actions/runs/42503272686): todos verdes | — |
| CP-E | PRE-08 código morto; sondas NL→SQL | backend e Vitest 92/92 verdes; tsc e lint ok | [`3c20cde`](https://github.com/Soturine/Prescripta/commit/3c20cde) | origin/main | CI/Security/Container verdes (`42503672390`, `42503672389`, `42503672335`) | PRE-07 DEFERRED |
| CP-F | NEW-11 alternativas, NEW-12 CDS, ADR 010/011, crosswalk | backend 322 passed / 3 skipped; Vitest 94; E2E 19/2 incl. visual; controles negativos | [`1c92ee8`](https://github.com/Soturine/Prescripta/commit/1c92ee8) | origin/main | CI/Security/Container verdes | política de idade pendente de revisão clínica |
| CP-G | NEW-13–17: exibição de dose, concentração, sessão multi-aba, testes de negação; benchmark Tasy/Anvisa; dogfood matrix | backend 345 passed / 3 skipped; Vitest 98; E2E 19/2; controles negativos | [`f016896`](https://github.com/Soturine/Prescripta/commit/f016896) | origin/main | CI `42506699421`, Security `42506699408`, Container `42506699388`: verdes | dogfood BLOCKED |
| CP-H | PRE-04 concorrência real em PG; NEW-05 harness PG completo; CI PG ampliado | SQLite 346/5 skipped; PostgreSQL suíte inteira 348/0/3; simulação do step de CI 28/28 | [`4bd77bb`](https://github.com/Soturine/Prescripta/commit/4bd77bb) | origin/main | CI `42508296009` (incl. novo step PG), Security `42508296098`, Container `42508295956`: verdes | — |
| CP-I | NEW-18 índice, NEW-19 evidência de release, handoff | SQLite 350/5; Alembic round trip PG; EXPLAIN | [`5ae81d9`](https://github.com/Soturine/Prescripta/commit/5ae81d9) | origin/main | CI `42508809961`, Security `42508809873`, Container `42508810071`: verdes | — |
| CP-J | NEW-20 alternativas absurdas (achado em navegador real); revisão UI/UX | backend 351/5; Vitest 98; E2E 19/2; i18n 877 | [`0d23f1e`](https://github.com/Soturine/Prescripta/commit/0d23f1e) | origin/main | CI `42509403848`, Security `42509403923`, Container `42509403958`: verdes | leitor de tela e demais perfis não revisados |
| CP-K | Dogfood real (Engine, Assertiva, Framework), mutação agent-led (NEW-23/24/25, ADR 012), acessibilidade por perfil (NEW-27/28/29), MFA (NEW-21), código morto confirmado pelo Engine | Árvore final: SQLite 368 passed / 5 skipped (exit 0); PostgreSQL 17 370 passed / 3 skipped (exit 0, JUnit 373); Vitest 98/98; E2E 27 passed / 2 skipped; gates de repositório verdes; Gitleaks 0 | `75b19ea`, `14f9be1`, `129dd29`, `a18e081` + docs | origin/main (`e80ee70`) | CI `42533288573`, Security `42533288696`, Container `42533288543`: verdes | leitor de tela real não testado; mutação nativa da Assertiva não executada (execução nativa do backend resolvida depois, `45e80d5`, run `e6e0bad61f71427f`) |

## Bloqueios

Ver [OPEN_BLOCKERS.md](OPEN_BLOCKERS.md). O bloqueio de instalação das ferramentas foi resolvido em
2026-11-08 por regra de permissão escolhida pelo usuário; o dogfood foi executado.

## Fechamento (CP-L): classificação das pendências

Escopo congelado nos checkpoints A–K. Nada abaixo é corrigido nesta versão.

| Classe | Item | Onde está declarado |
|---|---|---|
| Bloqueante para a v1.1.0 | Nenhum item de produto. Só os quatro gates (CI, Security, Container, Qualification) no SHA final. | release notes |
| Limitação conhecida | Sem validação clínica profissional; teto de idade (ADR 010) e ausência de teto de concentração pendentes de especialista | release notes, ADR 010 |
| Limitação conhecida | MFA verificado no login, sem fluxo de cadastro (NEW-21) | release notes, `docs/security/authentication-and-roles.md` |
| Limitação conhecida | Acessibilidade verificada com axe e estrutura em Chromium; sem leitor de tela real nem zoom 200/400 % | release notes, UI/UX audit |
| Limitação conhecida | Ferramentas rodaram em revisões da auditoria, não no SHA final; Assertiva sem PostgreSQL provisionado e sem mutação nativa (Cosmic Ray); mutação feita manualmente pelo agente | release notes, DOGFOOD_MATRIX |
| Limitação conhecida | Exceção Trivy zlib com vencimento em 2026-11-22; Dependabot alerts desabilitados (admin) | release notes, `docs/security/accepted-risks.md` |
| Limitação conhecida | Backend sozinho, fora do monorepo, depende de `VERSION` da raiz (NEW-22) | FINDINGS_REGISTER |
| Backlog | PRs Dependabot #68–#70 (merge do mantenedor), majors #37, #39–#42 | DEPENDABOT_PR_TRIAGE |
| Backlog | 28 candidatos sem referência textual; PRE-07 (arquivos grandes) | DUPLICATION_DEAD_CODE_AND_LEGACY |
| Backlog (ferramentas) | Assertiva: PRs das branches AS-02 e AS-07; AS-03, 04, 05, 06, 08, 09, 10. Engine: ENG-02 a 06. Framework: DF-002, DF-003 | dogfood/TOOL_FEEDBACK, dogfood/DERIVANTA_FRAMEWORK_FEEDBACK |
