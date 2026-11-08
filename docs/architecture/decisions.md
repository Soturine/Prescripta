# Decisões de arquitetura

## ADR 001 — Regras determinísticas primeiro

Decisão: risco, bloqueio, dose crítica e recomendação final são calculados em `backend/app/services`. IA só explica, extrai ou propõe dentro de contratos tipados e fontes permitidas.

## ADR 002 — PostgreSQL operacional, SQLite local

Decisão: PostgreSQL é o alvo da stack reprodutível e de ambientes não locais. SQLite reduz dependências no desenvolvimento demonstrativo, mas é rejeitado em produção.

## ADR 003 — Frontend sem regra clínica

Decisão: React coleta entradas e apresenta valores canônicos do backend. Locale, badge, filtro ou estado visual não podem reinterpretar risco.

## ADR 004 — Autorização e sessão no backend

Decisão: o backend combina capacidades, instituição, relação/purpose e escopo por objeto. Sessão usa cookie HttpOnly; as decisões históricas de “sem autenticação” e token em `localStorage` foram superadas.

## ADR 005 — Snapshots e unidade de trabalho

Decisão: decisão, auditoria e snapshot são persistidos na mesma transação. Relatórios históricos leem o snapshot, verificam JSON canônico e não consultam o cadastro vivo.

## ADR 006 — Research aggregate-first

Decisão: Research aceita apenas DSL e operadores permitidos, registra attrition e proveniência e retorna agregados. Definições revisadas ganham nova versão, e IA não executa consulta.

## ADR 007 — i18n de apresentação

Decisão: PT-BR e EN-US usam catálogos estáticos e verificados. A escolha manual prevalece sobre preferências do navegador, com fallback PT-BR. Códigos, unidades, valores persistidos e dados de fonte não são traduzidos.

## ADR 008 — Containers reprodutíveis e mínimos

Decisão: bases são fixadas por digest, builds são multi-stage e processos rodam sem root. Migração é um serviço one-shot idempotente antes da API; PostgreSQL permanece na rede interna. O smoke de container valida integração e não duplica a suíte completa.

## ADR 009 — Supply chain bloqueante

Decisão: lockfiles, installs exatos, Actions por SHA, inspeção de install scripts, secret scan, SCA, CodeQL, SBOM, scan de imagem e attestations compõem a evidência. Exceções precisam ser estreitas, justificadas e versionadas.

## ADR 010 — Composição do risco agregado por idade (proposta, pendente de revisão clínica)

Contexto: até a v1.0.0, `RiskEngine` elevava o nível agregado em +1 para idade ≥ 65 (podendo chegar a
`critico`/`bloqueado`), mas o orquestrador — caminho da checagem e do CDS — recalculava o máximo dos
achados e descartava a elevação. No próprio motor, acrescentar `ELDERLY_CAUTION` recalculava o
máximo e **reduzia** `critico` para `alto` (comportamento não monotônico). Tabela de 18 cenários
(idade 64/65/70 × risco base baixo/moderado/alto × cautela) registrada em
`docs/audits/2026-11-prescripta-assurance/FINDINGS_REGISTER.md` (PRE-01).

Decisão: uma única função, `compose_risk_level`, usada por motor, orquestrador e alternativas. É
monotônica (acrescentar achado nunca reduz o nível) e aplica +1 nível por idade com **teto `alto`**
(`AGE_ELEVATION_CEILING`). Idade isolada não gera bloqueio: `critico` exige achado crítico próprio.

Efeito observável: no caminho principal, idosos sem achados passam de `baixo` para `moderado` e com
base `moderado` passam a `alto` (mais conservador que o comportamento anterior do orquestrador). No
caminho de alternativas, base `alto` + idade deixa de virar `critico/bloqueado`.

Severidade de achado × nível agregado: o card `AGE_RISK` tem severidade própria `baixo` e descreve que
eleva o agregado; `highest_severity`/`risk_level` é o **nível agregado** e pode ser maior que todos os
cards. A UI não deve inferir o agregado a partir dos cards.

Status: decisão de engenharia para remover divergência e não monotonicidade; **não é política clínica
validada**. O teto é uma constante revisável. Critérios para revisão por especialista: se idade isolada
deve poder bloquear; se o +1 deve depender de comorbidades, função renal ou classe do fármaco; como
`ELDERLY_CAUTION` interage com o +1. Regras demonstrativas, sem uso assistencial.

## ADR 011 — Alternativas são candidatos para revisão, não substituições

Contexto: alternativas eram avaliadas pelo `RiskEngine` isolado, sem Dose Intelligence, psicotrópicos,
política do prescritor ou cobertura, e com a **dose do medicamento original** aplicada ao candidato;
podiam aparecer como `liberado` (selo verde).

Decisão: cada candidato passa pelo mesmo orquestrador em modo `include_dose=False`: checagens
dependentes de dose são puladas e a dose vira dado ausente (decisão `insufficient_data`, nunca
`evaluated_no_issue`). O status exibido é `atencao` ou `bloqueado`, nunca `liberado`; a resposta
declara `review_status=candidate_for_human_review` e `dose_assessment=not_evaluated_for_alternative`.
Ordem transparente: mesmo grupo alternativo > mesma ação terapêutica > relacionamento cadastrado,
desempate por nome e id; no máximo quatro candidatos, buscados no catálogo inteiro.
