# Changelog

Todas as mudanças relevantes deste projeto são documentadas aqui.

## [Unreleased]

### Planned

- v0.9.0: Docker/PostgreSQL/migrações/deploy demo.
- v1.0.0: versão final de portfólio.

## [0.8.3] - 2026-07-11

### Added

- Protocolos versionados em banco, execucao com paciente opcional, passos
  executados e relatorio persistido em `GeneratedReport` como
  `protocol_run_report`.
- Endpoints de relatorio de protocolo em PDF, JSON e CSV por `run_id`, alem de
  filtro `/api/reports?target_type=protocol_run`.
- Auditoria de protocolo com filtros por protocolo, categoria, severidade,
  versao, execucao, relatorio, paciente, usuario, fonte, IA/fallback e data.
- Historico clinico longitudinal com documentos, extracao assistida, revisao
  humana, timeline e `PatientKnowledgeBundle` minimizado.
- Checagem com dados do paciente considerados, regra por peso, idade/faixa
  etaria, altura/IMC e bundle clinico sem dado identificavel por padrao.
- Regras demonstrativas para psicotropicos, serotonergicos, IMAO,
  bipolaridade/mania, litio/renal/AINEs e limiar convulsivo.
- Catalogo farmacologico ampliavel com busca assistida por fonte, importacao em
  lote e fila de curadoria.
- Prompts v0.8.3 por modulo em `backend/app/ai/prompts`.
- Frontend com visao clinica/tecnica, historico/laudos no paciente, curadoria de
  medicamentos, protocolos com contexto do paciente e dashboard orientado a
  tarefa.
- Documentacao por audiencia, escopo medico, fluxos clinicos, IA, historico do
  paciente, psicotropicos e onboarding institucional.

### Security

- IA continua impedida de alterar risco, dose, status, protocolo, bloqueio ou
  decisao final.
- Dados extraidos de documentos e fontes farmacologicas ficam `pending_review`.
- Bundles enviados a IA sao minimizados e sem identificadores por padrao.
- API Key nao e exposta em frontend, auditoria, relatorio ou exportacao.

### Tests

- Cobertura para relatorio de protocolo em `GeneratedReport`, filtros de
  auditoria, contexto de paciente em protocolo, documentos pendentes, revisao
  humana, bundle do paciente, regra por peso, IMC, psicotropicos, IA minimizada,
  importacao de catalogo e curadoria.

## [0.8.2] - 2026-07-11

### Added

- Central de Protocolos Rápidos com sete fluxos demonstrativos de urgência.
- Endpoints `/api/protocols`, detalhe, execução, explicação, evidência, relatório,
  PDF e exportação JSON/CSV por evento.
- Execução auditada `protocol.run` com contexto mínimo, flags e cálculos
  demonstrativos.
- Tela **Protocolos** no frontend com filtros, passos, contexto, evidências,
  explicação e exportações.
- Docs de arquitetura de protocolos, política de fontes, UX, quickstart,
  troubleshooting, jornada inicial e benchmark v0.8.2.

### Changed

- README raiz reestruturado como guia de produto, arquitetura, módulos, setup,
  uso inicial, screenshots e limites.
- Sidebar e health visual atualizados para v0.8.2.
- Frontend recebeu polish em botões, campos, loading, empty states, layout,
  dashboard e textos visíveis.
- Roadmap reposicionado para v0.9.0 como próxima etapa principal.

### Security

- IA em protocolos é apenas explicativa e não altera passos, dose, fonte ou
  decisão.
- Protocolos mantêm aviso educacional e exigem julgamento humano.
- Eventos de protocolo registram `secret_logged=false`.

### Tests

- Cobertura para listagem, detalhe, validação de contexto, execução, auditoria,
  relatório, exportações e explicação fallback de protocolos.

## [0.8.1] - 2026-07-10

### Added

- `/api/health` com versão, ambiente, banco e status de IA sem segredos.
- Painel de saúde de IA com provider, cache, fallback, circuit breaker e histórico recente.
- Retry/backoff para falhas transitórias de IA externa e circuit breaker simples.
- Scripts `setup-dev.ps1`, `dev.ps1`, `reset-demo-db.ps1` e `check-install.ps1`.
- Relatórios com painel de detalhe, JSON, regeneração de PDF, timeline e evidências.
- Docs de setup, registro de prompts e benchmark SafeDose v0.8.1.

### Changed

- README virou página de produto/portfólio da versão atual.
- Sidebar e dashboard exibem versão v0.8.1 e atalhos de fluxo.
- Importações usam editor de payload recolhível e linguagem de exemplo de teste.
- Medicamentos ganharam filtros e textos visíveis revisados.
- Deduplicação/reconciliação reconhecem aliases brasileiros de dipirona/metamizol.
- Condições importadas podem ser aplicadas aos campos clínicos estruturados adequados.
- PDF evita substituição destrutiva de acentos suportados por `cp1252`.

### Security

- Identificadores aceitos por reconciliação são salvos com hash/máscara.
- Health e histórico de IA não expõem API Key ou segredo.
- Fallback determinístico permanece disponível quando provider externo falha.

### Tests

- Cobertura para health, retry, circuit breaker, aliases de dipirona e identificador mascarado.

## [0.8.0] - 2026-07-10

### Added

- Motor central de relatórios em `backend/app/reports`.
- `ReportEvidenceBundle` versionado, serializável e com hash estável.
- `GeneratedReport` para histórico de relatórios gerados, hash de arquivo,
  template, provider/modelo e fallback.
