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
