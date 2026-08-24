# Changelog

## [0.10.0] - 2026-08-24

### Interoperability, Operations & Stabilization

- aggregate traversal budgets close numeric fail-open paths across nested payloads;
- Agent Runtime v2 chooses and executes registered tools server-side with object scope,
  server budgets, idempotency, cancellation and mandatory human review;
- governed Evidence acquisition adds provider limits, bounded retry, real process TTL cache,
  concurrency-safe plan versions and review-preserving deduplication;
- bounded FHIR R4 JSON subset preserves coding and lineage, blocks ambiguous payloads and requires
  idempotent, tenant-scoped human reconciliation;
- safe request IDs/logging, bounded metrics, PostgreSQL recovery qualification, benchmark budgets,
  OpenAPI compatibility policy and build-once release provenance;
- CodeQL 4.37.7 adopted after inspection; remaining Dependabot majors/groups deferred to v1 freeze.

This release remains synthetic/demo/educational only. It is not clinically, causally, FHIR,
SMART, regulatory or production validated.

## [0.9.3] - 2026-08-13

### Advanced Research Methods, Agentic Evidence & Security Hardening

- bounded linear numeric parsing and CDP argument isolation close the three known CodeQL findings structurally;
- independent synthetic PSM/IPTW reference fixture, richer overlap/balance diagnostics and deterministic sensitivity grids;
- PostgreSQL-authoritative NL→SQL planner budgets plus database-enforced read-only execution;
- versioned PubMed/Crossref/OpenAlex metadata acquisition with safe XML, bounded retry, rights/provenance and review-preserving dedupe;
- bounded research-agent templates with tool allowlists, budgets, audit, cancellation and mandatory human checkpoints;
- direct-main and version-tag rulesets, evidence-based stale-branch cleanup and inspection-only Dependabot review.

This release remains synthetic/demo/educational only. It makes no clinical, epidemiological,
causal, regulatory or production-readiness claim.

## [0.9.2] - 2026-08-11

### Research Copilot v2 e Comparative RWE

- comparação determinística de coortes sintéticas com Table 1, missingness, SMD, risco,
  diferença de risco, RR, OR, intervalos, pessoa-tempo e incidência;
- PSM e IPTW experimentais com estimand/configuração explícitos, overlap, balance, ESS, pesos
  extremos, abstention e salvaguardas permanentes contra alegações causais;
- Research Copilot v2 proposal-only para protocolo, conceitos, evidência e explicações, com
  grounding, proveniência, revisão humana e evals adversariais;
- Literature workspace com extração por fonte/locator e resistência a prompt injection;
- NL→SQL experimental desativado por padrão, validado por AST, limitado a view agregada e
  escopado por instituição, estudo e snapshot antes de execução humana explícita;
- ponte “Explorar em RWE” cria apenas um draft de pesquisa a partir de achado auditado;
- Research Package v3 preserva lineage comparativo, métodos e evidências sem linhas de paciente.

### Limitações

- somente dados sintéticos/demonstrativos; sem validação epidemiológica, clínica ou regulatória;
- PSM/IPTW não têm validação externa independente e não autorizam conclusão causal;
- query assistant continua default-off e o conteúdo de IA permanece proposta pendente de revisão.

## [0.9.1] - 2026-08-11

### Terminologia e OMOP parcial

- registro institucional de fontes/releases com licença, proveniência, checksum, import seguro e
  idempotente de subsets fornecidos pelo operador, busca limitada e drift;
- mappings versionados, suggestion-only e aprovados somente por revisor humano independente, com
  conceito Standard ativo, domínio compatível e falha fechada em ambiguidade;
- adapter sintético OMOP CDM 5.4 parcial para sete tabelas, preservando valores de origem e conceito
  zero quando não mapeado, com manifest, métricas, hashes e matriz de compatibilidade honesta;
- UI PT-BR/EN-US para registro, licenças, conceitos, fila de mapping, preview/export e histórico.

### Reprodutibilidade e supply chain

- Data Quality passa a ser escopado pelo cohort run/snapshot exato; outcomes revisados são fixados no
  plano e no run, sem interferência de achados ou versões não relacionados;
- Research Package v2 agrega lineage terminológico/OMOP, hashes por arquivo e verificador de
  adulteração, permanecendo aggregate-only e synthetic/demo-only;
