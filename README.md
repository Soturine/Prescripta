# Prescripta

![Version](https://img.shields.io/badge/version-v0.8.3-blue)
![Backend](https://img.shields.io/badge/backend-FastAPI-009688)
![Frontend](https://img.shields.io/badge/frontend-React-155E75)
![License](https://img.shields.io/badge/license-Apache--2.0-slate)

Prescripta e uma plataforma educacional de apoio a prescricao segura. Ela combina
regras deterministicas, catalogo farmacologico por principio ativo, historico
clinico longitudinal, protocolos rapidos, relatorios auditaveis e IA assistiva
controlada por evidencias.

> Prescripta nao e dispositivo medico validado. Nao substitui avaliacao
> profissional, protocolo institucional, bula, regulacao medica ou decisao
> clinica. Nao use dados reais de pacientes.

## Sumario

- [O que e](#o-que-e)
- [Por que existe](#por-que-existe)
- [Para quem serve](#para-quem-serve)
- [Como funciona](#como-funciona)
- [Modulos](#modulos)
- [Fluxos principais](#fluxos-principais)
- [IA no Prescripta](#ia-no-prescripta)
- [Visao clinica e visao tecnica](#visao-clinica-e-visao-tecnica)
- [Screenshots](#screenshots)
- [Instalacao rapida](#instalacao-rapida)
- [Instalacao detalhada](#instalacao-detalhada)
- [Credenciais demo](#credenciais-demo)
- [Testes](#testes)
- [Arquitetura](#arquitetura)
- [Roadmap](#roadmap)
- [Limitacoes](#limitacoes)
- [Licenca](#licenca)

## O Que E

Prescripta e um produto de portfolio healthtech que demonstra como organizar um
sistema de apoio a prescricao com seguranca, rastreabilidade e separacao clara
entre regra clinica, interface, auditoria e IA.

Na v0.8.3, o sistema ganha historico clinico do paciente com laudos e documentos,
protocolos versionados integrados a `GeneratedReport`, bundle clinico minimizado
para IA, catalogo farmacologico ampliavel e visoes mais adequadas para medico,
enfermagem, auditoria e administracao.

## Por Que Existe

Prescricoes podem falhar por historico incompleto, duplicidade, alergias nao
revisadas, baixa rastreabilidade, documentos espalhados e excesso de confianca em
resumos manuais. Prototipos com IA ainda trazem o risco de deixar um modelo
generativo decidir o que deveria continuar deterministico.

Prescripta responde com:

- regras testaveis no backend;
- fontes, jurisdicao e status de validacao;
- revisao humana para dados importados ou extraidos;
- auditoria de checagem, protocolo, relatorio, IA e download;
- IA limitada a explicar, resumir e estruturar dados com fonte;
- fallback local quando provider externo falha ou nao esta configurado.

## Para Quem Serve

- Avaliadores nao tecnicos que querem entender o fluxo de uma prescricao.
- Medicos e enfermagem que querem ver alertas praticos e dados considerados.
- Auditores e administradores que precisam de rastreabilidade, hashes e eventos.
- Desenvolvedores/TI que querem estudar FastAPI, React, adapters, relatorios e IA
  segura.

## Como Funciona

1. Um usuario abre ou cadastra um paciente.
2. O historico clinico recebe dados estruturados, documentos, textos, importacoes
   e observacoes.
3. Dados extraidos de laudos ficam `pending_review` ate revisao humana.
4. A checagem monta um contexto clinico controlado com idade, peso, altura, IMC,
   alergias, medicamentos atuais, comorbidades, perfil funcional e documentos
   revisados.
5. O motor deterministico calcula risco, alertas, dose por peso quando houver
   regra cadastrada, cautelas por idade e fatores neuropsiquiatricos.
6. A IA pode explicar os alertas, gerar narrativa ou estruturar uma fonte, mas
   nunca altera risco, dose, status, bloqueio, protocolo ou decisao final.
7. Relatorios, exportacoes e protocolos entram em auditoria.

## Modulos

| Aba | O que faz | Acoes principais |
| --- | --- | --- |
| Dashboard | Entrada do produto e estado do ambiente. | Comece por aqui, saude da API/IA, atalhos e fluxos. |
| Pacientes | Perfil clinico, historico e documentos. | Cadastrar, editar, anexar laudo, extrair entidades, revisar timeline. |
| Historico clinico/laudos | Area dentro do paciente. | Texto colado, documentos, exames, observacoes, medicamentos anteriores e eventos. |
| Medicamentos | Catalogo e fila de curadoria. | Busca local, aliases, regra por peso, busca assistida por fonte e importacao em lote. |
| Checagem | Analise deterministica de prescricao. | Dose, via, duracao, alertas, dados considerados, orientacao e IA explicativa. |
| Protocolos | Fluxos rapidos demonstrativos. | Selecionar paciente, executar, explicar, gerar relatorio PDF/JSON/CSV. |
| Importacoes | Entrada estruturada FHIR/JSON/CSV/mock. | Consentimento, deduplicacao, aceite/rejeicao por item. |
| Relatorios | Historico de `GeneratedReport`. | Preview, PDF, JSON, CSV, hash, provider/modelo e evidencias. |
| Auditoria | Rastro de eventos e governanca. | Filtros por protocolo, paciente, usuario, IA, fonte, data, relatorio e severidade. |
| IA | Configuracao e saude operacional. | Provider/modelo, teste, fallback, cache e visibilidade sem expor chave. |
| Usuarios | Controle administrativo. | Criar contas e perfis demo. |

## Fluxos Principais

### Checar prescricao

Abra um paciente, selecione medicamento, dose, frequencia, via e duracao. A tela
mostra decisao resumida, alertas praticos, dados considerados, dados faltantes,
orientacao ao paciente e detalhes tecnicos quando permitido.

### Importar historico

Use a area de importacoes para payloads FHIR-like, JSON, CSV ou mock. Cada item
precisa de revisao humana antes de alterar o perfil do paciente.

### Anexar laudo

No detalhe do paciente, cole um texto ou registre metadados de documento. A
extracao assistida cria entidades em `pending_review`; o profissional aceita ou
rejeita antes de aplicar ao paciente.

### Consultar protocolo

Abra Protocolos, selecione o paciente se fizer sentido, informe contexto minimo e
execute. A versao do protocolo, passos, flags, calculos e dados do paciente
considerados ficam registrados.

### Gerar relatorio

Relatorios de prescricao, orientacao, auditoria, reconciliacao e protocolo entram
em `GeneratedReport`, com hash e metadados de IA/fallback.

### Configurar IA

Somente admin configura provider/modelo/API Key. Medicos, enfermagem e auditoria
veem status operacional sem ver segredo.

## IA No Prescripta

A IA pode:

- explicar alertas ja gerados;
- resumir dados faltantes;
- gerar orientacao ao paciente com linguagem controlada;
- compor narrativa de relatorio a partir de `ReportEvidenceBundle`;
- explicar protocolo sem mudar etapas;
- extrair entidades de laudo ou fonte farmacologica fornecida;
- resumir historico revisado e auditoria.

A IA nao pode:

- liberar prescricao;
- alterar risco, dose, status, protocolo ou regra critica;
- inventar fonte, diagnostico, interacao, efeito ou bula;
- salvar dado extraido como validado automaticamente;
- receber dados identificaveis por padrao.

## Visao Clinica E Visao Tecnica

Medico e enfermagem veem por padrao a visao clinica: risco, alertas, dados do
paciente considerados, perguntas sugeridas e orientacao. Score bruto, hashes,
RAG, JSON e `source_id` ficam recolhidos.

Admin e auditor podem abrir a visao tecnica: evidencias, bundle, timeline,
hashes, provider/modelo, regras disparadas e payloads auditaveis. O backend
continua sendo a fonte real de autorizacao.

## Screenshots

Assets da v0.8.3 ficam em `docs/assets/v0.8.3/`.

| Area | Imagem |
| --- | --- |
| Dashboard clinico | `docs/assets/v0.8.3/dashboard-clinical-view-v0.8.3.png` |
| Historico e laudos | `docs/assets/v0.8.3/patient-history-documents-v0.8.3.png` |
| Checagem clinica | `docs/assets/v0.8.3/prescription-clinical-view-v0.8.3.png` |
| Detalhes tecnicos | `docs/assets/v0.8.3/prescription-technical-details-v0.8.3.png` |
| Protocolos com paciente | `docs/assets/v0.8.3/protocol-patient-context-v0.8.3.png` |
| Relatorio de protocolo | `docs/assets/v0.8.3/protocol-generated-report-v0.8.3.png` |
| Fila de curadoria | `docs/assets/v0.8.3/medication-curation-queue-v0.8.3.png` |
| Mobile | `docs/assets/v0.8.3/responsive-mobile-v0.8.3.png` |

GIFs principais:

- `docs/assets/v0.8.3/prescripta-v0.8.3-main-demo.gif`
- `docs/assets/v0.8.3/prescripta-v0.8.3-patient-history-demo.gif`
- `docs/assets/v0.8.3/prescripta-v0.8.3-ai-assisted-workflow.gif`
- `docs/assets/v0.8.3/prescripta-v0.8.3-protocol-personalized-demo.gif`

## Instalacao Rapida

```powershell
powershell -ExecutionPolicy Bypass -File scripts/setup-dev.ps1
powershell -ExecutionPolicy Bypass -File scripts/check-install.ps1
powershell -ExecutionPolicy Bypass -File scripts/dev.ps1
```

URLs padrao:

- Frontend: `http://127.0.0.1:5173`
- API: `http://127.0.0.1:8000/api`
- Swagger: `http://127.0.0.1:8000/docs`
- Health: `http://127.0.0.1:8000/api/health`

## Instalacao Detalhada

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r backend\requirements.txt
cd frontend
npm install
```

Crie `.env` a partir de `.env.example` se quiser alterar banco, CORS ou IA. Para
uso local com fallback, nenhuma chave externa e obrigatoria.

Backend:

```powershell
cd backend
..\.venv\Scripts\python -m uvicorn app.main:app --reload
```

Frontend:

```powershell
cd frontend
npm run dev
```

## Credenciais Demo

| Perfil | E-mail | Senha |
| --- | --- | --- |
| Admin | `admin@prescripta.local` | `Admin@12345` |
| Medico | `medico@prescripta.local` | `Medico@12345` |
| Enfermagem | `enfermagem@prescripta.local` | `Enfermagem@12345` |
| Auditor | `auditor@prescripta.local` | `Auditor@12345` |

## Testes

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

Qualidade textual e diff:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/check-text-quality.ps1
git diff --check
```

## Arquitetura

```txt
frontend React + TypeScript
  -> cliente HTTP tipado
  -> visoes clinica/tecnica
  -> rotas protegidas por perfil

backend FastAPI
  -> schemas Pydantic
  -> services deterministicas
  -> repositories SQLAlchemy
  -> relatorios, auditoria e exports
  -> IA assistiva via AISettingsService

SQLite local demo
  -> seed artificial
  -> sem dados reais
```

Camadas de acoplamento institucional ficam em `backend/app/integrations` e docs
de onboarding explicam adapters FHIR-like, JSON, CSV, API custom, banco
institucional, mock e upload manual.

## Roadmap

- `v0.8.3`: inteligencia clinica assistida, historico longitudinal, protocolos
  integrados a relatorios, catalogo ampliavel e UX por perfil.
- `v0.9.0`: Docker, PostgreSQL, migracoes, deploy demo e hardening de ambiente.
- `v1.0.0`: versao final de portfolio com dados e docs revisados.

## Limitacoes

- Uso educacional/demonstrativo.
- Nao substitui avaliacao profissional.
- Nao acessa sistema hospitalar sem API, contrato, permissao e configuracao.
- OCR real e armazenamento de arquivos binarios ficam para etapa futura.
- Catalogo ampliado tem itens pendentes de curadoria quando nao ha fonte validada.
- Protocolos demonstrativos exigem julgamento humano e fonte institucional.

## Licenca

Apache-2.0. Veja `LICENSE`.
