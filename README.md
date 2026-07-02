# Prescripta

![Version](https://img.shields.io/badge/version-v0.1.0-blue)
![Backend](https://img.shields.io/badge/backend-FastAPI-009688)
![Frontend](https://img.shields.io/badge/frontend-React-155E75)
![License](https://img.shields.io/badge/license-Apache--2.0-slate)

Prescripta é um sistema web educacional de apoio à prescrição segura. O MVP demonstra como identificar riscos antes de uma prescrição usando regras determinísticas para alergias, interações medicamentosas, dose máxima, polifarmácia, contraindicações, vias inválidas e fatores de risco do paciente.

> Uso educacional/demonstrativo: Prescripta não é dispositivo médico, não substitui avaliação profissional e não deve ser usado para decisões clínicas reais.

## Preview

### Dashboard

![Dashboard do Prescripta](docs/assets/dashboard.png)

### Checagem de prescrição

![Tela de checagem de prescrição](docs/assets/prescription-check.png)

### Auditoria

![Tela de auditoria](docs/assets/audit.png)

### Fluxo demonstrativo

![GIF demonstrativo do Prescripta](docs/assets/prescripta-demo.gif)

## Problema

Prescrições podem concentrar riscos em vários pontos: histórico do paciente, dose diária, via de administração, medicamentos contínuos e comorbidades. Prescripta organiza essas verificações em um fluxo web simples, auditável e testável.

## Funcionalidades

- Dashboard com contagem de pacientes, medicamentos, checagens e alertas por severidade.
- CRUD básico de pacientes.
- CRUD básico de medicamentos.
- Checagem de prescrição com status, risco, alertas, recomendação e revisão humana.
- Motor de risco determinístico para alergia, dose máxima, interação, polifarmácia, idade, contraindicação e via.
- Auditoria automática de toda checagem.
- Seed demonstrativo para facilitar avaliação local.

## Arquitetura

O backend FastAPI concentra domínio, regras, schemas, repositórios, banco SQLite e rotas. O frontend React consome a API real via Axios/React Query e não contém regra clínica. A auditoria é persistida a cada checagem.

```text
backend/app/domain       Entidades e enums de domínio
backend/app/services     Motor de risco e verificadores determinísticos
backend/app/repositories Persistência SQLAlchemy
backend/app/api/routes   Endpoints FastAPI
frontend/src/pages       Telas principais
frontend/src/components  Componentes reutilizáveis
docs                     Documentação modular
```

## Stack

- Frontend: React, TypeScript, Vite, TailwindCSS, React Router, Axios, React Query, React Hook Form, Zod.
- Backend: FastAPI, Pydantic, SQLAlchemy, SQLite, Pytest, Ruff.
- Qualidade: Conventional Commits, changelog, roadmap, GitHub Actions.

## Como Rodar Backend

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r backend\requirements.txt
cd backend
..\.venv\Scripts\python -m uvicorn app.main:app --reload
```

Ou da raiz:

```powershell
.\.venv\Scripts\python -m uvicorn app.main:app --reload --app-dir backend
```

Swagger: `http://localhost:8000/docs`

## Como Rodar Frontend

```powershell
cd frontend
npm install
npm run dev
```

Frontend: `http://localhost:5173`

## Testes E Lint

Backend:

```powershell
cd backend
..\.venv\Scripts\python -m ruff check . --no-cache
..\.venv\Scripts\python -m pytest
```

Frontend:

```powershell
cd frontend
npm run lint
npm run build
```

## Release Atual

- Versão: `v0.1.0`
- Notas: [docs/releases/v0.1.0.md](docs/releases/v0.1.0.md)
- Tag sugerida/publicada: `v0.1.0`

## Roadmap Resumido

- `v0.1.0`: MVP de prescrição segura.
- `v0.2.0`: autenticação, perfis e segurança.
- `v0.3.0`: IA apenas para explicação de alertas.
- `v0.4.0`: relatórios PDF e exportação.
- `v0.5.0`: Docker, PostgreSQL e deploy.
- `v1.0.0`: versão demonstrável completa.

## Documentação

- [Visão geral da arquitetura](docs/architecture/overview.md)
- [Decisões de arquitetura](docs/architecture/decisions.md)
- [Visão de produto](docs/product/vision.md)
- [Roadmap de produto](docs/product/roadmap.md)
- [User stories](docs/product/user-stories.md)
- [Motor de risco](docs/clinical-rules/risk-engine.md)
- [Notas do seed de medicamentos](docs/clinical-rules/medication-seed-notes.md)
- [Privacidade e LGPD](docs/security/privacy-and-lgpd.md)
- [Threat model básico](docs/security/threat-model-basic.md)
- [Release v0.1.0](docs/releases/v0.1.0.md)
