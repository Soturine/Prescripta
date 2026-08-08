# Fronteiras transacionais

## Objetivo

Cada caso de uso deve abrir uma sessão, coordenar `add`/`flush`, confirmar uma vez e fazer rollback
integral em erro. Repositories não devem decidir isoladamente quando uma operação composta termina.

## Estado v0.8.8

Repositories, services, integrações e reports não executam mais `commit()`; eles adicionam objetos e
usam `flush()` somente quando precisam materializar ID, constraint ou valor do banco. O dependency
`get_db` é o limite padrão da requisição e confirma uma vez depois de a rota retornar. Exceções fazem
rollback integral, inclusive de auditoria já materializada por `flush()`.

O login negado é uma exceção explícita no limite da aplicação: a própria rota confirma uma única vez
o contador e o evento de segurança antes de lançar o erro HTTP. Não há objeto clínico nessa unidade
de trabalho. O seed também confirma explicitamente porque não pertence ao lifecycle de request.

## Contrato

1. rota valida autorização e payload;
2. serviço executa o caso de uso na sessão recebida;
3. repositories adicionam e executam `flush`;
4. serviço registra auditoria na mesma sessão;
5. o limite route/application confirma a operação uma única vez;
6. qualquer exceção executa rollback e não deixa evento órfão.

Testes de falha depois de persistência intermediária provam rollback conjunto para prescrição,
auditoria, grant e break-glass. Novos workflows de protocolo, farmácia e Research devem repetir o
mesmo contrato; `commit()` dentro de service/repository é regressão arquitetural.
