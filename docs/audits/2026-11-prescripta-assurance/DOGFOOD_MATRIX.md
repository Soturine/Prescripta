# Dogfood Derivanta / Engine / Assertiva — matriz e log agent-led

Execução real em 2026-11-08, feita pelo agente com as CLIs instaladas em venv próprio de cada
checkout (autorização por regra de permissão local adicionada a pedido do usuário). Cada linha abaixo
tem comando, versão, SHA e exit code em [dogfood/RUN_MANIFEST.json](dogfood/RUN_MANIFEST.json); os
relatórios originais (HTML/JSON) ficam fora do repositório público, por conterem caminhos locais, com
SHA-256 de cada arquivo no manifesto.

Versões: Derivanta Framework `218761d`; Derivanta Engine 0.1.0 (`17fa564` → correção `3958b84` +
`d413e53`, publicada em `main`, CI `42529300375` verde, incluindo Linux); Assertiva 0.10.1
(`2618d95` → correção `76f2370` + `9885dde`, branch `fix/dogfood-prescripta-collect-cause`, CI
`42529304020` verde; **sem PR, sem merge e sem release**: CI verde da branch não equivale a entrega).

## Estado por célula

| Alvo | Agente + Framework | Derivanta Engine (CLI) | Assertiva (CLI) |
|---|---|---|---|
| Prescripta | **EXECUTED** (AUDIT.md, ADAPTIVE_TEST_ASSURANCE, mutação manual) | **EXECUTED**: `inspect --maintainability` em `83d4bec`, `6508221`, `14f9be1` (original e corrigido); `compare 6508221→14f9be1`; `evaluate` com `--framework` e `--repository` | **EXECUTED**: estático; `--execute` raiz (FAIL de coleta), backend (BLOCKED), frontend (Vitest PASS 98/98, Playwright BLOCKED); evidência importada (JUnit + coverage); controle negativo de CI de outra revisão; reexecução com a correção; **com `pytest.ini` na raiz (`45e80d5`): execução nativa do backend `ENGINE_EXECUTED` PASS, 368 passed / 0 errors / 5 skipped, linhas 89,1 %, ramos 67,1 %** (run `e6e0bad61f71427f`, com `PYTEST_ADDOPTS=--basetemp` declarado no manifesto) |
| Derivanta Engine | lido (AGENTS, regras 1–8) | **EXECUTED** em si mesma (`inspect --maintainability`, gate: lint, format, mypy, conformance 20/20, suíte 944/4) | **EXECUTED**: estático (run `01fa0870329d4b2d`); `--execute` 1º run caiu na limpeza do temporário (AS-07), 2º run `d89a95c89e5d4c23`: 225 erros atribuídos à pasta temporária do sandbox (infraestrutura), cobertura de ramos 69,9 %, artefato FAIL por falso positivo de extra opcional (AS-08) |
| Assertiva | lido (CONTRIBUTING, CHANGELOG) | **EXECUTED** (`inspect --maintainability`, 256 candidatos) | suíte própria executada (ver TOOL_FEEDBACK AS-06) |
| Derivanta Framework | **EXECUTED** (workflow AUDIT aplicado; feedback em [DERIVANTA_FRAMEWORK_FEEDBACK.md](dogfood/DERIVANTA_FRAMEWORK_FEEDBACK.md)) | pin verificado pelo `evaluate --framework` (EXECUTED/PASSED `218761dbd7ce`) | não aplicável (sem suíte executável no checkout) |

## O que cada ferramenta encontrou no Prescripta e o que o agente decidiu

