# Roadmap técnico e de produto

O roadmap descreve direção, não compromisso clínico ou regulatório. Mesmo a v1.0.0 continuará
demonstrativa enquanto não existir validação independente.

## v0.8.8 — Foundation for Evidence Intelligence, Research & RWE

- fechamento dos workflows profissionais de enfermagem e farmácia;
- faixa usual de dose dimensional e transações centralizadas;
- fundações versionadas de Research, Evidence, Data Quality e AI Task Router;
- vertical slice de coorte determinística com attrition, snapshot e provenance;
- hardening de dependências, advisories e supply chain.

## v0.9.0 — Research & RWE MVP

- Study Workspace completo e Cohort Builder visual;
- attrition, Patient Journey e Population Analytics;
- epidemiologia descritiva e Data Quality dashboard;
- Analysis Plan, pacote de relatórios de pesquisa e Research Copilot v1.

## v0.9.1 — Terminology & OMOP

- serviço terminológico e revisão de mappings;
- metadados ICD/CID, SNOMED CT, LOINC, RxNorm e ATC conforme licenças;
- adapter OMOP para Person, Visit, Condition, Drug Exposure, Measurement, Procedure e Observation;
- lineage de ETL, matriz de compatibilidade e exports OHDSI-ready somente onde verdadeiros.

## v0.9.2 — AI Research Copilot

- roteamento avançado por tarefa;
- extração de literatura com fonte e página;
- sugestões de conceitos, protocolo e coorte;
- explicação de journey e Data Quality, com eval suite e rota local Llama;
- NL para SQL somente depois de AST, views read-only e budgets maduros.

## v0.9.3 — Medication Safety RWE

- Signal Explorer e coortes exposed/comparator;
- prevalência, incidência, utilização, baseline tables, SMD, RR/OR e intervalos;
- análise comparativa descritiva;
- propensity/matching apenas após validação robusta como ferramenta de pesquisa.

## v0.9.4 — Interoperability & Operational Hardening

- adapters FHIR mais amplos e workflows profissionais expandidos;
- observabilidade, performance e jobs assíncronos quando necessários;
- backup/restore, localization e metadata de policy.

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
