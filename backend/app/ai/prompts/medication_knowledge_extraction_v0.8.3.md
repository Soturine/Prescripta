# medication_knowledge_extraction_v0.8.3

Objetivo: estruturar dados farmacologicos a partir de fonte fornecida.

Entrada: texto, URL, CSV/JSON ou base local informada pelo usuário.

Saida JSON: `active_ingredient`, `dcb_name`, `synonyms`, `brand_names`,
`therapeutic_class`, `jurisdiction`, `source_name`, `source_url`,
`validation_status`, `contraindications`, `adverse_effects`, `interactions`,
`renal_caution`, `hepatic_caution`, `psychiatric_cautions`.

Campos proibidos: `validated`, dose inventada, fonte inventada, decisão clínica.

Regras: se a fonte não trouxer dado, retornar vazio ou `unknown`; status inicial
deve ser `pending_review`.

Fallback: item minimo pendente de curadoria.

Teste: dado critico sem fonte deve ser rejeitado.
