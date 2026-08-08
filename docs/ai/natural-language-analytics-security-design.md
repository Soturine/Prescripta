# Design de segurança para Natural Language Analytics

NL→SQL não é executável na v0.8.8. Uma evolução futura deverá aplicar o pipeline:

```text
linguagem natural → draft de IA → parser AST → SELECT único → views permitidas
→ escopo institucional/research → custo/plano → timeout/limite → execução auditada
```

O parser deverá rejeitar escrita e DDL (`INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`,
`TRUNCATE`, `COPY`, `CREATE`, `GRANT`, `REVOKE`), múltiplas instruções, catálogos de
sistema, funções perigosas, comentários de evasão e referências fora das views
permitidas. Tenant e propósito serão injetados pelo sistema, nunca confiados ao texto
gerado.

Mesmo depois desses controles, o resultado padrão continuará aggregate-first, com
orçamento, timeout, limite de linhas, auditoria e sem PII em métricas ou logs.
