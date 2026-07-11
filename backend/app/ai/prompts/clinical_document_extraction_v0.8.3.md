# clinical_document_extraction_v0.8.3

Objetivo: extrair entidades de laudo/documento clinico para revisao humana.

Entrada: texto minimizado, metadados de documento e tipo de fonte.

Saida JSON: `medications`, `allergies`, `conditions`, `exams`,
`lab_values`, `symptoms`, `adverse_events`, `mental_health_history`,
`reproductive_factors`, `observations`, `confidence`.

Campos proibidos: diagnostico novo, validacao automatica, decisao de tratamento.

Regras: tudo deve permanecer `pending_review` ate revisao humana.

Fallback: extracao deterministica simples por termos conhecidos.

Teste: a resposta nao pode aplicar dado direto ao paciente.
