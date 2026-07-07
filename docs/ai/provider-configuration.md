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

## Variáveis

```env
PRESCRIPTA_AI_PROVIDER=fallback
PRESCRIPTA_AI_MODEL=
PRESCRIPTA_AI_BASE_URL=
PRESCRIPTA_AI_ENABLE_EXTERNAL_CALLS=false
PRESCRIPTA_CONFIG_ENCRYPTION_KEY=
```

O frontend nunca chama provider externo diretamente.
