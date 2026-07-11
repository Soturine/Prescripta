# Roadmap Futuro de Integracao Clinica

A v0.5.0 apenas documenta esta camada. Ela n?o implementa FHIR/CDS Hooks nem integracao hospitalar real.

## Camada de Interoperabilidade Clinica

Arquitetura futura sugerida: Ports & Adapters / Hexagonal Architecture.

```text
Frontend
↓
Backend Prescripta
↓
Clinical Integration Layer
↓
Adapters
   ├── FHIR Adapter
   ├── RNDS Adapter futuro
   ├── HL7 v2 Adapter futuro
   ├── CSV/JSON Import Adapter
   ├── PDF Import Adapter
   ├── Hospital API Adapter
   └── Lab/Imagem Adapter
↓
Banco / Cache / Auditoria
```

## Estrutura futura sugerida

```text
backend/app/integrations/
  ports/
    patient_source.py
    medication_source.py
    allergy_source.py
    observation_source.py
    prescription_source.py
    document_source.py
  adapters/
    fhir/
      fhir_patient_adapter.py
      fhir_medication_adapter.py
      fhir_allergy_adapter.py
      fhir_observation_adapter.py
      fhir_bundle_importer.py
    hospital_api/
      generic_hospital_adapter.py
    files/
      csv_importer.py
      json_importer.py
      pdf_importer.py
    mock/
      mock_hospital_adapter.py
  mapping/
    fhir_mapper.py
    internal_mapper.py
    terminology_mapper.py
  services/
    integration_service.py
    patient_matching_service.py
    consent_service.py
    import_audit_service.py
```

## Portas futuras

- `PatientSourcePort`
- `MedicationSourcePort`
- `AllergySourcePort`
- `ConditionSourcePort`
- `ObservationSourcePort`
- `PrescriptionSourcePort`
- `DocumentSourcePort`

## Modelos futuros

```text
ExternalPatientIdentity
- patient_id interno
- external_system
- external_patient_id
- hospital_name
- document_hash
- created_at

ClinicalImportBatch
- id
- source_system
- imported_by
- patient_id
- consent_id
- status
- imported_at
- errors

ClinicalSourceRecord
- id
- batch_id
- record_type
- source_payload
- mapped_payload
- confidence
- accepted_by_user
- rejected_reason

ConsentRecord
- patient_id
- authorized_by
- purpose
- source_system
- valid_until
- created_at
```

## Modo CDS externo futuro

`POST /api/cds/prescription-check`

Entrada futura:

```json
{
  "patient": {},
  "medication_request": {},
  "allergies": [],
  "conditions": [],
  "current_medications": [],
  "observations": []
}
```

Saida futura:

```json
{
  "status": "blocked",
  "risk_level": "critical",
  "alerts": [],
  "cards": [],
  "audit_id": "..."
}
```

## Regras de integracao

- N?o fazer scraping de hospitais.
- N?o armazenar credenciais de portais.
- N?o prometer integracao automatica com Santa Casa, Unimed, Policlin ou qualquer hospital sem contrato/API.
- Integracoes reais exigem parceria, credenciais, contrato, seguranca e conformidade LGPD.
- RNDS/FHIR e roadmap futuro.
- Hospitais privados podem usar APIs proprias.
- Prescripta deve estar preparado por adapters, n?o por scraping.
# Atualizacao v0.6.0

Prescripta agora possui a base demonstrativa de Ports & Adapters em `backend/app/integrations`.

Essa base prepara integracoes futuras por API oficial, mas n?o implementa integracao real com hospitais, RNDS, HL7 v2 completo ou DICOM. Hospitais privados exigem contrato, credenciais oficiais, seguranca, governanca e conformidade LGPD.

N?o usar scraping, credenciais de portais ou dados reais na demo publica.

# Atualizacao v0.7.0

A camada de importa??o ganhou reconciliacao granular por item.

O servico compara dados importados com dados existentes, marca novo/duplicado/conflito/possivel match e registra aceite/rejeicao item a item. O aceite seguro ignora conflitos e duplicados.

Pendencia para v0.8.0: reconciliacao clinica avancada com mais tipos FHIR, relatorios/exportacao e filtros de auditoria.
