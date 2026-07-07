# Changelog

Todas as mudancas relevantes deste projeto sao documentadas aqui.

## [Unreleased]

### Planned

- v0.8.0: Relatórios, exportação e auditoria avançada.
- v0.9.0: Docker/PostgreSQL/deploy.
- v1.0.0: versão final de portfólio.

## [0.7.1] - 2026-07-07

### Added

- Tela **IA** para configurar provider, API Key, Base URL, modelo, chamadas externas e teste de conexão.
- Modelos `AIProviderCredential`, `AIProviderSettings`, `AIProviderModelCache` e `AIConfigurationAuditLog`.
- Listagem dinâmica de modelos com cache de 24 horas e refresh manual.
- Serviço central de configuração de IA usado pela explicação assistida e pelo `MedicationCounselingExtractor`.
- Script `scripts/check-text-quality.ps1` para detectar mojibake, `.env.example` comprimido e Markdown problemático.
- Documentação de configuração de provider, seleção de modelos e tratamento seguro de API Key.
- Documentos de importação clínica assistida, cenários FHIR, revisão humana e auditoria SafeDose/RicoToro.
- Roadmap de protocolos rápidos/emergência como lacuna futura, sem implementação clínica nesta versão.

### Changed

- README, roadmap e documentos centrais revisados para português correto e linguagem mais profissional.
- `.env.example` reorganizado em blocos com variáveis de IA, criptografia e providers.
- Importação/reconciliação clínica documentada como fluxo assistido com revisão humana avançada.
- O fallback determinístico permanece padrão e é acionado quando IA externa está indisponível.

### Security

- API Key nunca é retornada pela API, não é salva em `localStorage` e não entra na auditoria.
- Chaves persistidas usam criptografia com `PRESCRIPTA_CONFIG_ENCRYPTION_KEY`.
- Ambiente local sem chave de criptografia usa armazenamento em memória para credenciais via UI.
- Apenas `admin` salva, apaga, testa ou ativa provider/modelo.

### Tests

- Backend ampliado para 64 testes.
- Cobertura de chave mascarada, bloqueio de chamadas externas, uso do modelo selecionado,
  cache de modelos, modelo customizado e qualidade textual básica.

## [0.7.0] - 2026-07-07

### Added

- `MedicationCounselingSummary` com fonte, jurisdicao, evidencia extraida, cache e revisao humana.
- `MedicationCounselingExtractor` com providers GPT/Gemini/Llama/fallback e JSON validado por Pydantic.
- Taxonomia controlada de efeitos adversos e orientacoes praticas.
- Seeds demonstrativos de tansulosina, sertralina/ISRS e litio demo.
- `PatientFunctionalProfile` com direcao, maquinas, altura, quedas, turno, alcool e alta atencao.
- Modo sem historico com dados faltantes e pergunta minima contextual.
- Cards de orientacao ao paciente, contexto funcional, dados faltantes e resumo pratico na checagem.
- Reconciliacao clinica granular com badges, decisao por item e aceite seguro de itens sem conflito.
- Endpoints de counseling, perfil funcional e reconciliacao granular.

### Changed

- Explicacao assistida inclui secao `Como explicar ao paciente` baseada no counseling ja validado no payload.
- Importacoes clinicas mantem aceite/rejeicao de lote e ganham revisao campo a campo.
- Roadmap atualizado para v0.8.0 relatorios/exportacao/auditoria, v0.9.0 Docker/PostgreSQL/deploy e v1.0.0 portfolio.

### Security

- Geracao por IA/fallback fica `pending_review` e nao aparece como validada.
- IA nao altera status, risco, bloqueio, dose critica ou recomendacao final.
- Decisoes granulares, revisao de resumo e perfil funcional geram auditoria.

### Tests

- Backend ampliado para 58 testes.
- Mantidos testes antigos de v0.6.0.

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
