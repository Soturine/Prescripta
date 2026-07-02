# Prescripta

![Version](https://img.shields.io/badge/version-v0.2.0--dev-blue)
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
- Login JWT com perfis `admin`, `medico`, `enfermagem` e `auditor`.
- CRUD básico de pacientes protegido por perfil.
- CRUD básico de medicamentos protegido por perfil.
- Checagem de prescrição com status, risco, alertas, recomendação e revisão humana.
- Motor de risco determinístico para alergia, dose máxima, interação, polifarmácia, idade, contraindicação e via.
- Auditoria automática com usuário responsável em ações relevantes.
- Gestão de usuários para administradores.
- Seed demonstrativo para facilitar avaliação local.

## Arquitetura

O backend FastAPI concentra domínio, regras, autenticação, autorização, schemas, repositórios, banco SQLite e rotas. O frontend React consome a API real via Axios/React Query e não contém regra clínica. A auditoria é persistida para checagens e ações administrativas relevantes.

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
- Backend: FastAPI, Pydantic, SQLAlchemy, SQLite, JWT, Argon2, Pytest, Ruff.
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

## Credenciais Demonstrativas

As credenciais abaixo são apenas para ambiente local e dados fictícios.

| Perfil | E-mail | Senha |
| --- | --- | --- |
| Admin | `admin@prescripta.local` | `Admin@12345` |
| Médico | `medico@prescripta.local` | `Medico@12345` |
| Enfermagem | `enfermagem@prescripta.local` | `Enfermagem@12345` |
| Auditor | `auditor@prescripta.local` | `Auditor@12345` |

## Perfis De Usuário

- Admin: gerencia pacientes, medicamentos, usuários, checagens, auditoria e dashboard.
- Médico: gerencia pacientes, consulta medicamentos, verifica prescrições e vê dashboard.
- Enfermagem: consulta pacientes e medicamentos, verifica prescrições e vê dashboard.
- Auditor: vê dashboard e auditoria, sem criar ou editar registros.

## Segurança

- Senhas são armazenadas com hash Argon2 via `pwdlib`.
- Tokens JWT usam `PRESCRIPTA_SECRET_KEY` e expiração configurável por `PRESCRIPTA_ACCESS_TOKEN_EXPIRE_MINUTES`.
- O frontend armazena o token em `localStorage` nesta versão demonstrativa. Isso simplifica o MVP, mas não é a recomendação final para produção.
- Backend é a fonte real de autorização; menus ocultos no frontend são apenas ergonomia.

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

- Publicada: `v0.1.0`
- Notas: [docs/releases/v0.1.0.md](docs/releases/v0.1.0.md)
- Em desenvolvimento local: `v0.2.0`
- Notas planejadas: [docs/releases/v0.2.0.md](docs/releases/v0.2.0.md)

## Roadmap Resumido

- `v0.1.0`: MVP de prescrição segura.
- `v0.2.0`: autenticação, perfis, segurança básica e auditoria com usuário.
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
- [Autenticação e perfis](docs/security/authentication-and-roles.md)
- [Threat model básico](docs/security/threat-model-basic.md)
- [Release v0.1.0](docs/releases/v0.1.0.md)
- [Release v0.2.0](docs/releases/v0.2.0.md)
