# Contratos de adapters

Adapters traduzem fonte externa para DTO interno; não escrevem diretamente no prontuário. Cada
importação declara sistema, tipo, versão, consentimento, identificador externo e itens. Patient,
Medication, Allergy, Condition, Observation, Document e Prescription devem preservar código,
display, status, data e origem quando disponíveis.

Erros de campo geram conflito ou item pendente, não descarte silencioso. O contrato não promete
FHIR completo: os payloads são FHIR-like e precisam de validação institucional antes de conexão
real.
