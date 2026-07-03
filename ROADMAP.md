# Roadmap

## v0.5.0 - Catalogo Brasil/Anvisa + principio ativo + vocabulario controlado

- ActiveIngredient e DrugProduct.
- Aliases comerciais resolvendo para principio ativo.
- Fonte/jurisdicao/status de validacao.
- Vocabulario clinico controlado.
- RAG rastreavel por fonte.

## v0.6.0 - Camada de Interoperabilidade Clinica / Ports & Adapters

- `backend/app/integrations/ports/`.
- Adapters FHIR/JSON/CSV/mock.
- `PatientMatchingService`.
- `ClinicalDeduplicationService`.
- `ConsentService`.
- `IntegrationAuditService`.
- Endpoint futuro `/api/cds/prescription-check`.
- Sem scraping de hospitais.

## v0.7.0 - Importacao clinica assistida + FHIR Bundle + JSON/CSV

- Importacao assistida.
- FHIR Bundle demonstrativo.
- Importacao JSON/CSV.
- Validacao e aceite pelo usuario.

## v0.8.0 - Relatorios, exportacao e auditoria avancada

- Relatorios demonstrativos.
- Exportacao.
- Filtros avancados de auditoria.
- Trilhas de revisao mais completas.

## v0.9.0 - Docker/PostgreSQL/deploy

- Docker Compose.
- PostgreSQL.
- Migracoes.
- Deploy demonstrativo.

## v1.0.0 - Versao final de portfolio

- Fluxos estaveis.
- Documentacao completa.
- Dados demonstrativos revisados.
- Release pronta para portfolio.
