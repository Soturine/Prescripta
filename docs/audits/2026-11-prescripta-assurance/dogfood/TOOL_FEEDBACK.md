# Feedback para Derivanta Engine e Assertiva

Cada item tem evidência reproduzida neste dogfood. "FIXED" só quando a ferramenta foi alterada com
teste que falha antes; o resto é proposta, sem alteração nas ferramentas.

## Derivanta Engine

| ID | Tipo | Observação | Evidência | Estado |
|---|---|---|---|---|
| ENG-01 | falso positivo | 142 de 182 candidatos "sem referência" eram rotas FastAPI, listeners SQLAlchemy e hooks `@compiles`, registrados pelo decorador. | triagem 182 → 142/40; após a correção, 170 → 28 no mesmo escopo; os 28 de fato não têm referência textual (o que não os torna código morto) e nenhum candidato verdadeiro foi perdido | **FIXED** em `3958b84` + `d413e53` (Engine `main`); teste com controles negativos (`@functools.cache`, `.get` não roteador, função simples continuam acusados); suíte 944 passed / 4 skipped, lint, format, mypy, conformance 20/20 |
| ENG-02 | falso negativo (contrato) | Uso só em teste conta como referência; `calculate_daily_dose` (alias usado só pelo próprio teste) não foi acusado. | conhecido de antemão no PRE-08 | PROPOSED: classe `TEST_ONLY` separada de "referenciado" |
| ENG-03 | falso negativo (capacidade) | Módulo sem definições próprias (só re-export) e sem importadores não é acusado: a regra olha definições, não módulos. | `knowledge/normalizer.py` | PROPOSED: candidato "módulo sem importador" |
| ENG-04 | falso negativo | `evaluate --repository` observa o HEAD (`14f9be1`), mas não compara com o `revision` da evidência citada pela alegação (`6508221`). A Assertiva acusa o mesmo caso (`CI_RUN_FOR_ANOTHER_REVISION`). | `engine_evaluate_14f9be1.*` | PROPOSED: achado quando a revisão da evidência difere do HEAD observado |
| ENG-05 | falso positivo de contexto | `NO_OP_FUNCTION` em `tests/fixtures/portable-results/test_shop.py::test_coupon_skipped`, entrada intencional de fixture. | inspeção da Assertiva | PROPOSED: tratar diretórios de fixture como a Assertiva já trata |
| ENG-06 | ruído | O inventário de linguagens inclui diretórios ignorados pelo Git (ex.: `.tmp/` com um venv local, acusado como C/C++). | `engine_evaluate_14f9be1.txt` | PROPOSED: marcar entradas ignoradas pelo Git ou excluí-las por padrão |

## Assertiva

| ID | Tipo | Observação | Evidência | Estado |
|---|---|---|---|---|
| AS-01 | hipótese antiga | "Teste de negação de escrita que só verifica 403" merece sinal próprio? | `STATE_AFTER_REJECTION_NOT_EVIDENCED` já existe e acusa | **NO_CHANGE** (já coberto) |
| AS-02 | diagnóstico | Em erro de coleta, o relatório guardava só o caminho; o FAIL parecia falha do produto. | antes: run `16748d2153094daf`; depois: run `d1b8259bd8944dea` mostra `backend/tests: ModuleNotFoundError: No module named 'app'` | **FIXED** em `76f2370` + `9885dde` (branch `fix/dogfood-prescripta-collect-cause`, sem PR); teste falha antes (KeyError) |
| AS-03 | capacidade | Sem diretório de trabalho por subprojeto: um monorepo com config pytest em `backend/` não é coletado da raiz e, auditado a partir de `backend/`, perde arquivos da raiz. Bloqueia `--execute` e `--mutate` no backend. | runs `16748d2153094daf` (FAIL), `2126988ac4c446c8` (BLOCKED) | PROPOSED: `[tests] workdir` por runner |
| AS-04 | ambiente/adaptador | Playwright BLOCKED no Windows: `spawn cmd.exe ENOENT`. | run `25dbd3f2ce3b432e` | PROPOSED: investigar o PATH do processo isolado no Windows |
| AS-05 | redação | A limitação "variáveis com aparência de credencial foram retidas do código executado" aparece num run sem execução (só importação); `SESSIONNAME` (variável padrão do Windows) entra na lista. | run `3b942881ac954fef` | PROPOSED: só emitir quando houve execução |
| AS-06 | suíte própria | Neste Windows com sandbox, 3 testes de processo (`os.kill`, lease de workspace, falha de instalação) falham igual em `2618d95` limpo; 3 outros dependiam do `coverage`, ausente no venv montado pelo agente (não é defeito da Assertiva). | `assertiva_rerun_*` | OBSERVED: causa raiz não investigada; pode ser o sandbox |

| AS-07 | robustez | `--execute` no Derivanta Engine: a limpeza do `TemporaryDirectory` da qualificação do artefato (`python_package._qualify_into`) falhou com `PermissionError` (`python.exe` do venv temporário ainda travado no Windows) e derrubou a auditoria inteira, sem relatório, exit 1. Intermitente: a reexecução idêntica terminou. Falha de limpeza deveria virar limitação, não perder o run. | stderr do 1º run; run `d89a95c89e5d4c23` (2º) | **FIXED** em `3d24a90` (branch `fix/artifact-cleanup-keeps-report`, sem PR): `workspace.disposable_dir` remove sem seguir links e declara o que sobrar como limitação; testes de saída limpa, erro no corpo, arquivo aberto no Windows (o `TemporaryDirectory` original falhando é o controle negativo) e entrada não removível no POSIX |
| AS-08 | falso positivo | `dependency_closure` do artefato acusa `mcp` como "importado sem dependência declarada", mas o Engine declara `mcp` no extra opcional `[mcp]` e o importa sob demanda (`cli.py:274`). As coletas falhas do artefato (`test_mcp_stdio.py`, `test_skill.py`) vêm da mesma causa. | run `d89a95c89e5d4c23` | PROPOSED: reconhecer extras opcionais com import tardio |

## Pontos fortes observados (sem mudança necessária)

- Assertiva no Engine: 225 erros de teste no isolamento vinham de `PermissionError` na pasta temporária
  da máquina (restrição do sandbox); a ferramenta atribuiu a causa à infraestrutura (`origin
  INFRASTRUCTURE`) e mandou triar a causa antes dos testes, em vez de culpar o Engine. A execução
  direta do agente no mesmo SHA (com `--basetemp`) deu 944 passed / 4 skipped.

- Assertiva: rotula evidência importada como não executada por ela; marca `dirty=True` quando o
  próprio runtime tinha alteração não commitada; recusa contar `--execute` quando o código do projeto
  muda durante a execução (exit 3, provocado pelo agente na primeira tentativa).
- Engine: `compare` estável entre revisões; `evaluate` não promove alegação a verificada e acusa
  "validado" sem evidência.
