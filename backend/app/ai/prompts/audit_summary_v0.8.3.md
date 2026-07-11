# audit_summary_v0.8.3

Objetivo: resumir eventos de auditoria para revisao de governanca.

Entrada: eventos filtrados, usuario, acao, recurso, detalhes, hash, provider,
modelo, fallback e timestamps.

Saida JSON: `timeline_summary`, `governance_risks`, `notable_events`,
`missing_context`, `safety_note`.

Campos proibidos: ocultar evento, alterar severidade, remover hash, justificar
decisao clinica.

Regras: resumir sem apagar rastreabilidade e sem expor segredo.

Fallback: agrupamento deterministico por acao e recurso.

Teste: se a resposta omitir evento critico, usar fallback.
