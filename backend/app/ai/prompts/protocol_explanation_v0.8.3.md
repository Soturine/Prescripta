# protocol_explanation_v0.8.3

Objetivo: explicar racional e limitacoes de uma execucao de protocolo.

Entrada: protocolo, versao, passos, contexto minimo, paciente selecionado,
flags, calculos demonstrativos e evidencias.

Saida JSON: `simple_explanation`, `professional_summary`, `missing_context`,
`safety_note`, `cited_evidence_refs`.

Campos proibidos: novo passo, nova dose, alteracao de ordem, alteracao de
severidade, autorizacao de conduta.

Regras: nao mudar a estrutura do protocolo e citar apenas evidencias presentes.

Fallback: explicacao local com aviso educacional.

Teste: qualquer etapa inventada deve acionar fallback.
