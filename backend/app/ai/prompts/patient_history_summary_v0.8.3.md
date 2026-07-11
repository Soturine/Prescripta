# patient_history_summary_v0.8.3

Objetivo: resumir hist?rico longitudinal revisado.

Entrada: `PatientKnowledgeBundle` minimizado, documentos revisados, importacoes
aceitas, medicamentos atuais, alergias, eventos e perfil funcional.

Saida JSON: `summary`, `relevant_context`, `missing_data`, `review_questions`,
`limitations`.

Campos proibidos: identificador novo, diagnostico definitivo, conclusao de risco
sem regra.

Regras: citar apenas dados revisados ou explicitamente pendentes.

Fallback: resumo local por secoes.

Teste: se a IA incluir dado ausente, descartar.
