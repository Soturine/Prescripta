# FHIR Mapping Demonstrativo

A v0.6.0 reconhece um subconjunto educacional de FHIR Bundle JSON.

## Recursos reconhecidos

- `Patient`
- `AllergyIntolerance`
- `Condition`
- `MedicationStatement`
- `MedicationRequest`
- `Observation`
- `DiagnosticReport`
- `DocumentReference`

## Saida interna

Cada recurso vira `ClinicalSourceRecord` com:

- `source_payload`: recurso original.
- `mapped_payload`: valor normalizado demonstrativo.
- `confidence`: confianca aproximada.
- `record_type`: tipo interno.

O mapeamento não e FHIR completo e não substitui validação institucional.
