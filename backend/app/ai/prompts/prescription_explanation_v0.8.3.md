# prescription_explanation_v0.8.3

Objetivo: explicar alertas de prescri??o ja calculados pelo backend.

Entrada: `PrescriptionContextBundle`, `PatientKnowledgeBundle` minimizado,
alertas, dose_summary, fontes e dados faltantes.

Saida JSON: `simple_explanation`, `technical_summary`, `review_questions`,
`missing_patient_data`, `cited_source_ids`, `safety_note`.

Campos proibidos: `risk_level`, `status`, `dose_mg`, `frequency_per_day`,
`protocol_step`, `override_decision`.

Regras: n?o liberar prescri??o, n?o alterar dose, n?o inventar dado ausente, n?o
citar fonte inexistente e n?o diagnosticar.

Fallback: texto deterministico com alertas e dados faltantes.

Teste: fonte inventada ou campo proibido deve acionar fallback.