- npm 11.18.0 e install scripts pinados por path/versão; workflow de tag produz e atesta SBOMs de
  dependências e imagens, além de checksums.

### Limitações

- DQD não foi executado; Achilles/ATLAS e readiness para rede OHDSI não são suportados.
- Nenhum vocabulário completo/licenciado é distribuído e não há validade clínica, causal,
  regulatória, OMOP completa ou RWE real.

## [0.9.0] - 2026-08-09

### Research & RWE MVP

- Study Workspace em cinco áreas com prontidão em oito etapas, protocolo e outcomes versionados,
  revisão humana independente e detalhes técnicos progressivos;
- Cohort DSL v2 declarativa, compatível com v1, com grupos `all`/`any`, profundidade e custo
  limitados, temporalidade, builder visual acessível, prévia agregada e attrition;
- Data Quality ganha runs persistidos, dimensões, acknowledgement auditado e bloqueio de análise
  apenas para finding crítico aberto;
- Analysis Plan e Research Analysis Run executam somente métodos descritivos allowlisted, com
  Table 1, missingness, prevalência com denominador/janela e hashes estáveis;
- Patient Journey falha fechado fora de fixture sintética e Research Package exporta somente
  arquivos lógicos agregados com manifesto e hashes por arquivo;
- Research Copilot v1 permanece proposal-only, estruturado e revisável; aceitação cria draft nunca
  revisado e não existe tradução de linguagem natural para SQL.

## [0.8.9] - 2026-08-09

### Qualidade e supply chain

- quality ratchets independentes elevam cobertura combinada/branches do backend e statements,
  branches, functions e lines do frontend, com validação incremental documentada;
- cenários adversariais cobrem contratos/fallback do AI Task Router, transições de Research,
  autorização farmacêutica e regras profissionais sem reduzir severidade;
- install scripts npm usam inventário fail-closed por path e versão exatos; Actions permanecem
  fixadas por SHA;
- imagens recebem scan HIGH/CRITICAL e SBOM CycloneDX; manifests de dependência e SBOMs recebem
  attestations de provenance no workflow de tag.

### Containers e operação

- imagens backend/frontend multi-stage usam bases oficiais fixadas por digest, runtime sem root,
  filesystem somente leitura, capabilities removidas e healthchecks;
- Compose inclui PostgreSQL interno, migration one-shot idempotente, dependências por health,
  segmentação de rede e limites de recursos;
- smoke reproduzível valida build, migrations, health, restart e usuários sem repetir pytest,
  Vitest ou Playwright.

### Produto, i18n e documentação

- shell healthtech light-first organiza cuidado, evidência, pesquisa e governança, com drawer e
  barra inferior mobile;
- dashboard, paciente, checagem clínica, farmácia, evidências, Research e auditoria recebem
  hierarquia e componentes de domínio com aprofundamento progressivo;
- PT-BR e EN-US usam catálogos estáticos, detecção segura, override persistido, equivalência de
  status e preservação de códigos, unidades e valores canônicos;
- ajuda contextual, guia por rota, glossário, arquitetura frontend, threat model, hazard log,
  roadmap e screenshots sintéticos foram atualizados.

## [0.8.8] - 2026-08-08

### Workflows e segurança clínica

- faixa usual de dose passa a usar contrato dimensional explícito, limites inclusivos, escopo,
  normalização corporal e precisão `Decimal`;
- transações de aplicação são centralizadas no request unit of work; serviços executam `flush()` e
  rollback inclui domínio e auditoria;
- enfermagem recebe prescrição estritamente vinculada a versão de protocolo institucional aplicável,
  credencial, vigência, vínculo e coassinatura;
- intervenções farmacêuticas ganham lifecycle, optimistic locking, idempotência, eventos,
  reconciliação por item e revisão de formulação sem alteração automática da prescrição.

### Research, RWE e evidências

- estudos, protocolos, concept sets, coortes e outcomes institucionais/versionados com revisão humana
  independente e imutabilidade após revisão;
- cohort DSL declarativa sem SQL livre, com allowlist, budget, execução determinística aggregate-first,
  attrition, snapshots e hashes canônicos;