- Relatório técnico de prescrição, orientações ao paciente, relatório de
  reconciliação clínica e relatório de auditoria.
- Exportações JSON/CSV para prescrições, importações, auditoria e relatórios.
- `AIReportComposer` com prompt versionado, JSON validado por Pydantic e fallback
  determinístico.
- Tela **Relatórios** no frontend.
- Auditoria avançada com filtros, busca textual, exportação, PDF, detalhe,
  timeline e evidências da decisão.
- Botões de relatório, exportação, evidências e timeline na checagem de prescrição.
- Botões de relatório e exportação na reconciliação clínica.

### Changed

- Frontend usa lazy loading por rota para reduzir o chunk inicial do Vite.
- Auditoria de checagem inclui princípio ativo, fonte, jurisdição, validação e
  eventos `prescription.alert_fired`.
- API versionada como `0.8.0`.

### Security

- Payload enviado a IA externa para relatórios é minimizado e não envia dados
  identificáveis por padrão.
- Narrativa de IA não pode retornar campos reservados nem citar `source_id`
  inexistente; caso ocorra, o backend usa fallback.
- Exportações e auditorias registram `secret_logged=false` e não incluem API Key.

### Tests

- Backend ampliado para 69 testes.
- Cobertura de PDF, preview, JSON/CSV, histórico `GeneratedReport`, permissões e
  rejeição de fonte inventada por IA em relatório.
- `npm run build` passa sem aviso de chunk maior que 500 kB.

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

- `MedicationCounselingSummary` com fonte, jurisdição, evidência extraída, cache e revisão humana.
- `MedicationCounselingExtractor` com providers GPT/Gemini/Llama/fallback e JSON validado por Pydantic.
- Taxonomia controlada de efeitos adversos e orientações práticas.
- Seeds demonstrativos de tansulosina, sertralina/ISRS e litio demo.
- `PatientFunctionalProfile` com direcao, maquinas, altura, quedas, turno, alcool e alta atencao.
- Modo sem histórico com dados faltantes e pergunta mínima contextual.
- Cards de orientação ao paciente, contexto funcional, dados faltantes e resumo prático na checagem.
- Reconciliação clínica granular com badges, decisão por item e aceite seguro de itens sem conflito.
- Endpoints de counseling, perfil funcional e reconciliação granular.

### Changed

- Explicacao assistida inclui secao `Como explicar ao paciente` baseada no counseling ja validado no payload.
- Importacoes clinicas mantem aceite/rejeicao de lote e ganham revisao campo a campo.
- Roadmap atualizado para v0.8.0 relatorios/exportacao/auditoria, v0.9.0 Docker/PostgreSQL/deploy e v1.0.0 portfolio.

### Security

- Geração por IA/fallback fica `pending_review` e não aparece como validada.
- IA não altera status, risco, bloqueio, dose crítica ou recomendação final.
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

- Sem scraping, sem credenciais de portais e sem integração hospitalar real.
- IA permanece apenas explicativa e não altera decisão determinística.

## [0.5.0] - 2026-07-03

### Added

- `ActiveIngredient`, `DrugProduct`, `MedicationKnowledgeSource` e `ClinicalVocabulary`.
- Busca por principio ativo ou alias comercial.
- Lookup assistido Anvisa/DCB.
- Seed BR com dipirona, ibuprofeno e nimesulida.
- Aliases Novalgina, Anador, Dorflex, Neosaldina e Lisador resolvendo para dipirona.
- Frontend com busca de catálogo, painel Anvisa/DCB, badges de fonte e selects clínicos controlados.
- RAG com metadados de fonte, jurisdição, tipo de evidência e status de validação.
- Documentacao de fontes brasileiras, politica de conflito e interoperabilidade futura.

### Changed

- `MedicationModel` ganhou campos de princípio ativo, aliases, fonte, jurisdição, status, concentração e forma farmacêutica.
- Campos clínicos genéricos são normalizados para códigos controlados.
- Compatibilidade e grafo clínico exibem labels humanos.
- IA explicativa menciona fonte/jurisdição e trata fontes internacionais como secundárias no contexto BR.

### Security

- IA segue sem alterar status, risco, bloqueio, dose ou recomendacao.
- Sem scraping agressivo.
- Sem integração hospitalar real nesta versão.

## [0.4.0] - 2026-07-02

### Added

- Perfil clínico inteligente.
- Triagem rápida com auditoria.
- Dose acumulada, duração e compatibilidade paciente-medicação.
- RAG clínico demonstrativo.
- Clinical Context Graph.
- Alternativas avaliadas pelo motor de risco.
- Script Windows de execucao local.

## [0.3.0] - 2026-07-02

### Added

- IA explicativa para alertas gerados por regras deterministicas.
- Endpoint protegido e fallback determinístico.
- Painel "Explicar com IA".
- Documentacao, benchmark e assets de apresentacao.

## [0.2.0] - 2026-07-02

### Added

- Autenticacao JWT.
- Perfis `admin`, `medico`, `enfermagem` e `auditor`.
- Gestao de usuarios.
- Auditoria com usuário responsável.

## [0.1.0] - 2026-07-02

### Added

- Backend FastAPI.
- Frontend React.
- CRUD básico de pacientes e medicamentos.
- Motor determinístico inicial.
- Auditoria, testes, documentação e CI.
