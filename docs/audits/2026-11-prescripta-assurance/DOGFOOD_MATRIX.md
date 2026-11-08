# Dogfood Derivanta / Engine / Assertiva — matriz e log agent-led

Checkouts em 2026-11-08 (iguais a `origin/main`, sem alterações locais):
`Derivanta@218761d`, `Derivanta-Engine@17fa564`, `Assertiva@2618d95` (v0.10.1).

## Estado por célula

| Alvo | Agente + Framework | Derivanta Engine (CLI) | Assertiva (CLI) | Evidência independente |
|---|---|---|---|---|
| Prescripta | **EXECUTED** (ver log abaixo) | **BLOCKED** | **BLOCKED** | pytest SQLite/PG, Vitest, Playwright, Alembic PG, Trivy, Gitleaks, pip-audit, npm audit, CI por SHA |
| Assertiva | NOT_EXECUTED | BLOCKED | BLOCKED | — |
| Derivanta Engine | NOT_EXECUTED | BLOCKED | BLOCKED | — |
| Derivanta Framework | **EXECUTED (leitura e aplicação de owners)** | BLOCKED | BLOCKED | — |

Nenhum output de ferramenta existe neste repositório e nenhum foi simulado. `RUN_MANIFEST.json`,
reports HTML/JSON da Assertiva e `DERIVANTA_ENGINE_*.json` **não foram criados** porque nenhuma
execução ocorreu. Ver [OPEN_BLOCKERS.md](OPEN_BLOCKERS.md).

## Log agent-led (o que o agente fez com o Framework)

Owners efetivamente lidos e usados: `Derivanta/skill/SKILL.md`, `skill/workflows/AUDIT.md`,
`skill/workflows/CONTEXT_IMPACT_AND_TEST_EVIDENCE.md`; da Assertiva, `references/TEST_QUALITY.md`
(como lente metodológica, não como execução da ferramenta).

| Orientação aplicada | Decisão concreta e efeito verificável |
|---|---|
| AUDIT §13: caminho de desafio materialmente distinto para achados de alto impacto | Todo achado corrigido tem controle negativo: o teste é rodado contra o código do HEAD anterior e precisa falhar (PRE-01, 02, 03, 04, 05, 06, 09, NEW-04, 06, 10–16). |
| CONTEXT/TEST: "coletor configurado que falhou → BLOCKED, nunca PASS" | O smoke de containers falhou localmente por porta 8080 ocupada (NVIDIA Broadcast); classificado como ambiental, reexecutado em porta alternativa antes de qualquer conclusão. |
| SKILL: "não inferir ausência de inspeção incompleta"; achados semânticos sem ferramenta | PRE-06 em PostgreSQL (500), NEW-11 (alternativas com dose de outra droga), NEW-12, NEW-15 e as corridas de sessão R1/R2 foram achados por raciocínio sobre ordem de requisições e dialetos, não por ferramenta. |
| TEST_QUALITY: oráculos fracos (só status), testes sem asserção, tautologias | Sonda AST do agente: 275 testes, 0 tautologias, 0 exceções engolidas, 2 sem asserção (legítimos: "aceita sem erro"), 15 só com status. Fortalecidos os que negam **escrita** (efeito parcial) e os de sessão (corpo do erro). |

Diferença honesta: a sonda AST e as lentes acima **não** equivalem à Assertiva (que também executa a
suíte, importa cobertura, mede mutação e classifica fidelidade). Nenhuma descoberta acima é atribuída
às ferramentas.

## Feedback para as ferramentas (proposto, não aplicado)

| tool_gap_id | Ferramenta | Observação | Estado |
|---|---|---|---|
| FW-01 | Derivanta Framework | A orientação sobre "coletor que falhou" não menciona conflito de porta no host como causa comum de falso negativo em smokes locais. Candidato a exemplo no owner, não regra nova. | PROPOSED (sem evidência de ferramenta) |
| AS-01 | Assertiva | Hipótese a testar quando houver execução: o padrão "teste de negação de escrita que só verifica 403" merece sinal próprio (efeito parcial não verificado). | PROPOSED — requer execução para saber se já é detectado |
