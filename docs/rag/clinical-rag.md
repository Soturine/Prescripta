# Busca lexical clínica demonstrativa

## Escopo honesto

O subsistema recupera trechos de Markdown por correspondência lexical. Não usa embeddings, reranker
ou avaliação clínica de retrieval; portanto, não deve ser apresentado como RAG validado. Ele não decide
status, reduz severidade, libera prescrição nem substitui bula, monografia ou protocolo vigente.

## Índice

`backend/app/knowledge/retriever.py` constrói uma vez por processo um índice imutável e versionado
`lexical-index-v1`. Documentos recebem SHA-256, são divididos em chunks de até 1.000 caracteres e
deduplicados por hash. Cada hit inclui:

- `source_id` e `chunk_id` estáveis;
- `source_hash` e versão do índice;
- trecho, score e termos encontrados;
- fonte, jurisdição, tipo de evidência e versão;
- status de validação e `valid_until` quando declarado;
- aviso educacional.

Fonte expirada produz `coverage_status=source_expired` e impede resultado favorável. Marcadores comuns
de prompt injection fazem o chunk ser excluído do índice. Esse filtro é heurístico e não substitui
curadoria humana.

## Governança pendente

Antes de qualquer uso além da demo ainda são necessários corpus versionado e aprovado, processo de
curadoria, avaliação de recall/precision, groundedness, proteção de poisoning, política de expiração,
monitoramento de drift e validação de cada fonte no contexto brasileiro.
