# Prescripta

![Version](https://img.shields.io/badge/version-v0.6.0-blue)
![Backend](https://img.shields.io/badge/backend-FastAPI-009688)
![Frontend](https://img.shields.io/badge/frontend-React-155E75)
![License](https://img.shields.io/badge/license-Apache--2.0-slate)

Prescripta e um sistema web educacional de apoio a prescricao segura. A v0.6.0 amplia seguranca clinica e cria uma camada de interoperabilidade demonstrativa por Ports & Adapters, com importacoes pendentes, consentimento, auditoria e CDS API.

> Uso educacional/demonstrativo: Prescripta nao e dispositivo medico, nao substitui avaliacao profissional e nao deve ser usado para decisoes clinicas reais.

Prescripta e um motor de apoio a prescricao segura, preparado para integracao com sistemas clinicos via arquitetura de interoperabilidade, FHIR-like imports, adapters hospitalares, auditoria, consentimento e motor deterministico de risco.

## Preview v0.6.0

![GIF demonstrativo do Prescripta v0.6.0](docs/assets/v0.6.0/prescripta-v0.6-demo.gif)

![Importacoes clinicas](docs/assets/v0.6.0/clinical-imports-list.png)

![Plano de exposicao medicamentosa](docs/assets/v0.6.0/medication-exposure-plan.png)

![Painel CDS API](docs/assets/v0.6.0/cds-api-panel.png)

![Identificadores do paciente](docs/assets/v0.6.0/patient-identifiers.png)

## Funcionalidades

- Login JWT com perfis `admin`, `medico`, `enfermagem` e `auditor`.
- CRUD de pacientes com vocabulario clinico controlado.
- Triagem rapida com selects estruturados e auditoria.
- Catalogo farmacologico centrado em `ActiveIngredient`.
- Produtos/aliases comerciais em `DrugProduct` e `MedicationModel` compativel com versoes anteriores.
- Busca por principio ativo ou nome comercial, como `Novalgina -> dipirona`.
- Fonte e jurisdicao: `BR`, `US`, `EU`, `GLOBAL`.
- Lookup assistido Anvisa/DCB sem scraping agressivo.
- Motor deterministico de risco para alergia, dose, duracao, dose acumulada, cautelas, interacoes, comorbidades e contexto clinico.
- Exposicao medicamentosa com dose diaria, dose acumulada, uso continuo e monitoramento.
- Perfil farmacocinetico/farmacodinamico com mecanismo, metabolismo, eliminacao e CYP.
- Alertas neuropsiquiatricos e reprodutivo/ginecologicos como revisao profissional.
- Identificadores de paciente com hash/mascara e matching sem merge automatico inseguro.
- Importacoes clinicas FHIR/JSON/CSV/mock com consentimento, pending_review e aceite/rejeicao.
- Endpoint demonstrativo `POST /api/cds/prescription-check`.
- RAG interno com `jurisdiction`, `source_name`, `source_url`, `evidence_type` e `validation_status`.
- IA explicativa multi-provider com fallback deterministico, sem poder de alterar decisao.
- Auditoria automatica de acoes relevantes.

## Fonte Brasil/Anvisa/DCB

A v0.5.0 prioriza:

- Anvisa/Bulario Eletronico;
- DCB como nomenclatura brasileira oficial;
- curadoria manual demonstrativa marcada por status.

openFDA, DailyMed, FDA e RxNorm podem ser considerados no futuro como fontes secundarias, nunca como regra primaria brasileira.

## Rodar Com Script Windows

```powershell
powershell -ExecutionPolicy Bypass -File scripts/start-prescripta.ps1
```

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

| Perfil | E-mail | Senha |
| --- | --- | --- |
| Admin | `admin@prescripta.local` | `Admin@12345` |
| Medico | `medico@prescripta.local` | `Medico@12345` |
| Enfermagem | `enfermagem@prescripta.local` | `Enfermagem@12345` |
| Auditor | `auditor@prescripta.local` | `Auditor@12345` |

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

- Publicada: `v0.6.0`
- Notas: [docs/releases/v0.6.0.md](docs/releases/v0.6.0.md)
- Auditoria de profissionalizacao: [docs/product/professionalization-audit-v0.5.0.md](docs/product/professionalization-audit-v0.5.0.md)
- Fontes brasileiras: [docs/clinical-rules/brazilian-medication-sources.md](docs/clinical-rules/brazilian-medication-sources.md)

## Roadmap Resumido

- `v0.6.0`: Seguranca clinica ampliada + interoperabilidade clinica demonstrativa.
- `v0.7.0`: Importacao clinica assistida aprimorada + revisao humana avancada.
- `v0.8.0`: Relatorios, exportacao e auditoria avancada.
- `v0.9.0`: Docker/PostgreSQL/deploy.
- `v1.0.0`: versao final de portfolio.

## Documentacao

- [Visao geral da arquitetura](docs/architecture/overview.md)
- [Decisoes de arquitetura](docs/architecture/decisions.md)
- [Modelo principio ativo primeiro](docs/clinical-rules/active-ingredient-first-model.md)
- [Fontes brasileiras de medicamentos](docs/clinical-rules/brazilian-medication-sources.md)
- [Vocabulario clinico controlado](docs/clinical-rules/controlled-clinical-vocabulary.md)
- [Motor de risco](docs/clinical-rules/risk-engine.md)
- [Exposicao e uso continuo](docs/clinical-rules/medication-exposure-and-continuous-use.md)
- [Arquitetura de interoperabilidade](docs/interoperability/architecture.md)
- [CDS API](docs/interoperability/cds-api.md)
- [Consentimento e LGPD](docs/security/consent-and-lgpd.md)
- [Estrategia Anvisa/DCB](docs/data/anvisa-dcb-import-strategy.md)
- [Politica de conflito de fontes](docs/data/source-conflict-policy.md)
- [IA explicativa](docs/ai/ai-explainer.md)
- [Roadmap de integracao clinica futura](docs/interoperability/future-clinical-integration-roadmap.md)
- [Privacidade e LGPD](docs/security/privacy-and-lgpd.md)
- [Threat model basico](docs/security/threat-model-basic.md)
