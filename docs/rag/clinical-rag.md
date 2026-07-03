# RAG Clínico Demonstrativo

Prescripta v0.4.0 adiciona uma camada interna de recuperação de conhecimento para explicação.

## Escopo

O RAG recupera trechos de uma base interna demonstrativa em Markdown. Ele não decide status, não libera prescrição e não substitui bula, monografia ou protocolo validado.

## Estrutura

```text
backend/app/knowledge/
backend/app/data/knowledge_base/
```

A busca textual normaliza acentos, caixa e sinônimos simples. Sem embeddings ou API externa, o sistema continua funcionando.

## Saída

Cada evidência contém:

- fonte interna;
- trecho encontrado;
- score simples;
- termos encontrados;
- aviso educacional.

Esses trechos são usados pela IA explicativa como contexto demonstrativo.
