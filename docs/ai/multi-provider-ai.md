# IA Multi-Provider

A IA explicativa continua responsável e limitada.

## Providers

Configuração:

```env
PRESCRIPTA_AI_PROVIDER=fallback
PRESCRIPTA_AI_API_KEY=
PRESCRIPTA_AI_MODEL=gpt-5.5
PRESCRIPTA_AI_BASE_URL=
```

Providers suportados na arquitetura:

- `openai`: usa SDK OpenAI e Responses API;
- `local` ou `llama`: usa endpoint OpenAI-compatible quando `PRESCRIPTA_AI_BASE_URL` estiver configurada;
- `gemini`: fica roteado para fallback determinístico nesta versão, sem dependência extra;
- `fallback`: explicação determinística baseada em alertas, RAG interno e compatibilidade.

## Salvaguardas

- IA não altera resultado determinístico.
- IA não inventa fonte.
- IA informa que a base RAG é demonstrativa.
- IA sugere perguntas de revisão, não prescrição.
- IA aponta dados considerados e dados faltantes.