- timeline sintética, regras iniciais de Data Quality e workspace Research com estados de permissão,
  cohort builder, runs, provenance e Copilot proposal-only;
- `EvidenceSource` e `EvidenceLink` registram fontes e relações rastreáveis sem atribuir validade
  científica automática.

### IA, segurança e dependências

- AI Task Router aplica task/template/schema, classificação, policy de provider, minimização, source
  grounding, fallback e revisão de `AIInteraction`, sem escrita do LLM no domínio;
- React Router 7.18.2 está fora da faixa afetada atualizada de `GHSA-qwww-vcr4-c8h2`; a exceção
  temporária foi encerrada e high/critical volta a falhar sem allowlist;
- backend, frontend e CodeQL receberam updates compatíveis reproduzidos em commits próprios; majors
  Node/Vite/jsdom/Lucide e o `pydantic-core` isolado foram deferidos com blockers documentados;
- `cryptography` 50.0.0 corrige `PYSEC-2026-3552`/`CVE-2026-69247`, detectado pelo `pip-audit` no
  gate final, com Fernet, credenciais e startup revalidados;
- migrations reversíveis, seeds idempotentes, testes backend/frontend/E2E, SBOMs, threat model,
  hazard log, roadmap e documentação da release foram ampliados.

## [0.8.7] - 2026-07-29

### Segurança clínica

- Quantidades dimensionais exatas para massa, volume/concentração, bases corporais, taxa, intervalo,
  duração, PRN e exposição, com arredondamento rastreado e abstention em ambiguidade.
- Relações clínicas explícitas, purpose/capability, care team/episode e break-glass governado; mesmo
  tenant deixa de conceder acesso implícito.
- Perfis profissionais por capacidades, segmento psicológico separado e override com segundo médico
  independente.

### Segurança e dependências

- Transporte externo fixado no IP validado, Host/SNI original, policies por provider, redirects/proxy
  bloqueados e limites de resposta/timeout.
- Backend, React 19.2.8, React Query, Playwright, Tailwind 4 e Actions por SHA atualizados após revisão
  individual; `pydantic-core` incompatível foi deferido corretamente.
- Risco temporário do React Router limitado por gate com expiração em 15/08/2026.

### Frontend, testes e documentação

- Novo design system e shell responsivo por capacidades, dashboards profissionais, workspaces e
  checagem dimensional com cobertura/abstention/auditoria explícitas.
- Coverage Vitest, Playwright real para autorização/dose/override, axe, snapshots visuais,
  mobile/tablet/reduced motion e estados de falha/retry/vazio.
- Capturador multiplataforma substitui a vitrine por assets fictícios v0.8.7 e manifesto SHA-256;
  auditorias, runbooks, threat model, hazard log e notas de release atualizados.

## [0.8.6] - 2026-07-29

### Segurança clínica e integridade

- Decisão canônica com cobertura explícita, abstention e precedência de `CRITICAL`/hard block.
- Dose dimensional sem peso, limite ou sexo imputado silenciosamente.
- Snapshot clínico imutável, JSON canônico versionado e relatórios históricos snapshot-only.
- CDS resolve medicamento, rulesets e fontes no backend e usa idempotência persistente.
- Override separado da decisão, com justificativa, proibição para crítico/hard block e segundo revisor.

### Segurança da aplicação e dados

- Autorização por instituição/grant de paciente e testes BOLA negativos.
- Cookie HttpOnly, lockout persistente, MFA TOTP opcional, startup seguro e health mínimo.
- SSRF com HTTPS/allowlist/IP público, explicação de IA por `audit_id`, minimização e circuit breaker
  compartilhado no banco.
- Terminologia clínica centralizada sem substring como match confirmado, idade derivada da data de
  nascimento, paginação e manifesto de exportação.

### Banco, qualidade e governança

- Alembic com upgrade/downgrade/check, PostgreSQL em CI e unit of work com rollback testado.
- Ruff, ESLint/React Hooks/acessibilidade, typecheck, Vitest, Playwright, cobertura de branches com gate
  de 80%, property-based testing, CodeQL, SCA, gitleaks e SBOM.
- `SECURITY.md`, `CODEOWNERS`, Dependabot, threat model, hazard log e runbooks operacionais.
- Claims corrigidos para demo educacional, compatibilidade parcial e busca lexical não validada.

