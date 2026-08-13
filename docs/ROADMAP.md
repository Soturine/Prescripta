# Roadmap técnico e de produto

O roadmap descreve direção, não compromisso clínico ou regulatório. Mesmo a v1.0.0 continuará
demonstrativa enquanto não existir validação independente.

## v0.8.8 — Foundation for Evidence Intelligence, Research & RWE

- fechamento dos workflows profissionais de enfermagem e farmácia;
- faixa usual de dose dimensional e transações centralizadas;
- fundações versionadas de Research, Evidence, Data Quality e AI Task Router;
- vertical slice de coorte determinística com attrition, snapshot e provenance;
- hardening de dependências, advisories e supply chain.

## v0.8.9 — Quality Ratchet, Containers, Healthtech UX, i18n e User Guidance

- cobertura independente mais alta e testes adversariais para IA, Research, Farmácia e escopo clínico;
- imagens reprodutíveis, Compose com PostgreSQL/migração e hardening sem root;
- scan e SBOM de imagens, política de install scripts e provenance de release;
- shell healthtech e workspaces de decisão, farmácia, evidência, pesquisa, paciente e auditoria;
- PT-BR/EN-US com equivalência de status e valores canônicos preservados;
- guia do usuário por rota, ajuda contextual e screenshots atuais.

## v0.9.0 — Research & RWE MVP

- entregue: Study Workspace completo e Cohort Builder visual sobre DSL v2;
- entregue: attrition, Patient Journey sintética fail-closed e Population Analytics;
- entregue: epidemiologia descritiva, small-cell suppression e Data Quality dashboard;
- entregue: Analysis Plan, Research Package aggregate-only e Research Copilot v1 proposal-only.

## v0.9.1 — Terminology & OMOP

- serviço terminológico e revisão de mappings;
- metadados ICD/CID, SNOMED CT, LOINC, RxNorm e ATC conforme licenças;
- adapter OMOP para Person, Visit, Condition, Drug Exposure, Measurement, Procedure e Observation;
- lineage de ETL, matriz de compatibilidade e exports OHDSI-ready somente onde verdadeiros.

## v0.9.2 — Research Copilot v2, Medication Safety RWE e Comparative Analytics

- entregue: ponte auditada Medication Safety → draft de estudo e Signal Explorer sintético;
- entregue: coortes exposed/comparator, Table 1, missingness, SMD, medidas comparativas,
  pessoa-tempo e incidência com denominadores explícitos;
- entregue como experimental: PSM/IPTW com diagnósticos, abstention e sem conclusão causal;
- entregue: Copilot v2 proposal-only, extração/síntese grounded e evals adversariais;
- entregue como piloto default-off: NL→SQL por AST sobre view agregada e execução humana.

## v0.9.3 — Advanced Research Methods, Agentic Evidence & Security Hardening

- entregue: referência numérica independente, sensitivity grids e diagnósticos de PSM/IPTW;
- entregue: planner PostgreSQL autoritativo e transação read-only para NL→SQL default-off;
- entregue: aquisição de metadados PubMed/Crossref/OpenAlex com rights e provenance;
- entregue: workflows agentes limitados com allowlist, budgets e checkpoint humano;
- entregue: hardening CodeQL, CDP e governança de histórico/tags.

## v0.9.4 — Interoperability & Operational Hardening

- adapters FHIR mais amplos e workflows profissionais expandidos;
- observabilidade, performance e jobs assíncronos quando necessários;
- backup/restore, localization e metadata de policy.
- avaliação humana estruturada do Copilot e corpus licenciado/curado em escala;
- benchmarks maiores e filas assíncronas somente quando evidência de carga justificar.

## v0.10.0 — Stabilization

- estabilidade de API/schema e garantias de migration;
- CI de reprodutibilidade, benchmarks e deprecações;
- remediação de security review/pentest;
- acessibilidade, performance e limpeza documental.

## v1.0.0 — Stable Demonstrative Platform

- três pilares maduros;
- contratos estáveis, provenance e governança de IA maduros;
- demos de pesquisa reproduzíveis;
- nenhuma grande feature incompleta.

Validação clínica/regulatória, QMS, LGPD institucional, pentest, interoperabilidade oficial e
implantação produtiva permanecem programas externos ao roadmap de código.
