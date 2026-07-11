# Paginação e filtros de auditoria

`GET /api/audit` retorna `items`, `page`, `page_size`, `total`, `total_pages`, `has_next` e
`has_previous`. A consulta de contagem deriva do mesmo statement filtrado usado na listagem.

Filtros diretos — ação, recurso, risco, status, usuário e datas — são aplicados em colunas. Campos
históricos presentes somente no JSON de detalhes ainda usam busca textual no SQLite. Essa limitação
é explícita; a migração para colunas/indexes e PostgreSQL está planejada, não simulada.

O frontend mantém filtros na URL, apresenta o total e permite avançar ou retornar. Exportações
continuam recebendo o mesmo conjunto de filtros e são auditadas pelos serviços de relatório.
