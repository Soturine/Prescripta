# Segurança do NL→SQL experimental

Na v0.9.2 o piloto existe, mas `PRESCRIPTA_RESEARCH_QUERY_ASSISTANT_ENABLED=false` é o default.
Preview não executa nada; execução exige ação humana separada sobre aquele preview imutável.

```text
linguagem natural → SQL proposto → parser AST → SELECT único → view agregada aprovada
→ instituição + estudo + snapshot injetados → budget/limit/timeout → execução auditada
```

O validador usa AST, não regex. Rejeita escrita/DDL/transação, múltiplas instruções,
UNION/INTERSECT/EXCEPT, joins, catálogos, tabelas diretas, colunas/funções não permitidas e custo
estimado acima da policy. A única view é `research_aggregate_comparisons`; seu conteúdo é
aggregate-only e herda supressão de células pequenas.

O sistema injeta placeholders nomeados de `institution_id`, `study_id` e
`dataset_snapshot_marker`, limita linhas, timeout e 200 kB de resultado, e grava somente hash da
pergunta, SQL normalizado, policy, resultado agregado e auditoria. SQL gerado nunca define escopo.

O piloto não deve ser habilitado com dados reais sem revisão de threat model, permissões read-only no
banco, observabilidade, teste de carga e aprovação institucional.

Referências técnicas: [SQLGlot/AST](https://github.com/tobymao/sqlglot) e
[PostgreSQL `statement_timeout`](https://www.postgresql.org/docs/current/runtime-config-client.html).