## [8.6.0] - 2026-07-11

> Esta publicação histórica usou numeração incorreta. Seu conteúdo permanece preservado e não inclui
> retroativamente os hardenings acima. A linha correta e consolidada é `v0.8.6`.

### Corrigido

- Checker textual Python multiplataforma, sem executável `powershell` hardcoded.
- Dependências backend travadas e warnings de HTTP 422/TestClient corrigidos na origem.

### Alterado

- CI com backend Ubuntu/Windows, Vitest, smoke e `release-readiness`.
- Auditoria com contrato paginado, total, total de páginas e navegação no frontend.
- Política de publicação exige CI verde para o SHA final antes da tag.

### Documentação

- Auditoria prévia, rastreabilidade, transações, performance, acessibilidade e índice central.

## [0.8.5] - 2026-07-11

### Alterado

- Auditoria completa do repositório, documentação por audiência e matriz honesta de aceite.
- Filtros e paginação de eventos de auditoria executados no banco.
- Frontend responsivo por perfil, com design tokens e separação clínica/técnica.

### Corrigido

- Licença Apache-2.0, encoding UTF-8, acentuação, links e assets.
- Validações de Dose Intelligence, deduplicação psicotrópica e lifecycle de policy.
- Duplicação silenciosa de documentos clínicos.

### Evidência

- Capturas e GIFs reais, testes ampliados e baseline de performance documentado.

## [0.8.4] - 2026-07-11

### Adicionado

- Dose Intelligence rastreável com fórmula, unidade, faixa, limites e bases antropométricas.
- Psychotropic Safety Engine com sinais heurísticos amplos e revisão humana obrigatória.
- Política de prescrição separando autorização, regra regulatória, institucional, clínica e demo.
- Perfil clínico fictício de prescritores, prompts v0.8.4 e cartões clínicos/técnicos.
- Documentação aprofundada por audiência, matriz de aceite e assets renderizados no README.

### Corrigido

- Acentuação, mojibake e clareza de textos visíveis.
- Verificação de qualidade textual agora bloqueia termos sem acento nas áreas monitoradas.

### Segurança

- IA continua impedida de validar regra, alterar risco/dose ou criar bloqueio legal.
- Credenciais demo permanecem não verificadas e nenhuma consulta externa a CRM/CFM/RQE é feita.

Todas as mudanças relevantes deste projeto são documentadas aqui.

## [Unreleased]

### Planned

- v0.9.0: Docker/PostgreSQL/migrações/deploy demo.
- v1.0.0: versão final de portfólio.

## [0.8.3] - 2026-07-11

### Added

- Protocolos versionados em banco, execução com paciente opcional, passos
  executados e relatório persistido em `GeneratedReport` como
  `protocol_run_report`.
- Endpoints de relatório de protocolo em PDF, JSON e CSV por `run_id`, alem de
  filtro `/api/reports?target_type=protocol_run`.
- Auditoria de protocolo com filtros por protocolo, categoria, severidade,
  versão, execução, relatório, paciente, usuário, fonte, IA/fallback e data.
- Histórico clínico longitudinal com documentos, extração assistida, revisão
  humana, timeline e `PatientKnowledgeBundle` minimizado.
- Checagem com dados do paciente considerados, regra por peso, idade/faixa
  etária, altura/IMC e bundle clínico sem dado identificável por padrão.
- Regras demonstrativas para psicotrópicos, serotoninérgicos, IMAO,
  bipolaridade/mania, lítio/renal/AINEs e limiar convulsivo.
- Catálogo farmacológico ampliável com busca assistida por fonte, importação em
  lote e fila de curadoria.
- Prompts v0.8.3 por módulo em `backend/app/ai/prompts`.
- Frontend com visão clínica/tecnica, histórico/laudos no paciente, curadoria de
  medicamentos, protocolos com contexto do paciente e dashboard orientado a
  tarefa.
- Documentação por audiência, escopo médico, fluxos clínicos, IA, histórico do
  paciente, psicotrópicos e onboarding institucional.

### Security

- IA continua impedida de alterar risco, dose, status, protocolo, bloqueio ou
  decisão final.
