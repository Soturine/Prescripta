# Visão Geral da Arquitetura

Prescripta é organizado como um monorepo simples, com backend e frontend independentes.

## Backend

O backend usa FastAPI e centraliza regra de negócio, autenticação e autorização.

- `domain`: entidades de domínio como paciente, medicamento, prescrição e alerta.
- `schemas`: contratos Pydantic expostos na API.
- `services`: verificadores de alergia, dose, interação e motor de risco.
- `core/auth.py`: dependências de autenticação e autorização por perfil.
- `core/security.py`: hash de senha e emissão/validação de JWT.
- `repositories`: acesso a dados com SQLAlchemy.
- `api/routes`: endpoints HTTP.
- `database`: sessão, modelos SQLAlchemy e seed demonstrativo.

## Frontend

O frontend usa React com Vite e consome a API real via Axios e React Query.

- `pages`: telas de navegação.
- `components`: formulários, layout, badges e estados reutilizáveis.
- `services`: cliente HTTP.
- `context`: sessão autenticada e usuário atual.
- `types`: tipos derivados dos contratos da API.

## Persistência

A versão `v0.2.0` ainda usa SQLite local. A auditoria registra checagens de prescrição e ações administrativas com usuário responsável quando disponível.

## Limites

O projeto é educacional e não é um dispositivo médico. A IA não faz parte desta versão.
