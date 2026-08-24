# Documentação do Prescripta

Documentação evergreen do Prescripta v1.0.0. Guias atuais descrevem o `main`; notas e auditorias
versionadas preservam a realidade de cada release. O sistema é demonstrativo, sintético e não deve
ser usado em atendimento real.

## Começar

- [Quick Start](setup/quickstart.md)
- [Instalação local](getting-started/local-setup.md)
- [Docker e Compose](operations/docker.md)
- [Primeiro acesso](user-guide/getting-started.md)
- [Troubleshooting](setup/troubleshooting.md)

## Usar

- [Guia do usuário por tarefa](user-guide/README.md)
- [Navegação](user-guide/navigation.md)
- [Perfis, capacidades e acesso](user-guide/permissions-and-access.md)
- [Idioma PT-BR/EN-US](user-guide/language-and-localization.md)
- [Glossário](user-guide/glossary.md)
- Guias por público: [avaliação](audiences/for-laypeople-and-evaluators.md),
  [médicos](audiences/for-physicians.md), [enfermagem](audiences/for-nursing.md),
  [auditoria](audiences/for-auditors.md) e [TI/integrações](audiences/for-it-and-integrations.md)

## Entender o produto

- [Visão geral](product/product-overview.md)
- [Tour](product/product-tour.md)
- [Estado atual](product/current-project-status.md)
- [Limitações conhecidas](product/known-limitations.md)
- [Roadmap](ROADMAP.md)
- [Escopo médico e limites](product/medical-scope-and-limitations.md)

## Domínios

- **Medication Safety:** [motor de risco](clinical-rules/risk-engine.md),
  [dose](clinical/dose-intelligence.md), [farmácia](clinical-workflows/pharmacy-workflow.md) e
  [protocolos de enfermagem](clinical-workflows/nursing-protocol-prescribing.md)
- **Evidence Intelligence:** [visão geral](evidence/README.md), [fontes](evidence/source-model.md),
  [concept sets](evidence/concept-sets.md) e [Literature Copilot](evidence/literature-copilot.md)
- **Research & RWE:** [visão geral](research/README.md), [análises](research/analysis-and-package.md),
  [métodos](research/statistical-methods.md) e [guia por tarefa](user-guide/research/README.md)
- **IA:** [configuração](ai/provider-configuration.md), [Task Router](ai/task-router.md),
  [provenance](ai/ai-provenance.md) e [workflows governados](ai/agentic-research-workflows.md)
- **Interoperabilidade:** [arquitetura](interoperability/architecture.md),
  [FHIR delimitado](interoperability/fhir-mapping.md),
  [reconciliação](interoperability/clinical-reconciliation.md) e
  [OMOP parcial](architecture/terminology-and-omop-v091.md)

## Desenvolver

- [Arquitetura](architecture/overview.md) e [transações/migrations](architecture/transaction-boundaries.md)
- [Frontend](frontend/architecture.md), [design system](frontend/design-system.md),
  [informação](frontend/information-architecture.md) e [i18n](frontend/internationalization.md)
- [OpenAPI e política de compatibilidade](api/openapi-policy.json)
- [Níveis de validação](testing/validation-levels.md) e [CI/release gates](testing/ci-and-release-gates.md)
- [Assets e captura visual](assets/README.md)

## Operar e auditar

- [Operações e runbooks](operations/README.md)
- [Backup e restauração](operations/backup-and-restore.md)
- [Segurança](security/threat-model.md), [papéis](security/authentication-and-roles.md) e
  [riscos aceitos](security/accepted-risks.md)
- [Auditoria](auditing/README.md) e [relatórios](reports/README.md)
- [Releases](releases/README.md) e [auditorias históricas](audits/README.md)

**Regra de autoridade:** LLMs propose. Deterministic systems calculate. Humans approve. Sources substantiate.