- Dados extraidos de documentos e fontes farmacologicas ficam `pending_review`.
- Bundles enviados a IA sao minimizados e sem identificadores por padrão.
- API Key não e exposta em frontend, auditoria, relatório ou exportacao.

### Tests

- Cobertura para relatório de protocolo em `GeneratedReport`, filtros de
  auditoria, contexto de paciente em protocolo, documentos pendentes, revisão
  humana, bundle do paciente, regra por peso, IMC, psicotrópicos, IA minimizada,
  importação de catálogo e curadoria.

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
- Seeds demonstrativos de tansulosina, sertralina/ISRS e lítio demo.
- `PatientFunctionalProfile` com direcao, maquinas, altura, quedas, turno, alcool e alta atencao.
- Modo sem histórico com dados faltantes e pergunta mínima contextual.
- Cards de orientação ao paciente, contexto funcional, dados faltantes e resumo prático na checagem.
- Reconciliação clínica granular com badges, decisão por item e aceite seguro de itens sem conflito.
- Endpoints de counseling, perfil funcional e reconciliação granular.

### Changed

- Explicacao assistida inclui secao `Como explicar ao paciente` baseada no counseling ja validado no payload.
- Importacoes clínicas mantem aceite/rejeicao de lote e ganham revisão campo a campo.
- Roadmap atualizado para v0.8.0 relatórios/exportacao/auditoria, v0.9.0 Docker/PostgreSQL/deploy e v1.0.0 portfolio.

### Security

- Geração por IA/fallback fica `pending_review` e não aparece como validada.
- IA não altera status, risco, bloqueio, dose crítica ou recomendação final.
- Decisoes granulares, revisão de resumo e perfil funcional geram auditoria.

### Tests

- Backend ampliado para 58 testes.
- Mantidos testes antigos de v0.6.0.

## [0.6.0] - 2026-07-03

### Added

- Plano de exposicao medicamentosa com dose diaria, dose acumulada, duracao, uso continuo e monitoramento.
- Perfil ADME/farmacocinetico/farmacodinamico e cautelas renal/hepatica por nivel.
- Vocabulario `mental_health` e `reproductive_gynecologic`.
- Regra demonstrativa rifampicina/rifabutina + contraceptivo hormonal.
- Identificadores de paciente com hash/mascara e matching com revisão humana.
- Camada `backend/app/integrations` com ports, adapters FHIR/JSON/CSV/mock e mappers.
- Fluxo de importacoes clínicas `pending_review`, aceite/rejeicao, consentimento e auditoria.
- Endpoint `POST /api/cds/prescription-check`.
- Tela de Importacoes Clínicas e painel CDS API.

### Security

- Sem scraping, sem credenciais de portais e sem integração hospitalar real.
- IA permanece apenas explicativa e não altera decisão determinística.

## [0.5.0] - 2026-07-03

### Added

- `ActiveIngredient`, `DrugProduct`, `MedicationKnowledgeSource` e `ClinicalVocabulary`.
- Busca por princípio ativo ou alias comercial.
- Lookup assistido Anvisa/DCB.
- Seed BR com dipirona, ibuprofeno e nimesulida.
- Aliases Novalgina, Anador, Dorflex, Neosaldina e Lisador resolvendo para dipirona.
- Frontend com busca de catálogo, painel Anvisa/DCB, badges de fonte e selects clínicos controlados.
- RAG com metadados de fonte, jurisdição, tipo de evidência e status de validação.
- Documentação de fontes brasileiras, politica de conflito e interoperabilidade futura.

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
- Script Windows de execução local.

## [0.3.0] - 2026-07-02

### Added

- IA explicativa para alertas gerados por regras deterministicas.
- Endpoint protegido e fallback determinístico.
- Painel "Explicar com IA".
- Documentação, benchmark e assets de apresentacao.

## [0.2.0] - 2026-07-02

### Added

- Autenticacao JWT.
- Perfis `admin`, `médico`, `enfermagem` e `auditor`.
- Gestao de usuários.
- Auditoria com usuário responsável.

## [0.1.0] - 2026-07-02

### Added

- Backend FastAPI.
- Frontend React.
- CRUD básico de pacientes e medicamentos.
- Motor determinístico inicial.
- Auditoria, testes, documentação e CI.
