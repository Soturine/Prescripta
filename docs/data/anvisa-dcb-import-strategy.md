# Estrategia de Consulta Anvisa/DCB

Prescripta v0.5.0 cria a arquitetura de consulta, mas não implementa importação automatica completa.

## Fluxo alvo

1. Usuário digita princípio ativo ou nome comercial.
2. Sistema procura no catálogo local.
3. Se não encontrar, gera link assistido para Anvisa/Bulario e referencia DCB.
4. Se dados forem criados a partir da consulta, entram como `pending_review`.
5. Revisor humano valida antes de mudar para `curated` ou `validated`.

## Endpoint atual

`GET /api/medication-sources/anvisa/search?q=dipirona`

Retorna `local_match` quando encontra no catálogo local ou `assisted_lookup` quando deve abrir consulta oficial.

## Limites

- Sem scraping agressivo.
- Sem promessa de API publica universal.
- Sem uso de openFDA/DailyMed como fonte primaria para BR.
- Cache demonstrativo e registros pendentes de revisão.
