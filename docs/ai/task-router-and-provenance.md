# AI Task Router e provenance

Aplicações chamam um único router por `task_type`. A policy combina classificação de
dados e configuração institucional antes de selecionar fallback, OpenAI, Gemini,
Ollama ou endpoint OpenAI-compatible. `sensitive` e `restricted` aceitam somente opção
local autorizada. Preferência do usuário não supera essa policy.

As tasks da v0.8.8 retornam JSON estruturado. Drafts de coorte passam também pelo
validator determinístico da DSL; resumos de evidência só podem citar `source_id`
fornecido e autorizado. Saída inválida é rejeitada, nunca corrigida silenciosamente.

`AIInteraction` persiste provider/modelo, versões de prompt e schema, fontes, contexto
institucional, hashes de entrada/saída, latência, fallback, classificação e revisão
humana. O prompt bruto não é persistido. Saídas começam em `needs_review` e jamais
publicam protocolo, concept set, coorte ou conclusão automaticamente.
