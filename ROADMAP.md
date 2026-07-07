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

## Próximas Versões

### v0.8.0 - Relatórios, exportação e auditoria avançada

- Relatórios de checagens, orientações e importações.
- Exportação demonstrativa.
- Filtros avançados de auditoria.
- Reconciliação clínica avançada se necessário.

### v0.8.x - Protocolos rápidos / emergência, se priorizado

- Apenas com fonte/protocolo validado e revisão clínica.
- Possíveis fluxos: PCR, anafilaxia, IAM, crise convulsiva e cálculo por peso.

### v0.9.0 - Docker/PostgreSQL/deploy

- Docker Compose.
- PostgreSQL.
- Migrações.
- Deploy demonstrativo.

### v1.0.0 - Versão final de portfólio

- Fluxos estáveis.
- Documentação completa.
- Dados de exemplo revisados.
- Release final apresentável.
