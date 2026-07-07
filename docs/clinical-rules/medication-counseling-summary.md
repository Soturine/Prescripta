# Medication Counseling Summary

`MedicationCounselingSummary` e o resumo pratico de seguranca do medicamento.

Ele nao decide risco e nao altera o resultado da prescricao. O motor deterministico continua sendo a fonte de `status`, `risk_level`, bloqueio, dose critica e recomendacao final.

## Campos principais

- medicamento ou principio ativo;
- `source_id`, fonte, URL, jurisdicao e versao;
- `validation_status`: `pending_review`, `curated`, `validated`, `rejected`, `obsolete`;
- `generated_by`: `ai_provider`, `fallback_deterministic`, `manual_curated`, `seed_demo`;
- efeitos principais, avisos de atividades, sinais de alerta e monitoramento;
- resumo para paciente e resumo profissional;
- evidencia extraida.

## Regras

- Resumos gerados ficam `pending_review`.
- Resumos `curated` ou `validated` tem prioridade de cache.
- Resumo pendente nunca aparece como validado.
- Fonte alterada exige nova revisao.
- Profissional/admin pode revisar; auditor e enfermagem podem visualizar conforme permissao.

## Uso na checagem

A checagem de prescricao inclui `patient_counseling`, `missing_data_mode` e `contextual_question`. Esses campos sao orientativos e nao rebaixam risco nem desbloqueiam prescricao.
