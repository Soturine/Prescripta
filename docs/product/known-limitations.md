# Limitações conhecidas

Estas limitações descrevem o `main` da v1.0.0. Elas não transformam funcionalidades demonstrativas
em validação clínica, regulatória ou institucional.

## Produto e dados

- dados, pacientes, fontes e rulesets distribuídos são sintéticos, demonstrativos ou pendentes de
  revisão; não há validação clínica, legal, regulatória ou epidemiológica externa;
- não há consulta real a CRM/RQE nem conteúdo terminológico licenciado distribuído pelo projeto;
- documentos não possuem storage binário/OCR produtivo e a pseudonimização não equivale a
  anonimização;
- métricas de performance são benchmarks limitados, não SLA.

## Interoperabilidade e operação

- o importador cobre um subset delimitado de FHIR R4 JSON; não há FHIR completo, SMART App Launch,
  CDS Hooks completo ou integração hospitalar certificada;
- OMOP CDM 5.4 é parcial: DQD, Achilles/ATLAS, estudos em rede e compatibilidade externa não foram
  executados;
- PostgreSQL é o alvo da stack e das migrations Alembic; SQLite e auto-seed existem somente para
  desenvolvimento/demo local;
- faltam pentest independente, QMS, DLP/WORM e validação LGPD institucional para uso produtivo.

## Research, Evidence e IA

- Research & RWE opera sobre fixtures sintéticas e resultados agregados; PSM/IPTW e sensitivity
  diagnostics são experimentais e não sustentam inferência causal;
- NL→SQL é default-off, restrito a AST e views agregadas escopadas; execução depende de ação humana;
- IA externa é opcional e proposal-only, sem garantia de disponibilidade, custo ou qualidade;
- agentes são limitados por ferramentas, orçamento e checkpoint humano, mas não substituem revisão
  independente das fontes.

## Evidência de qualidade

Testes automatizados, regressão visual, acessibilidade, scans e Qualification demonstram conformidade
com os contratos do repositório. Eles não equivalem a validação clínica, pentest independente,
conformance oficial de interoperabilidade ou homologação hospitalar.
