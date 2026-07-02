# Visão Geral da Arquitetura

Prescripta é organizado como um monorepo simples, com backend e frontend independentes.

## Backend

O backend usa FastAPI e centraliza a regra de negócio em serviços determinísticos.

- `domain`: entidades de domínio como paciente, medicamento, prescrição e alerta.
- `schemas`: contratos Pydantic expostos na API.
- `services`: verificadores de alergia, dose, interação e motor de risco.
- `repositories`: acesso a dados com SQLAlchemy.
- `api/routes`: endpoints HTTP.
- `database`: sessão, modelos SQLAlchemy e seed demonstrativo.

## Frontend

O frontend usa React com Vite e consome a API real via Axios e React Query.

- `pages`: telas de navegação.
- `components`: formulários, layout, badges e estados reutilizáveis.
- `services`: cliente HTTP.
- `types`: tipos derivados dos contratos da API.

## Persistência

A versão `v0.1.0` usa SQLite local. A auditoria de checagem é persistida sempre que `/api/prescriptions/check` é chamado.

## Limites

O projeto é educacional e não é um dispositivo médico. A IA não faz parte desta versão.
