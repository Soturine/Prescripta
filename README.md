# Prescripta

![Versão](https://img.shields.io/badge/versão-v8.6.0-087f8c)
![CI](https://github.com/Soturine/Prescripta/actions/workflows/ci.yml/badge.svg)
![Backend](https://img.shields.io/badge/backend-FastAPI-009688)
![Frontend](https://img.shields.io/badge/frontend-React-149eca)
![Testes](https://img.shields.io/badge/qualidade-pytest%20%7C%20Ruff%20%7C%20TypeScript-16a34a)
![Licença](https://img.shields.io/badge/licença-Apache--2.0-f59e0b)

O Prescripta é um produto demonstrativo de portfólio healthtech para organizar contexto, checar
regras rastreáveis e documentar revisão de prescrições. A v8.6.0 consolida backend, frontend,
catálogo, dose, psicotrópicos, policy, IA assistiva, relatórios e auditoria em uma experiência mais
coesa e transparente.

> **Aviso educacional:** não é dispositivo médico, não possui validação clínica e não deve ser
> usado para atendimento real. Não substitui médico, farmacêutico, enfermagem, bula, protocolo,
> autoridade sanitária, análise jurídica ou decisão institucional. Use somente dados fictícios.

## Sumário

- [O que é e que problema resolve](#o-que-é-o-prescripta)
- [Públicos e funcionamento](#para-quem-serve)
- [Módulos](#módulos-e-abas)
- [Motores clínicos](#checagem-de-prescrição)
- [IA, relatórios e auditoria](#ia-no-prescripta)
- [Demonstração visual](#screenshots-reais)
- [Instalação e primeiro uso](#instalação-rápida)
- [Arquitetura, segurança e limites](#arquitetura)

## O que é o Prescripta

É uma aplicação web com API FastAPI, frontend React e persistência SQLAlchemy. Ela reúne dados
fictícios do paciente, exposição informada, regras determinísticas, evidências, orientações e trilha
de auditoria. A inteligência artificial é opcional, minimizada e substituível por fallback local.

O [tour do produto](docs/product/product-tour.md) percorre os fluxos principais. O índice
[Documentação do Prescripta](docs/README.md) conecta guias clínicos, técnicos e por audiência.

## Que problema resolve

Uma checagem não é apenas comparar um número: unidade, frequência, via, peso, altura, histórico,
medicamentos concomitantes, fonte e vigência mudam a interpretação. O Prescripta torna essas
dependências visíveis, separa incerteza de bloqueio e registra por que um alerta apareceu.

## Para quem serve

- **Leigos e avaliadores:** entender o fluxo e os limites de um protótipo healthtech.
- **Médicos:** revisar contexto, dose, interações e dados faltantes sem falsa segurança.
- **Enfermagem:** registrar e visualizar contexto, orientação e escalonamento permitido.
- **Administração:** manter usuários, catálogo, fontes, IA e políticas demo.
- **Auditoria/TI:** reconstruir decisão, hash, provider, source IDs, integrações e fallback.

## Como funciona em linguagem simples

O usuário escolhe paciente e medicamento fictícios, informa dose, frequência, via e duração. O
backend aplica regras cadastradas e devolve resultado geral, Dose Intelligence, sinais
psicotrópicos, policy do prescritor, lacunas e fontes. IA pode explicar o pacote já calculado, mas
não muda a decisão. Tudo relevante fica auditado.

## Fluxo geral

```text
Paciente + medicamento + exposição
              ↓
Contexto e dados faltantes
              ↓
Risco determinístico ─ Dose ─ Psicotrópicos ─ Policy
              ↓
Revisão humana + orientação + relatório
              ↓
EvidenceBundle, hash e auditoria
```

## Módulos e abas

| Módulo | O que o usuário vê | O que significa |
| --- | --- | --- |
| Dashboard | volume, alertas e qualidade do catálogo | transparência operacional, não cobertura clínica |
| Pacientes | perfil, fatores, documentos e timeline | contexto disponível e lacunas |
| Medicamentos | DCB, aliases, fonte, dose, policy e counseling | dado cadastrado com status de revisão |
| Checagem | resultado clínico e drawer/detalhes técnicos | revisão assistida, não prescrição automática |
| Protocolos | versões, etapas, fontes e execução | fluxo demonstrativo auditado |
| Importações | lotes e reconciliação item a item | dado externo não é aplicado silenciosamente |
| Relatórios | preview, PDF/JSON/CSV, evidência e hash | representação do bundle no momento da geração |
| Auditoria | filtros server-side, timeline e evidência | reconstrução de ações e decisões |
| IA assistiva | provider, modelo, fallback e limitação | explicação/extração, nunca decisão |

## Dashboard

Mostra pacientes, medicamentos, checagens, alertas e indicadores reais de curadoria: princípios
ativos, itens pendentes, demo, sem fonte, sem regra de dose, sem policy e com counseling. Um número
alto de medicamentos não significa catálogo completo.

## Pacientes

Cadastro fictício com antropometria, alergias, condições, medicamentos atuais, saúde mental,
fatores reprodutivos e perfil funcional. Dados ausentes aparecem como ausentes; não viram “não”.

## Histórico, laudos e documentos

Documentos textuais/metadados recebem hash, fonte e revisão. Duplicatas pela chave paciente + hash
+ tipo + data + origem geram conflito explícito. Extrações por IA/fallback ficam pendentes até
revisão humana. Não há OCR ou storage binário produtivo.

## Medicamentos e catálogo farmacológico

O catálogo é centrado em princípio ativo e aceita aliases/produtos. Fonte, jurisdição e status
acompanham o registro. Seeds são artificiais; regras sem curadoria não são mostradas como validadas.

## Checagem de prescrição

A checagem cruza alergia, interação, exposição, condições, histórico e regras específicas. A visão
clínica é padrão. Detalhes técnicos aparecem apenas para perfis adequados e incluem fórmulas, JSON,
source IDs, graph e evidências.

## Dose Intelligence

Calcula referência fixa, por peso real/ideal/ajustado, massa magra ou superfície corporal quando a
regra tem fonte e status. Separa dose por administração, diária, procedimento e acumulada; valida
unidade, rota e inputs. Nunca escolhe a dose final.

## Segurança psicotrópica

Sinais determinísticos cobrem serotoninérgicos, mania/psicose, convulsão, sedação, álcool,
depressão respiratória, QT, lítio, valproato, carbamazepina, lamotrigina, clozapina, metadona,
antipsicóticos e carga anticolinérgica. A chave estável evita duplicação por alias. Sinal é risco a
revisar, não diagnóstico.

## Política do prescritor

Separa autorização de sistema, regra legal/regulatória documentada, policy institucional,
recomendação clínica e demo. Exibe fonte, versão, vigência, instituição, segunda revisão e condição
de override. CRM/RQE demo permanece `demo_unverified`; nenhuma consulta externa é feita.

## Protocolos rápidos

Protocolos versionados podem receber paciente opcional, registrar etapas e gerar relatório. IA
explica apenas estrutura e fontes fornecidas; não cria dose, etapa ou conduta.

## Importações e reconciliação

Adapters mock aceitam formatos FHIR-like, JSON e CSV. Cada item é comparado ao contexto local e só
é aplicado após decisão humana auditada. Integração real exige API oficial, contrato, segurança e
base legal.

## Relatórios

Prescription, patient guidance, reconciliation, audit e protocol usam `GeneratedReport` quando
aplicável, com target, versão, template, hash, provider/modelo, fallback e anonimização. Narrativa
inválida ou com fonte inexistente é rejeitada.

## Auditoria

Filtros de usuário, paciente, medicamento, princípio ativo, protocolo, policy, especialidade, dose,
IA, fallback, fonte, jurisdição e data são aplicados no banco com ordenação e paginação. SQLite
ainda limita consultas estruturadas profundas em JSON.

## IA no Prescripta

Providers configuráveis incluem fallback, OpenAI, Gemini, Ollama e compatíveis com OpenAI. A chave
fica no backend e nunca em `localStorage`. Structured output e source locking protegem módulos
clínicos. Falha externa mantém fallback e auditoria; a IA não valida regra nem altera dose/risco.

## Visão clínica e visão técnica

A visão clínica reduz ruído e prioriza ação humana. A técnica apresenta fórmula, inputs, JSON,
policy, fontes, hash e metadados. Enfermagem não recebe o seletor técnico da checagem; autorização
real continua no backend.

## Integração institucional

Consulte [contratos](docs/integration/adapter-contracts.md),
[mapeamento](docs/integration/mapping-strategy.md),
[segurança/LGPD](docs/integration/security-and-lgpd.md) e
[payloads fictícios](docs/integration/sample-payloads.md).

## Screenshots reais

Capturas feitas na aplicação v8.6.0 rodando localmente com banco temporário e seeds fictícios. Cada
arquivo foi gerado novamente; o checker rejeita hashes duplicados nesta versão.

<table><tr><td><img src="docs/assets/v8.6.0/dashboard-clinical-v8.6.0.png" width="440" alt="Dashboard clínico"></td><td><img src="docs/assets/v8.6.0/dashboard-admin-v8.6.0.png" width="440" alt="Dashboard administrativo"></td></tr><tr><td>Dashboard clínico</td><td>Dashboard administrativo</td></tr></table>

<table><tr><td><img src="docs/assets/v8.6.0/patients-list-v8.6.0.png" width="440" alt="Lista de pacientes"></td><td><img src="docs/assets/v8.6.0/patient-details-v8.6.0.png" width="440" alt="Detalhes do paciente"></td></tr><tr><td>Pacientes</td><td>Histórico e documentos</td></tr></table>

<table><tr><td><img src="docs/assets/v8.6.0/medications-catalog-v8.6.0.png" width="440" alt="Catálogo"></td><td><img src="docs/assets/v8.6.0/medication-curation-v8.6.0.png" width="440" alt="Curadoria"></td></tr><tr><td>Catálogo farmacológico</td><td>Fila de curadoria</td></tr></table>

<table><tr><td><img src="docs/assets/v8.6.0/prescription-clinical-v8.6.0.png" width="440" alt="Checagem clínica"></td><td><img src="docs/assets/v8.6.0/prescription-technical-v8.6.0.png" width="440" alt="Checagem técnica"></td></tr><tr><td>Visão clínica</td><td>Visão técnica</td></tr></table>

<table><tr><td><img src="docs/assets/v8.6.0/dose-intelligence-v8.6.0.png" width="280" alt="Dose Intelligence"></td><td><img src="docs/assets/v8.6.0/psychotropic-safety-v8.6.0.png" width="280" alt="Psychotropic Safety"></td><td><img src="docs/assets/v8.6.0/prescribing-policy-v8.6.0.png" width="280" alt="Policy"></td></tr><tr><td>Dose</td><td>Psicotrópicos</td><td>Policy</td></tr></table>

<table><tr><td><img src="docs/assets/v8.6.0/protocols-list-v8.6.0.png" width="280" alt="Protocolos"></td><td><img src="docs/assets/v8.6.0/imports-v8.6.0.png" width="280" alt="Importações"></td><td><img src="docs/assets/v8.6.0/reports-v8.6.0.png" width="280" alt="Relatórios"></td></tr><tr><td>Protocolos</td><td>Importações</td><td>Relatórios</td></tr></table>

<table><tr><td><img src="docs/assets/v8.6.0/audit-v8.6.0.png" width="280" alt="Auditoria"></td><td><img src="docs/assets/v8.6.0/ai-settings-v8.6.0.png" width="280" alt="IA"></td><td><img src="docs/assets/v8.6.0/users-specialties-v8.6.0.png" width="280" alt="Usuários"></td></tr><tr><td>Auditoria</td><td>IA assistiva</td><td>Usuários e especialidades</td></tr></table>

<table><tr><td><img src="docs/assets/v8.6.0/mobile-v8.6.0.png" width="260" alt="Mobile"></td><td><img src="docs/assets/v8.6.0/tablet-v8.6.0.png" width="420" alt="Tablet"></td></tr><tr><td>390 × 844</td><td>768 × 1024</td></tr></table>

## GIFs

![Fluxo principal](docs/assets/v8.6.0/prescripta-v8.6.0-main-demo.gif)

Também estão disponíveis fluxos [clínico](docs/assets/v8.6.0/prescripta-v8.6.0-clinical-flow.gif),
[administrativo](docs/assets/v8.6.0/prescripta-v8.6.0-admin-flow.gif),
[auditoria](docs/assets/v8.6.0/prescripta-v8.6.0-audit-flow.gif) e
[mobile](docs/assets/v8.6.0/prescripta-v8.6.0-mobile-flow.gif).

## Instalação rápida

Windows:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/setup-dev.ps1
powershell -ExecutionPolicy Bypass -File scripts/dev.ps1
```

Linux/macOS:

```bash
./scripts/setup-dev.sh
./scripts/dev.sh
```

## Instalação detalhada

Requer Python 3.12+, Node 24+ e npm. Copie `.env.example` para `.env`, troque segredos de demo se
necessário e siga o [setup local](docs/getting-started/local-setup.md). Backend usa porta 8000 e
frontend 5173 por padrão.

## Primeiro uso

1. Entre como admin e confirme status da IA.
2. Abra um paciente fictício e revise dados/documentos.
3. Escolha uma checagem de exemplo.
4. Compare visão clínica e técnica.
5. Gere relatório e abra auditoria.

## Credenciais demo

| Perfil | E-mail | Senha |
| --- | --- | --- |
| Admin | `admin@prescripta.local` | `Admin@12345` |
| Médico geral | `médico@prescripta.local` | `Médico@12345` |
| Anestesiologia | `anestesia@prescripta.local` | `Anestesia@12345` |
| Psiquiatria | `psiquiatria@prescripta.local` | `Psiquiatria@12345` |
| Auditoria | `auditor@prescripta.local` | `Auditor@12345` |
| Enfermagem | `enfermagem@prescripta.local` | `Enfermagem@12345` |

## Configuração de IA

Somente admin salva/testa/ativa provider ou modelo. Sem chave e chamadas externas desabilitadas, o
fallback é esperado. Nunca capture a tela com chave preenchida.

## Testes

```powershell
cd backend
..\.venv\Scripts\python -m ruff check . --no-cache
..\.venv\Scripts\python -m pytest
cd ..\frontend
npm run lint
npm run build
cd ..
powershell -ExecutionPolicy Bypass -File scripts/check-text-quality.ps1
git diff --check
```

## Arquitetura

Regras determinísticas ficam em services, contratos em domain/schemas, SQLAlchemy em database e
repositories, integrações em ports/adapters e relatórios em EvidenceBundles. Rotas coordenam
casos de uso; React não decide risco. Consulte a
[visão de módulos](docs/product/system-modules.md) e a
[auditoria v0.8.5](docs/audits/v0.8.5-full-repository-audit.md).

## Estrutura do repositório

```text
backend/app/     API, domínio, serviços, banco, IA, RAG, relatórios e integrações
backend/tests/   testes unitários e de API
frontend/src/    páginas, componentes, configurações, serviços e tipos
docs/            produto, arquitetura, públicos, auditorias e assets
examples/        payloads estritamente fictícios
scripts/         instalação, execução, smoke test e qualidade
```

## Segurança e privacidade

Não use dados reais. Segredos ficam no backend, dados enviados à IA são minimizados, identificadores
são mascarados/hasheados quando aplicável e ações relevantes são auditadas. A demo não faz
scraping agressivo nem autenticação em portal institucional.

## Limitações atuais

Leia [limitações conhecidas](docs/product/known-limitations.md) e a
[matriz de aceite](docs/product/v0.8.5-acceptance-matrix.md). Catálogo, policy e regras de dose são
demonstrativos/pendentes quando indicado. Assets v0.8.4 não são usados como evidência v0.8.5.

## Roadmap

A v0.9.0 prevê Docker, PostgreSQL, Alembic, deploy demo, storage, backup/restore e hardening de
ambiente. Consulte o [ROADMAP](ROADMAP.md).

## Licença

Licenciado sob [Apache License 2.0](LICENSE).
