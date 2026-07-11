# report_narrative_v0.8.3

Objetivo: compor narrativa tecnica ou resumida para relatorios.

Entrada: `ReportEvidenceBundle`, hashes, eventos, fontes, status de IA e
limites.

Saida JSON: `executive_summary`, `technical_narrative`, `evidence_summary`,
`limitations`, `cited_source_ids`.

Campos proibidos: mudanca de resultado, fonte inexistente, dado identificavel
novo, recomendacao final sem base.

Regras: narrar apenas o que esta no bundle e preservar aviso legal.

Fallback: narrativa deterministica do renderer.

Teste: `cited_source_ids` fora do bundle invalida a resposta.
