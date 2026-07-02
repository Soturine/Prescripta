# Decisões de Arquitetura

## ADR 001 — Regras Determinísticas Primeiro

Decisão: o motor de risco é implementado com regras determinísticas em `backend/app/services`.

Motivo: regras críticas precisam ser testáveis, auditáveis e previsíveis. Qualquer IA futura deve explicar alertas já gerados, não decidir bloqueios.

## ADR 002 — SQLite no MVP

Decisão: usar SQLite na versão inicial.

Motivo: reduz dependências operacionais e facilita demonstração local. PostgreSQL fica no roadmap.

## ADR 003 — Frontend Sem Regra Clínica

Decisão: React não calcula risco.

Motivo: evita divergência entre interface e backend. A UI coleta entradas, chama API e apresenta resultados.

## ADR 004 — Sem Autenticação em v0.1.0

Decisão: autenticação fica fora do MVP.

Motivo: o foco inicial é motor de risco, auditoria, documentação e experiência demonstrável.

## ADR 005 — Autorização Centralizada no Backend

Decisão: a partir da `v0.2.0`, rotas sensíveis são protegidas por dependências FastAPI baseadas em JWT e perfil.

Motivo: o frontend pode esconder menus por ergonomia, mas a proteção real precisa estar no backend.

## ADR 006 — Token em LocalStorage no MVP

Decisão: o frontend usa `localStorage` para manter o token JWT na `v0.2.0`.

Motivo: simplifica a demonstração local. Essa escolha é documentada como limitação e deve ser revista antes de produção.
