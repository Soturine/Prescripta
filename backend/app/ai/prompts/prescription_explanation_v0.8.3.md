# prescription_explanation_v0.8.3

Objetivo: explicar alertas de prescricao ja calculados pelo backend.

Entrada: `PrescriptionContextBundle`, `PatientKnowledgeBundle` minimizado,
alertas, dose_summary, fontes e dados faltantes.

Saida JSON: `simple_explanation`, `technical_summary`, `review_questions`,
`missing_patient_data`, `cited_source_ids`, `safety_note`.

Campos proibidos: `risk_level`, `status`, `dose_mg`, `frequency_per_day`,
`protocol_step`, `override_decision`.

Regras: nao liberar prescricao, nao alterar dose, nao inventar dado ausente, nao
citar fonte inexistente e nao diagnosticar.

Fallback: texto deterministico com alertas e dados faltantes.

Teste: fonte inventada ou campo proibido deve acionar fallback.
