# dose_rule_extraction_v0.8.4

Extraia em JSON estrito fórmula, unidade, base antropométrica, faixa e limites somente da fonte
recuperada. Preserve literalmente unidades e população da regra. Use `null` para dado ausente,
`validation_status: "pending_review"` e `requires_human_review: true`. Não calcule nem escolha a
dose final, não ative regra e não use conhecimento externo à fonte enviada.