| Origem | Achado da ferramenta | Classificação do agente | Efeito no Prescripta |
|---|---|---|---|
| Engine `inspect` | 182 definições sem referência em `6508221` | 142 falsos positivos (rotas FastAPI, listeners SQLAlchemy, `@compiles`, registrados pelo decorador); 40 sem referência textual confirmada pelo agente | 11 definições removidas em `14f9be1` (8 de `core/constants.py`, `MASS_TO_MG`, `VOLUME_TO_ML`, `require_roles`); `encrypt_mfa_secret` saiu da lista só porque os testes novos o referenciam; 28 restantes classificados um a um em [DUPLICATION_DEAD_CODE_AND_LEGACY.md](DUPLICATION_DEAD_CODE_AND_LEGACY.md) |
| Engine `inspect` (corrigido) | 170 → 28 candidatos no mesmo escopo | os 28 não têm referência textual (confirmado pelo agente), o que **não** prova código morto: há API de integração, modelo de tabela e itens UNKNOWN; nenhum candidato verdadeiro perdido pela correção | correção da ferramenta (ENG-01) |
| Engine, conhecido de antemão | não acusou `calculate_daily_dose` (só usado em teste) nem `knowledge/normalizer.py` (módulo só de re-export) | **falsos negativos** por contrato (ENG-02, ENG-03) | removidos por decisão do agente |
| Engine `compare` | `6508221→14f9be1`: NEW 0, PERSISTING 331, ABSENT 14 | correto; 1 ABSENT (`encrypt_mfa_secret`) só porque os testes novos passaram a referenciá-lo | — |
| Engine `evaluate` | C4 "validado" sem evidência | verdadeiro positivo | nenhuma alegação de validação clínica |
| Engine `evaluate` | não acusou que C1 cita CI de `6508221` com HEAD observado `14f9be1` | **falso negativo** (ENG-04); a Assertiva acusou | evidência por SHA reforçada no handoff |
| Assertiva estático | WEAK_ORACLE, ERROR_STATUS_ONLY, STATE_AFTER_REJECTION_NOT_EVIDENCED | sinais E3 corretos; os 3 testes fortalecidos antes (NEW-17) não aparecem | confirma NEW-17; hipótese AS-01 antiga resolvida (já detectado) |
| Assertiva `--execute` raiz | FAIL: `backend/tests` não coletado | verdadeiro para o projeto: o monorepo só rodava a partir de `backend/`; antes da correção o relatório não dizia a causa (AS-02) | `pytest.ini` na raiz com caminhos relativos (`45e80d5`): coleta e execução nativas passaram (373 invocações) |
| Assertiva `--execute` raiz, após `pytest.ini` | 6 erros `PermissionError` atribuídos ao **produto** | falso positivo de origem (AS-09): o erro nasce no próprio pytest, no `.venv` dentro do projeto, ao criar `tmp_path` na pasta temporária negada pelo sandbox; com `--basetemp` fora da cópia: 0 erros | nenhum |
| Assertiva `--execute` backend | BLOCKED: `VERSION` não encontrado | **verdadeiro**: backend não é autocontido (NEW-22) | registrado |
| Assertiva importado | 368 casos PASS, rotulados "não executados pela Assertiva" | correto | — |
| Assertiva `--ci-run` | CI de `6508221` com HEAD `14f9be1` → `OTHER_REVISION` + `CI_RUN_FOR_ANOTHER_REVISION` | controle negativo **aprovado** | — |
| Agente: mutação manual | 6 mutantes no `risk_engine`, 5 no orquestrador; sobreviventes reexecutados contra a suíte inteira; compostos "todos os caminhos" | ver [dogfood/MUTATION_CONTROL.md](dogfood/MUTATION_CONTROL.md) | NEW-23, NEW-24 corrigidos com testes que falham antes; NEW-25 aberto |

Mutação nativa da Assertiva (`--mutate`) segue **BLOCKED**: a coleta nativa agora funciona, mas o
Cosmic Ray não está instalado no ambiente do projeto e instalá-lo está fora dos comandos autorizados. O controle de mutação foi feito manualmente pelo agente em
worktree descartável, declarado como tal.

## Log agent-led (Framework)

| Orientação aplicada | Decisão concreta e efeito verificável |
|---|---|
| AUDIT §13: desafio materialmente distinto para achado de alto impacto | Sobreviventes de mutação não viraram achado direto: reexecução contra a suíte inteira e, depois, mutantes compostos que removem todos os caminhos de um bloqueio. Isso separou guardas redundantes (O1, O3: equivalentes) de lacunas reais (P1, O5). |
| AUDIT §15: proposta ≠ implementado ≠ verificado | NEW-25 fica PROPOSED; ENG-02..06 e AS-03..06 ficam como propostas, sem alteração nas ferramentas. |
| ADAPTIVE_TEST_ASSURANCE: descobertos ≠ executados ≠ sustentam a alegação | Evidência importada rotulada como importada; runs da Assertiva com runtime `dirty=True` declarados. |
| Framework feedback depois do alvo | Feedback ao Framework escrito depois do registro de achados, sem envio upstream. |
| CONTEXT/TEST: "coletor que falhou → BLOCKED, nunca PASS" | Playwright BLOCKED e backend BLOCKED não foram contados como verde; o E2E segue evidenciado pelo CI e pela execução local direta. |

Feedback detalhado às ferramentas: [dogfood/TOOL_FEEDBACK.md](dogfood/TOOL_FEEDBACK.md).
