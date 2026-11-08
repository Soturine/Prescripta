# Derivanta Framework Feedback

Escrito depois do registro de achados do Prescripta, para que a melhoria do Framework não influencie
os achados do alvo. Local; nada foi enviado upstream.

## Identidade

- Data: 2026-11-08
- Auditoria alvo: assurance 2026-11 do Prescripta (CDS demonstrativo, FastAPI + React, dados sintéticos)
- Revisão do Derivanta: `218761d` (pin verificado pelo Engine `evaluate --framework`)
- Agente: Claude Code (Opus 5.5)
- Status: candidate · Compartilhamento: sanitized-shareable

## Resumo

O workflow AUDIT funcionou como guia e mudou decisões concretas (desafio independente dos
sobreviventes de mutação; proposta ≠ implementado). Uma lacuna material: o Framework reconhece que
sobrevivente de mutação não é necessariamente lacuna de teste, mas só num registro de pesquisa e sem
técnica para decidir. Este dogfood produziu uma técnica concreta.

## Superfícies usadas

| Superfície | Usada? | Utilidade | Atrito / limite |
|---|---|---|---|
| Skill / roteamento | sim, via Engine `evaluate` | workflow AUDIT + SECURITY, RELEASE, SAFETY, CONCURRENCY por gatilho declarado | as 5 perguntas sugeridas (RTO/RPO, residência de dados) não se aplicam a uma demo; ok como perguntas |
| `skill/workflows/AUDIT.md` §13, §15 | sim | decisivo para não transformar sobrevivente em achado sem desafio | — |
| Assurance (ADAPTIVE_TEST_ASSURANCE) | sim | distinção descoberto / executado / sustenta a alegação | — |
| Templates (FRAMEWORK_FEEDBACK, INSPECTION_COVERAGE) | sim (este arquivo) | estrutura útil | — |

## Achados do alvo já cobertos pelo Framework

| Achado | Owner existente | Mudança no Derivanta? |
|---|---|---|
| CI de outra revisão usado como evidência (controle negativo `--ci-run`) | AUDIT §1 "exact revision" + evidência por run | não |
| coletor BLOCKED não conta como verde | CONTEXT_IMPACT_AND_TEST_EVIDENCE | não |

## DF-002 — Sobrevivente de mutação diante de guardas redundantes

- Classificação: REUSABLE_PATTERN_CANDIDATE
- Estado da evidência: reproduced (um projeto)
- Evidência: [MUTATION_CONTROL.md](MUTATION_CONTROL.md): O1 e O3 sobreviveram à suíte inteira e eram
  equivalentes (bloqueio por dois caminhos); o composto P1 sobreviveu e revelou lacuna real (NEW-23).
- Owners buscados: `assurance/ADAPTIVE_TEST_ASSURANCE.md`; `research/records/2026-10-28-context-graph-agent-economy-and-qa-wave.md` ("survivor ≠ necessarily true test gap", PARTIAL)
- Por que não bastou: o Framework diz que pode ser mutante equivalente, mas não diz como decidir.
- Preocupação generalizável: sistemas críticos usam defesa em profundidade; mutante de um só local num
  caminho redundante é equivalente por construção, e o auditor pode errar nos dois sentidos (achado
  falso, ou descartar como "equivalente" uma lacuna real).
- Melhoria sugerida: em ADAPTIVE_TEST_ASSURANCE, um passo "para um sobrevivente num guarda de
  segurança, enumere todos os caminhos que produzem o mesmo efeito e aplique um mutante composto que
  remova todos; KILLED → o simples era equivalente; SURVIVED → lacuna real".
- Caso de eval sugerido: função com bloqueio por dois caminhos; um mutante simples sobrevive; a resposta
  esperada não reporta lacuna sem o composto.
- Risco: explosão combinatória se aplicado a tudo; restringir a guardas de segurança/bloqueio.
- Recomendação: candidate.

## DF-003 — Exemplo de conflito de porta em smoke local (antigo FW-01)

- Classificação: FRAMEWORK_GUIDANCE_GAP (pequeno)
- Observação: smoke de containers falhou por porta 8080 ocupada no host; a orientação de "coletor que
  falhou" não traz esse exemplo comum.
- Recomendação: defer (exemplo, não regra).
