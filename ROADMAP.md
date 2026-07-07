# Roadmap

## v0.5.0 - Catalogo Brasil/Anvisa + principio ativo + vocabulario controlado

- ActiveIngredient e DrugProduct.
- Aliases comerciais resolvendo para principio ativo.
- Fonte/jurisdicao/status de validacao.
- Vocabulario clinico controlado.
- RAG rastreavel por fonte.

## v0.6.0 - Seguranca clinica ampliada + interoperabilidade clinica demonstrativa

- Entregue: dose acumulada, uso continuo, monitoramento, ADME, neuropsiquiatria e ginecologia/reproducao.
- Entregue: `backend/app/integrations/ports/`.
- Entregue: adapters FHIR/JSON/CSV/mock.
- Entregue: `PatientMatchingService`, `ClinicalDeduplicationService`, `ConsentService`, `IntegrationAuditService`.
- Entregue: endpoint `/api/cds/prescription-check`.
- Sem scraping de hospitais.

## v0.7.0 - Resumo pratico de seguranca + perfil funcional + reconciliacao granular

- Entregue: resumo pratico de seguranca por medicamento com fonte/RAG e revisao humana.
- Entregue: taxonomia controlada de efeitos adversos e orientacoes praticas.
- Entregue: perfil funcional do paciente e modo sem historico.
- Entregue: pergunta minima contextual para atividades de risco.
- Entregue: reconciliacao clinica granular com aceite/rejeicao por item.
- Entregue: auditoria de geracao/revisao, perfil funcional e decisoes granulares.

## v0.8.0 - Relatorios, exportacao e auditoria avancada

- Relatorios demonstrativos.
- Exportacao.
- Filtros avancados de auditoria.
- Trilhas de revisao mais completas.
- Reconciliacao clinica avancada quando necessario.

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
