# Tratamento Seguro de API Key

## Regras

- API Key não é salva em `localStorage`.
- API Key não é usada pelo frontend para chamar provider externo.
- API Key não aparece em resposta da API.
- API Key não entra em auditoria.
- API Key não é impressa em log.

## Armazenamento

Com `PRESCRIPTA_CONFIG_ENCRYPTION_KEY`, o backend persiste a chave criptografada.

Sem essa variável em ambiente local, a chave digitada na UI fica apenas em memória e é marcada como não persistente.

Em produção, persistir chave sem `PRESCRIPTA_CONFIG_ENCRYPTION_KEY` retorna erro.

## Máscara

Respostas mostram apenas máscara, por exemplo:

```txt
sk-t...1234
AIza...wxyz
```

## Auditoria

Eventos registrados:

- `credential_saved`
- `credential_deleted`
- `model_list_refreshed`
- `model_selected`
- `connection_tested`
- `fallback_used`

O campo `secret_logged` permanece `false`.
