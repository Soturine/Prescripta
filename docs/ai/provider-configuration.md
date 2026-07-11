# Configuração de Provider de IA

A tela **IA** permite configurar o provider usado pelos recursos explicativos do Prescripta.

## Providers

- `fallback`: local, sem chave, sem chamada externa.
- `openai`: usa `OPENAI_API_KEY` ou chave salva pela UI.
- `gemini`: usa `GEMINI_API_KEY`, `GOOGLE_API_KEY` ou chave salva pela UI.
- `ollama`: usa `OLLAMA_BASE_URL`, padrão `http://localhost:11434`.
- `openai_compatible`: usa Base URL, API Key e modelo customizado.

## Fluxo

1. Admin escolhe provider.
2. Admin informa chave e Base URL quando aplicável.
3. Backend salva a credencial protegida ou em memória no ambiente local sem chave de criptografia.
4. Admin atualiza modelos.
5. Admin testa conexão.
6. Admin ativa modelo.

Médico, enfermagem e auditor podem ver status, mas não visualizam nem alteram a chave.

## Saúde Operacional

A v0.8.1 adiciona `GET /api/settings/ai/health` e um painel na tela **IA** com:

- provider e modelo ativos;
- chamadas externas habilitadas ou desabilitadas;
- status de credencial sem expor chave;
- cache de modelos;
- modo JSON;
- falhas recentes e circuit breaker;
- eventos recentes de configuração.

Chamadas externas usam retry/backoff apenas para timeouts, falhas de rede,
HTTP 429 e HTTP 5xx. Depois de falhas repetidas, o provider entra em degradação
temporária e o fluxo usa fallback local.

## Protocolos Rápidos

Na v0.8.2, a IA também pode explicar protocolos rápidos. O payload enviado é
minimizado: estrutura do protocolo, referências permitidas e contexto informado.
O backend rejeita resposta que cite referência inexistente e usa fallback local.
A IA não pode alterar etapa, dose, fonte ou decisão.

## Variáveis

```env
PRESCRIPTA_AI_PROVIDER=fallback
PRESCRIPTA_AI_MODEL=
PRESCRIPTA_AI_BASE_URL=
PRESCRIPTA_AI_ENABLE_EXTERNAL_CALLS=false
PRESCRIPTA_CONFIG_ENCRYPTION_KEY=
```

O frontend nunca chama provider externo diretamente.
