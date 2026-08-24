# Estado atual do projeto

O Prescripta v1.0.0 é a release estável publicada do portfólio healthtech demonstrativo, executável em FastAPI, React/TypeScript e SQLAlchemy. Pode rodar nativamente com SQLite para desenvolvimento ou em uma stack Docker Compose reprodutível com PostgreSQL. Não é produto clínico validado nem pronto para operação hospitalar.

## Capacidades disponíveis

- Medication Safety com decisão determinística, cobertura, abstention, dose dimensional, snapshot e override governado;
- pacientes, perfil funcional, protocolos, importações e reconciliação granular;
- farmácia clínica com proposta separada da decisão humana;
- Evidence Intelligence com fontes versionadas, vínculos e recuperação educacional;
- Research & RWE demonstrativo com estudos, concept sets, coortes, attrition, runs, proveniência e Data Quality;
- IA assistiva opcional, limitada por tarefa, schema, fonte, revisão e fallback;
- relatórios, exportações e auditoria pseudonimizada;
- shell healthtech responsivo, PT-BR/EN-US e ajuda contextual por rota;
- CI com quality ratchets independentes, testes adversariais, SAST/SCA, secret scan, SBOM, imagens escaneadas e provenance de release.

## Execução e segurança

O backend é a autoridade de permissão e regra clínica. A interface nunca calcula risco. A stack Compose usa serviços separados para migração, API, frontend e PostgreSQL; imagens da aplicação executam sem root, com filesystem somente leitura, capabilities removidas, healthchecks e limites. O banco não publica porta no host por padrão.

## Limites atuais

Dados e rulesets são sintéticos ou demonstrativos. Não há validação clínica, regulatória ou institucional, FHIR/SMART/CDS Hooks completos, OIDC/BFF, DLP, WORM, pentest independente, small-cell suppression formal ou validação epidemiológica externa. PostgreSQL é o alvo operacional da stack; SQLite permanece apenas para desenvolvimento local.
