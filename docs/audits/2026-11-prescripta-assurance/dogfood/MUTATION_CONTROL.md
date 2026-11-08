# Controle de mutação manual (agent-led)

Executado em 2026-11-08 em worktree descartável de `14f9be1`, com o interpretador do projeto. Cada
mutante é uma troca textual; o arquivo é restaurado com `git checkout` depois de cada execução e o
script recusa começar com worktree sujo. Scripts: `mutation_control.py` e `mutation_pairs.py`
(cópia e resultados JSON na pasta de evidência local, hashes em [RUN_MANIFEST.json](RUN_MANIFEST.json)).

Não é a mutação nativa da Assertiva (`--mutate`, BLOCKED por AS-03) nem uma pontuação de mutação:
são mutantes escolhidos à mão nas regras que decidem bloqueio, para testar se os testes as protegem.

## Rodada 1 — conjunto focado (5 arquivos, 30 testes)

| Mutante | Mudança | Resultado |
|---|---|---|
| M1 | teto de elevação por idade HIGH → CRITICAL | KILLED |
| M2 | idade não eleva o risco | KILLED |
| M3 | `max` → `min` na composição | KILLED |
| M4 | passo de elevação 1 → 0 | KILLED |
| M5 | `RiskEngine`: HIGH → liberado | sobreviveu |
| M6 | `RiskEngine`: CRITICAL → atenção | sobreviveu |
| O1 | orquestrador: severidade CRITICAL deixa de bloquear | sobreviveu |
| O2 | orquestrador: status de dose bloqueante ignorado | sobreviveu |
| O3 | orquestrador: política bloqueante ignorada | sobreviveu |
| O4 | `_legacy_status`: BLOCKED → ATTENTION | KILLED |
| O5 | achados deixam de exigir revisão | sobreviveu |

## Rodada 2 — sobreviventes contra a suíte inteira (363 testes)

| Mutante | Resultado | Leitura |
|---|---|---|
| M6 | KILLED (suíte inteira) | coberto fora do conjunto focado |
| M5 | sobreviveu | `RiskEngine.status` não é consumido por nenhuma rota (o orquestrador usa só alertas, compatibilidade, dose e grafo): superfície de decisão paralela, sem teste → **NEW-25** |
| O1, O2, O3, O5 | sobreviveram | hipótese: guardas redundantes (cada bloqueio chega por dois caminhos) ou lacuna real |

## Rodada 3 — mutantes compostos ("todos os caminhos")

Remover um único caminho de um bloqueio redundante produz um mutante equivalente. Para separar
redundância de lacuna, cada composto remove todos os caminhos de um tipo de bloqueio.

| Composto | Caminhos removidos | Resultado | Conclusão |
|---|---|---|---|
| P2 política | condição direta + `hard_block` + severidade CRITICAL do achado | KILLED (`test_policy_block_changes_aggregate_decision`) | O3 era equivalente |
| P3 CRITICAL | condição de severidade + `hard_block` dos alertas do `RiskEngine` | KILLED (`test_screening_findings_still_block`) | O1 era equivalente |
| P1 dose | condição direta + `hard_block` dos achados de dose | **sobreviveu** | o único teste de bloqueio por dose também é bloqueado pelo `RiskEngine` (`MAX_DAILY_DOSE_EXCEEDED`); máximo por procedimento e cumulativo só eram testados no serviço de dose, nunca na decisão agregada → **NEW-23** |

O5 não é redundante: sem `findings` na condição, um idoso com dose normal e cobertura completa recebia
`evaluated_no_issue`, e o envelope aceitava decisão favorável com achados → **NEW-24**.

## Correções e prova

| Achado | Teste novo | Controle negativo |
|---|---|---|
| NEW-23 | `test_dose_intelligence_block_alone_blocks_aggregate_decision` (3 status bloqueantes; dose normal para o `RiskEngine`) | P1 aplicado ao código real: 3 falhas; restaurado: verde |
| NEW-24 | `test_non_blocking_finding_under_full_coverage_still_requires_review`; invariante do envelope + `test_envelope_rejects_favorable_decision_with_findings` | O5 aplicado: falha (`evaluated_no_issue` ≠ `review_required`); restaurado: verde |
| NEW-25 | `test_invalid_route_generates_high_alert` passa a afirmar `status` e `human_review_required`; ADR 012 declara o orquestrador autoridade única | M5 aplicado: falha; restaurado: verde |

Suíte backend depois das correções: SQLite 368 passed / 5 skipped; PostgreSQL 17 ver
[RUN_MANIFEST.json](RUN_MANIFEST.json).
