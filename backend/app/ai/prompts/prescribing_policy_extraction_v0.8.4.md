# prescribing_policy_extraction_v0.8.4

Extraia em JSON estrito requisitos documentados, fonte, jurisdição, versão e tipo de política.
Sem fonte oficial clara, use `clinical_recommendation`, `institutional_policy` ou `demo_policy`;
nunca `legal_regulatory`. Toda saída permanece `pending_review` e
`requires_human_review: true`. Não declare autorização profissional nem crie bloqueio.
