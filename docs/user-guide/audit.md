# Auditoria

## Objetivo e acesso

Investigar ações, decisões e evidências com filtros progressivos. Requer `audit.read`; exportação depende de capacidade própria.

## Seções e passos

1. Use a visão inicial para período, ator, ação ou recurso.
2. Abra **Filtros avançados** somente quando necessário.
3. Selecione um evento e revise resumo, linha do tempo e evidências.
4. Expanda o payload técnico apenas para investigação autorizada.
5. Exporte JSON ou CSV quando houver finalidade e permissão.

## Exemplo e erros comuns

Para investigar um override, confira ator, justificativa, checagem original e estado posterior. Um filtro sem resultados não prova que o evento não ocorreu; valide período, organização e escopo.

## Dados, IA e autoridade

Eventos são persistidos com contexto mínimo necessário, e exportações registram hash e auditoria. Segredos não devem aparecer em logs ou payloads. A IA não modifica eventos; o registro append-only e seus artefatos verificados são autoritativos.

## Limitações

Retenção e acesso seguem a política do ambiente. A tela facilita investigação, mas não substitui cadeia de custódia ou procedimento formal.
