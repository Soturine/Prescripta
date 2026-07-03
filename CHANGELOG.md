# Changelog

Todas as mudancas relevantes deste projeto sao documentadas aqui.

## [Unreleased]

### Planned

- v0.7.0: Importacao clinica assistida aprimorada + revisao humana avancada.
- v0.8.0: Relatorios, exportacao e auditoria avancada.
- v0.9.0: Docker/PostgreSQL/deploy.

## [0.6.0] - 2026-07-03

### Added

- Plano de exposicao medicamentosa com dose diaria, dose acumulada, duracao, uso continuo e monitoramento.
- Perfil ADME/farmacocinetico/farmacodinamico e cautelas renal/hepatica por nivel.
- Vocabulario `mental_health` e `reproductive_gynecologic`.
- Regra demonstrativa rifampicina/rifabutina + contraceptivo hormonal.
- Identificadores de paciente com hash/mascara e matching com revisao humana.
- Camada `backend/app/integrations` com ports, adapters FHIR/JSON/CSV/mock e mappers.
- Fluxo de importacoes clinicas `pending_review`, aceite/rejeicao, consentimento e auditoria.
- Endpoint `POST /api/cds/prescription-check`.
- Tela de Importacoes Clinicas e painel CDS API.

### Security

- Sem scraping, sem credenciais de portais e sem integracao hospitalar real.
- IA permanece apenas explicativa e nao altera decisao deterministica.

## [0.5.0] - 2026-07-03

### Added

- `ActiveIngredient`, `DrugProduct`, `MedicationKnowledgeSource` e `ClinicalVocabulary`.
- Busca por principio ativo ou alias comercial.
- Lookup assistido Anvisa/DCB.
- Seed BR com dipirona, ibuprofeno e nimesulida.
- Aliases Novalgina, Anador, Dorflex, Neosaldina e Lisador resolvendo para dipirona.
- Frontend com busca de catalogo, painel Anvisa/DCB, badges de fonte e selects clinicos controlados.
- RAG com metadados de fonte, jurisdicao, tipo de evidencia e status de validacao.
- Documentacao de fontes brasileiras, politica de conflito e interoperabilidade futura.

### Changed

- `MedicationModel` ganhou campos de principio ativo, aliases, fonte, jurisdicao, status, concentracao e forma farmaceutica.
- Campos clinicos genericos sao normalizados para codigos controlados.
- Compatibilidade e grafo clinico exibem labels humanos.
- IA explicativa menciona fonte/jurisdicao e trata fontes internacionais como secundarias no contexto BR.

### Security

- IA segue sem alterar status, risco, bloqueio, dose ou recomendacao.
- Sem scraping agressivo.
- Sem integracao hospitalar real nesta versao.

## [0.4.0] - 2026-07-02

### Added

- Perfil clinico inteligente.
- Triagem rapida com auditoria.
- Dose acumulada, duracao e compatibilidade paciente-medicacao.
- RAG clinico demonstrativo.
- Clinical Context Graph.
- Alternativas avaliadas pelo motor de risco.
- Script Windows de execucao local.

## [0.3.0] - 2026-07-02

### Added

- IA explicativa para alertas gerados por regras deterministicas.
- Endpoint protegido e fallback deterministico.
- Painel "Explicar com IA".
- Documentacao, benchmark e assets de apresentacao.

## [0.2.0] - 2026-07-02

### Added

- Autenticacao JWT.
- Perfis `admin`, `medico`, `enfermagem` e `auditor`.
- Gestao de usuarios.
- Auditoria com usuario responsavel.

## [0.1.0] - 2026-07-02

### Added

- Backend FastAPI.
- Frontend React.
- CRUD basico de pacientes e medicamentos.
- Motor deterministico inicial.
- Auditoria, testes, documentacao e CI.
