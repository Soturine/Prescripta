# Cohort DSL v2

A DSL é JSON declarativo e nunca aceita SQL, expressão livre, nome de tabela ou campo arbitrário.
Definições v1 (`all`/`exclude`) continuam executáveis e são normalizadas para v2.

## Estrutura

- `schema_version: "2"`;
- grupos raiz `inclusion` e `exclusion`;
- cada grupo usa `operator: all|any`, `items`, identificador e rótulo;
- grupos podem ser aninhados até profundidade 2;
- até 30 critérios e custo estimado máximo 100.

Critérios permitidos: idade, sexo, condição, exposição medicamentosa, medição, procedimento, visita,
concomitância medicamentosa, janela de data e demografia allowlisted. Critérios clínicos exigem
versão explícita de concept set do mesmo tenant e revisada por pessoa.

Temporalidade aceita `before_index`, `after_index`, `on_index` e `during_window`, com janelas entre 0
e 3650 dias. Operadores incompatíveis, nesting excessivo, custo alto, concept set cross-tenant e
qualquer campo desconhecido são rejeitados.

O engine aplica cada item raiz sequencialmente para produzir attrition. Grupos aninhados contam como
uma etapa legível. O resultado contém somente contagens, estatísticas agregadas e hashes.
