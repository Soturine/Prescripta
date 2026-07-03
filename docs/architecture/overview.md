# Visão Geral da Arquitetura

Prescripta é organizado como um monorepo simples, com backend e frontend independentes.

## Backend

O backend usa FastAPI e centraliza regra de negócio, autenticação, autorização, contexto clínico, RAG demonstrativo e IA explicativa.

- `domain`: entidades de domínio como paciente, medicamento, prescrição e alerta.
- `schemas`: contratos Pydantic expostos na API.
- `services`: verificadores de alergia, dose, interação, compatibilidade, alternativas e motor de risco.
- `knowledge`: busca textual e normalização para RAG clínico demonstrativo.
- `data/knowledge_base`: base interna em Markdown, usada apenas como contexto explicativo.
- `core/auth.py`: dependências de autenticação e autorização por perfil.
- `core/security.py`: hash de senha e emissão/validação de JWT.
- `repositories`: acesso a dados com SQLAlchemy.
- `api/routes`: endpoints HTTP.
- `database`: sessão, modelos SQLAlchemy e seed demonstrativo.

## Frontend

O frontend usa React com Vite e consome a API real via Axios e React Query.

- `pages`: telas de navegação.
- `components`: formulários, layout, badges, cards clínicos e estados reutilizáveis.
- `services`: cliente HTTP.
- `context`: sessão autenticada e usuário atual.
- `types`: tipos derivados dos contratos da API.

## Persistência

A versão `v0.4.0` ainda usa SQLite local. A auditoria registra checagens de prescrição, ações administrativas, triagem rápida e metadados de explicação com usuário responsável quando disponível.

## Decisão Clínica

O motor determinístico no backend é a fonte de status, risco, bloqueio, dose crítica e recomendação. A IA e o RAG explicam contexto demonstrativo, mas não alteram decisões.

## Limites

O projeto é educacional e não é um dispositivo médico. A base interna de conhecimento não é uma bula validada, não substitui protocolo clínico e exige validação profissional antes de qualquer uso real.
