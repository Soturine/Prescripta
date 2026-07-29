# Backup e restauração

## Escopo

PostgreSQL é o alvo fora do modo local. SQLite serve somente à demo. Defina RPO/RTO, retenção,
região, criptografia, responsável e base legal antes de armazenar dados reais.

## Backup PostgreSQL

Use uma identidade de backup de privilégio mínimo e secret manager; nunca grave a URI no log.

```bash
pg_dump --format=custom --no-owner --no-acl --file=prescripta.dump "$DATABASE_URL"
sha256sum prescripta.dump > prescripta.dump.sha256
```

Criptografe o artefato em repouso, restrinja acesso, copie para domínio de falha separado e registre
timestamp, versão do schema/Alembic, tamanho, hash e política de expiração. O dump não deve entrar no
Git nem em artifacts públicos de CI.

## Teste de restauração

Restaure sempre em banco vazio e isolado, com credenciais distintas:

```bash
createdb prescripta_restore_test
pg_restore --exit-on-error --no-owner --no-acl --dbname=prescripta_restore_test prescripta.dump
alembic current
alembic check
```

Execute smoke tests de autenticação, contagens, integridade de snapshot/hash e relatórios. Na v0.8.7,
valide também o head `b87a224c617e`, grants, care teams, care episodes, break-glass ativos/revogados e
campos numéricos dimensionais. Usuário do mesmo tenant sem relação deve continuar sem paciente. Destrua o
ambiente de teste conforme a política de retenção. Um backup só é considerado válido após restauração
testada; mantenha evidência do exercício e tempo real de recuperação.

## SQLite local

Pare o processo antes de copiar o arquivo e use somente dados fictícios. Bancos `.db` são ignorados
pelo Git. Não promova uma cópia SQLite a ambiente não local.

## Falhas e escalonamento

Hash divergente, restauração parcial ou migration ausente é incidente: preserve logs minimizados,
isole o artefato, não sobrescreva o último backup conhecido e siga o
[plano de resposta](incident-response.md).
