# prescription_explanation_v0.8.3

Objetivo: explicar alertas de prescrição ja calculados pelo backend.

Entrada: `PrescriptionContextBundle`, `PatientKnowledgeBundle` minimizado,
alertas, dose_summary, fontes e dados faltantes.

Saida JSON: `simple_explanation`, `technical_summary`, `review_questions`,
`missing_patient_data`, `cited_source_ids`, `safety_note`.

Campos proibidos: `risk_level`, `status`, `dose_mg`, `frequency_per_day`,
`protocol_step`, `override_decision`.

Regras: não liberar prescrição, não alterar dose, não inventar dado ausente, não
citar fonte inexistente e não diagnosticar.

Fallback: texto deterministico com alertas e dados faltantes.

Teste: fonte inventada ou campo proibido deve acionar fallback.
