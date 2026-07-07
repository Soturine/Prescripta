# Seleção e Atualização de Modelos

A lista de modelos não é fixa no frontend.

## Fluxo

```txt
Frontend → GET /api/settings/ai/models?provider=openai&refresh=true
Backend → provider configurado
Backend → normaliza modelos
Backend → cache local
Frontend → listbox de modelos
```

## Cache

- TTL padrão: 24 horas.
- Refresh manual força consulta ao provider.
- Se o provider falhar, o cache anterior é usado quando existir.
- Sem cache, a UI permite modelo customizado.

## Modelo Customizado

Modelo customizado precisa ser testado antes de ser ativado. O teste marca o modelo como verificado no cache.

## Fallback

Se provider/modelo ficar indisponível, os serviços usam fallback determinístico e não quebram o fluxo clínico.
