# Arquitetura de Interoperabilidade Clinica

Prescripta v0.6.0 cria uma camada demonstrativa de Ports & Adapters em `backend/app/integrations`.

## Principios

- Adapters recebem dados externos e produzem registros internos pendentes.
- Portas definem contratos para paciente, medicamentos, alergias, condicoes, observacoes, prescricoes e documentos.
- Importação exige consentimento ou base legal aplicavel.
- Nenhum dado importado entra automaticamente no perfil definitivo.
- Aceite/rejeicao dependem de revisão humana e auditoria.
- A camada prepara FHIR/RNDS/HL7/CDS Hooks futuros, mas não implementa integracao real.

## Estrutura

- `ports/`: contratos com `Protocol`.
- `adapters/fhir`: importação demonstrativa de Bundle e recursos comuns.
- `adapters/json`: payload generico simples.
- `adapters/csv`: CSV de medicamentos/condicoes simples.
- `adapters/mock`: fonte hospitalar simulada.
- `mapping/`: mapeamento FHIR, interno e terminologico.
- `services/`: consentimento, auditoria, matching, deduplicacao e orquestracao.

## Limites

Sem scraping de hospitais, sem credenciais de portais, sem RNDS real, sem HL7 v2 completo e sem DICOM real.

