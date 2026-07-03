# Prescripta

![Version](https://img.shields.io/badge/version-v0.4.0-blue)
![Backend](https://img.shields.io/badge/backend-FastAPI-009688)
![Frontend](https://img.shields.io/badge/frontend-React-155E75)
![License](https://img.shields.io/badge/license-Apache--2.0-slate)

Prescripta é um sistema web educacional de apoio à prescrição segura. O projeto demonstra como correlacionar medicamento pretendido, perfil clínico estruturado do paciente, dose diária, dose acumulada, duração, cautelas por órgão/sistema, evidências internas demonstrativas e explicação responsável por IA.

> Uso educacional/demonstrativo: Prescripta não é dispositivo médico, não substitui avaliação profissional e não deve ser usado para decisões clínicas reais.

## Preview v0.4.0

### Fluxo demonstrativo

![GIF demonstrativo do Prescripta v0.4.0](docs/assets/v0.4.0/prescripta-v0.4-demo.gif)

### Telas principais

![Login](docs/assets/v0.4.0/login.png)

![Dashboard](docs/assets/v0.4.0/dashboard.png)

![Perfil clínico do paciente](docs/assets/v0.4.0/patient-clinical-profile.png)

![Checagem de prescrição](docs/assets/v0.4.0/prescription-check.png)

![Compatibilidade paciente-medicação](docs/assets/v0.4.0/prescription-compatibility.png)

![Evidências RAG](docs/assets/v0.4.0/rag-evidence-panel.png)

![Alternativas para avaliação profissional](docs/assets/v0.4.0/alternative-medications.png)

## Funcionalidades

- Dashboard com contagem de pacientes, medicamentos, checagens e alertas por severidade.
- Login JWT com perfis `admin`, `medico`, `enfermagem` e `auditor`.
- CRUD de pacientes com perfil clínico inteligente e badge de completude.
- Triagem rápida do paciente com preservação de histórico e auditoria.
- CRUD de medicamentos com dose máxima diária, duração, dose acumulada, cautelas por órgão/sistema e efeitos adversos demonstrativos.
- Checagem de prescrição com dose, frequência, via, duração, indicação e observações profissionais.
- Motor de risco determinístico para alergia, dose máxima, dose acumulada, duração, interações, polifarmácia, idade, contraindicações, vias e fatores clínicos do paciente.
- Compatibilidade paciente-medicação com score demonstrativo, fatores considerados e justificativas.
- RAG clínico demonstrativo com base interna em Markdown e busca textual normalizada.
- Clinical Context Graph para expor os nós e relações usados na análise.
- Alternativas terapêuticas avaliadas pelo motor de risco antes de aparecerem como opções para avaliação profissional.
- IA explicativa multi-provider, acionada manualmente, com fallback determinístico.
- Auditoria automática com usuário responsável em ações relevantes.
- Gestão de usuários para administradores.
- Seed demonstrativo para facilitar avaliação local.

## Ideia Clínica Implementada

A v0.4.0 responde à ideia de que dose máxima diária isolada não basta. A análise agora cruza:

- dose diária calculada;
- duração planejada;
- dose acumulada estimada;
- limites demonstrativos por condição clínica;
- histórico renal, hepático, cardíaco e gastrointestinal;
- alergias, reações adversas e medicamentos contínuos;
- cautelas e órgãos envolvidos no medicamento;
- evidências internas demonstrativas;
- alternativas cadastradas para avaliação profissional.

O resultado continua sendo demonstrativo. O sistema organiza risco e contexto para revisão humana, sem prescrever automaticamente.

## IA Explicativa

A IA recebe o resultado determinístico já calculado, o perfil clínico, a dose acumulada, as evidências RAG, o Clinical Context Graph e as alternativas avaliadas.

A IA:

- explica em linguagem simples por que a prescrição foi bloqueada ou exige atenção;
- gera resumo técnico;
- aponta dados do paciente considerados e dados faltantes;
- sugere perguntas de revisão clínica;
- cita que a base interna é demonstrativa;
- funciona em fallback determinístico sem chave de API.

A IA não:

- libera prescrição;
- calcula risco sozinha;
- altera status, risco, bloqueio, dose ou recomendação final;
- inventa fontes;
- substitui avaliação clínica profissional.

Configuração opcional:

```powershell
PRESCRIPTA_AI_PROVIDER=fallback
PRESCRIPTA_AI_API_KEY=
PRESCRIPTA_AI_MODEL=gpt-5.5
PRESCRIPTA_AI_BASE_URL=
```

Detalhes: [docs/ai/ai-explainer.md](docs/ai/ai-explainer.md) e [docs/ai/multi-provider-ai.md](docs/ai/multi-provider-ai.md)

## Arquitetura

O backend FastAPI concentra domínio, regras, autenticação, autorização, schemas, repositórios, banco SQLite, RAG interno, IA explicativa e rotas. O frontend React consome a API real via Axios/React Query e não contém regra clínica decisória.

```text
backend/app/domain          Entidades e objetos de resultado
backend/app/services        Motor de risco, contexto clínico, alternativas e IA
backend/app/knowledge       RAG demonstrativo e busca textual
backend/app/data            Base interna demonstrativa
backend/app/repositories    Persistência SQLAlchemy
backend/app/api/routes      Endpoints FastAPI
frontend/src/pages          Telas principais
frontend/src/components     Componentes reutilizáveis
docs                        Documentação modular
scripts                     Utilitários locais
```

## Stack

- Frontend: React, TypeScript, Vite, TailwindCSS, React Router, Axios, React Query, React Hook Form, Zod.
- Backend: FastAPI, Pydantic, SQLAlchemy, SQLite, JWT, Argon2, OpenAI SDK opcional, Pytest, Ruff.
- Qualidade: Conventional Commits, changelog, roadmap, GitHub Actions, releases versionadas.

## Rodar Com Script Windows

```powershell
powershell -ExecutionPolicy Bypass -File scripts/start-prescripta.ps1
```

O script abre backend, frontend e navegador usando portas padrão `8000` e `5173`.

## Como Rodar Backend

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r backend\requirements.txt
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

- Senhas com hash Argon2 via `pwdlib`.
- Tokens JWT com `PRESCRIPTA_SECRET_KEY` e expiração configurável.
- Backend é a fonte real de autorização.
- Frontend armazena token em `localStorage` nesta versão demonstrativa.
- IA explicativa é protegida por perfil, acionada por clique e tem fallback local.
- RAG interno é demonstrativo e não altera decisão.
- Nenhum dado real de paciente deve ser usado em seeds, testes ou demonstrações.

## Testes E Lint

Backend:

```powershell
cd backend
ruff check . --no-cache
pytest
```

Frontend:

```powershell
cd frontend
npm run lint
npm run build
```

## Release Atual

- Publicada: `v0.4.0`
- Notas: [docs/releases/v0.4.0.md](docs/releases/v0.4.0.md)
- Comparação conceitual: [docs/benchmark/safedose-comparison.md](docs/benchmark/safedose-comparison.md)
- Revisão de maturidade: [docs/product/maturity-review-v0.4.0.md](docs/product/maturity-review-v0.4.0.md)

## Roadmap Resumido

- `v0.1.0`: MVP de prescrição segura.
- `v0.2.0`: autenticação, perfis, segurança básica e auditoria com usuário.
- `v0.3.0`: IA explicativa, benchmark, maturidade e apresentação visual.
- `v0.4.0`: contexto clínico, dose acumulada, RAG interno e alternativas avaliadas.
- `v0.5.0`: relatórios PDF, exportação, filtros de auditoria e testes end-to-end.
- `v0.6.0`: Docker, PostgreSQL, migrações e deploy.
- `v1.0.0`: versão demonstrável completa.

## Documentação

- [Visão geral da arquitetura](docs/architecture/overview.md)
- [Decisões de arquitetura](docs/architecture/decisions.md)
- [Clinical Context Graph](docs/architecture/clinical-context-graph.md)
- [Visão de produto](docs/product/vision.md)
- [Roadmap de produto](docs/product/roadmap.md)
- [User stories](docs/product/user-stories.md)
- [Caso de uso do histórico do paciente](docs/product/patient-history-use-case.md)
- [Motor de risco](docs/clinical-rules/risk-engine.md)
- [Compatibilidade paciente-medicação](docs/clinical-rules/patient-medication-compatibility.md)
- [Dose acumulada e duração](docs/clinical-rules/cumulative-dose-and-duration.md)
- [Efeitos adversos e histórico](docs/clinical-rules/adverse-effects-and-patient-history.md)
- [RAG clínico demonstrativo](docs/rag/clinical-rag.md)
- [IA explicativa](docs/ai/ai-explainer.md)
- [IA multi-provider](docs/ai/multi-provider-ai.md)
- [Normalização e deduplicação](docs/data-quality/deduplication-and-normalization.md)
- [Comparação conceitual com SafeDose](docs/benchmark/safedose-comparison.md)
- [Revisão de maturidade v0.4.0](docs/product/maturity-review-v0.4.0.md)
- [Privacidade e LGPD](docs/security/privacy-and-lgpd.md)
- [Autenticação e perfis](docs/security/authentication-and-roles.md)
- [Threat model básico](docs/security/threat-model-basic.md)
- [Release v0.1.0](docs/releases/v0.1.0.md)
- [Release v0.2.0](docs/releases/v0.2.0.md)
- [Release v0.3.0](docs/releases/v0.3.0.md)
- [Release v0.4.0](docs/releases/v0.4.0.md)
