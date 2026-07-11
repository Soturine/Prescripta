# Roadmap

## Entregue

### v0.5.0 - Catálogo Brasil/Anvisa + princípio ativo

- `ActiveIngredient`, `DrugProduct`, aliases comerciais e fonte/jurisdição/status.
- Vocabulário clínico controlado.
- RAG rastreável por fonte.

### v0.6.0 - Segurança clínica ampliada + interoperabilidade

- Dose acumulada, uso contínuo, monitoramento e perfis ADME.
- Cautelas neuropsiquiátricas e reprodutivo/ginecológicas.
- Ports & Adapters para importação clínica FHIR/JSON/CSV/mock.
- Consentimento, auditoria e endpoint `/api/cds/prescription-check`.

### v0.7.0 - Resumo prático + perfil funcional + reconciliação granular

- Resumo prático de segurança por medicamento com fonte/RAG e revisão humana.
- Taxonomia controlada de efeitos adversos e orientações práticas.
- Perfil funcional do paciente, modo sem histórico e pergunta mínima contextual.
- Reconciliação clínica granular com aceite/rejeição por item.

### v0.7.1 - Hardening, IA configurável e qualidade textual

- Configuração de provider/modelo/API Key via UI.
- Cache dinâmico de modelos e teste de conexão.
- Chave protegida no backend, nunca exposta ao frontend.
- `.env.example`, README e documentação revisados.
- Importação clínica assistida documentada como lacuna fechada da v0.7.
- Auditoria de paridade conceitual SafeDose/RicoToro sem copiar código.
- Roadmap de protocolos rápidos/emergência documentado como possibilidade futura.

### v0.8.0 - Relatórios, Evidências e Auditoria Avançada com IA

- Report Engine central com `ReportEvidenceBundle`, hash estável e templates versionados.
- Relatório técnico de prescrição, orientações ao paciente, reconciliação clínica e auditoria.
- Exportações JSON/CSV para prescrições, importações, auditoria e relatórios gerados.
- `GeneratedReport` com histórico, provider/modelo, prompt version, fallback e hash de arquivo.
- `AIReportComposer` controlado por schema, com fallback determinístico e bloqueio de campos reservados.
- Auditoria avançada com filtros, busca, detalhe, timeline e evidências da decisão.
- Frontend com tela Relatórios, botões de PDF/exportação/evidências/timeline e lazy loading de rotas.

### v0.8.1 - Product Readiness, UX, IA Hardening e Amarração Clínica

- README e documentação reposicionados como material de produto/portfólio.
- Health endpoint, health panel de IA, retry/backoff e circuit breaker simples.
- UX de dashboard, sidebar, IA, importações, relatórios, auditoria e medicamentos polida.
- Deduplicação de aliases de dipirona/metamizol e reconciliação com campos clínicos estruturados.
- Identificadores importados aceitos com hash/máscara.
- Scripts Windows de setup, dev, reset demo e checagem de instalação.
- Benchmark SafeDose v0.8.1 e registro de prompts de relatório.

### v0.8.2 - Protocolos Rápidos, Frontend Polish e README de Produto

- Central de Protocolos Rápidos com anafilaxia, PCR, convulsão, hipoglicemia,
  dor torácica/SCA, broncoespasmo e intoxicação medicamentosa.
- Execução auditada, contexto mínimo, evidência, relatório, PDF e exportações
  JSON/CSV para protocolos.
- IA explicando protocolo sem alterar fluxo, fonte, dose ou decisão.
- README reestruturado como onboarding de produto e portfólio.
- Docs novas de protocolos, UX, quickstart, troubleshooting, jornada inicial,
  créditos de assets e benchmark v0.8.2.
- Frontend com polish visual, loading/empty states melhores, dashboard e tela
  Protocolos.

### v0.8.3 - Clinical Intelligence, Historico Longitudinal e IA Assistida

- Protocolos versionados e integrados a `GeneratedReport`.
- Relatorios de protocolo em PDF, JSON e CSV por execucao.
- Auditoria avancada com filtros especificos de protocolo.
- Historico clinico do paciente com laudos/documentos, extracao assistida,
  revisao humana, timeline e `PatientKnowledgeBundle`.
- Checagem usando peso, idade, altura/IMC, alergias, medicamentos atuais,
  condicoes, perfil funcional e historico revisado quando houver regra.
- Catalogo farmacologico ampliavel com busca por fonte, importacao em lote e
  fila de curadoria.
- IA por modulo com prompts versionados e bundles minimizados.
- Visao clinica/tecnica no frontend e documentacao por audiencia.

## Próximas Versões

### v0.9.0 - Docker/PostgreSQL/deploy

- Docker Compose.
- PostgreSQL.
- Migrações.
- Deploy demonstrativo e instalação mais profissional.
- Backup/restore e separacao dev/prod.
- Hardening de seguranca de ambiente.

### v1.0.0 - Versão final de portfólio

- Fluxos estáveis.
- Documentação completa.
- Dados de exemplo revisados.
- Release final apresentável.
