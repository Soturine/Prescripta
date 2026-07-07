# Roadmap de Produto

Prescripta e um motor de apoio a prescricao segura, preparado para integracao com sistemas clinicos via arquitetura de interoperabilidade, FHIR-like imports, adapters hospitalares, auditoria, consentimento e motor deterministico de risco.

## Sequencia

- `v0.5.0` - Catalogo Brasil/Anvisa + principio ativo + vocabulario controlado.
- `v0.6.0` - Seguranca clinica ampliada + interoperabilidade clinica demonstrativa.
- `v0.7.0` - Resumo pratico de seguranca + perfil funcional + reconciliacao granular.
- `v0.8.0` - Relatorios, exportacao e auditoria avancada.
- `v0.9.0` - Docker/PostgreSQL/deploy.
- `v1.0.0` - versao final de portfolio.

## v0.6.0

Entregue. Criou a camada `backend/app/integrations/` com portas, adapters FHIR/JSON/CSV/mock, matching de paciente, deduplicacao, consentimento, auditoria de importacao e endpoint `/api/cds/prescription-check`.

Nao deve fazer scraping de hospitais, nao deve guardar credenciais de portais e nao deve prometer integracao real sem parceria/API oficial.

## v0.7.0

Entregue. Criou resumo pratico de seguranca por medicamento, extractor IA/RAG com JSON validado, perfil funcional do paciente, modo sem historico, pergunta minima contextual e reconciliacao clinica granular por item.

## Proximas versoes

- `v0.8.0` - Relatorios, exportacao e auditoria avancada; reconciliacao clinica avancada se necessario.
- `v0.9.0` - Docker/PostgreSQL/deploy.
- `v1.0.0` - versao final de portfolio.
