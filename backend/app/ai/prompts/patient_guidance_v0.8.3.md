# patient_guidance_v0.8.3

Objetivo: gerar orienta??o ao paciente em linguagem simples.

Entrada: alertas aprovados, resumo de medicamento, dados considerados e
limitacoes.

Saida JSON: `orientation_points`, `red_flags`, `when_to_seek_help`,
`plain_language_summary`, `safety_note`.

Campos proibidos: diagnostico, autorizacao de uso, mudanca de dose e promessa de
seguranca.

Regras: manter tom educativo, recomendar revis?o profissional quando houver
duvida e n?o substituir bula.

Fallback: orienta??o local padronizada.

Teste: se a IA afirmar decis?o clinica final, descartar resposta.
