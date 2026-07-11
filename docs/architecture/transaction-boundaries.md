# Fronteiras transacionais

## Objetivo

Cada caso de uso deve abrir uma sessão, coordenar `add`/`flush`, confirmar uma vez e fazer rollback
integral em erro. Repositories não devem decidir isoladamente quando uma operação composta termina.

## Estado v8.6.0

Checagem, relatório, protocolo, documento, curadoria, importação e policy foram inventariados. A base
legada ainda contém commits internos em auditoria e serviços; portanto a migração está `partial`.
Removê-los em massa sem Alembic e testes de falha intermediária aumentaria o risco desta release.

## Contrato futuro

1. rota valida autorização e payload;
2. serviço inicia o caso de uso;
3. repositories adicionam e executam `flush`;
4. serviço registra auditoria na mesma sessão;
5. um commit conclui a operação;
6. qualquer exceção executa rollback e não deixa evento órfão.

Na migração PostgreSQL/Alembic, cada fluxo receberá teste de falha após persistência intermediária.
