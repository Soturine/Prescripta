# Autenticação e Perfis

Prescripta `v0.2.0` adiciona autenticação JWT e autorização por perfil.

## Endpoints

- `POST /api/auth/login`: recebe e-mail e senha, retorna token Bearer e usuário básico.
- `GET /api/auth/me`: retorna o usuário autenticado.

## Perfis

- `admin`: gerencia pacientes, medicamentos, usuários, checagens, auditoria e dashboard.
- `medico`: gerencia pacientes, consulta medicamentos, verifica prescrições e vê dashboard.
- `enfermagem`: consulta pacientes e medicamentos, verifica prescrições e vê dashboard.
- `auditor`: vê dashboard e auditoria, sem criar ou editar registros.

## Senhas

Senhas são armazenadas com hash Argon2. A senha original nunca deve ser salva, retornada em API, registrada em log ou enviada para auditoria.

## JWT

O segredo do JWT é configurado por `PRESCRIPTA_SECRET_KEY`. O tempo de expiração é configurado por `PRESCRIPTA_ACCESS_TOKEN_EXPIRE_MINUTES`.

Existe um valor padrão apenas para desenvolvimento local. Em ambiente real, sempre configure um segredo forte por variável de ambiente.

## Frontend

O frontend usa `localStorage` para manter o token nesta versão demonstrativa. Essa escolha simplifica o MVP, mas aumenta exposição a XSS e não deve ser tratada como desenho final de produção.

## Credenciais Demonstrativas

- `admin@prescripta.local` / `Admin@12345`
- `medico@prescripta.local` / `Medico@12345`
- `enfermagem@prescripta.local` / `Enfermagem@12345`
- `auditor@prescripta.local` / `Auditor@12345`

Essas contas existem apenas para demonstração local.

## Próximos Passos

- Estratégia de sessão mais robusta para produção.
- Política de troca e recuperação de senha.
- Revogação de tokens.
- Rate limit para login.
- Migrações formais de banco.
# Atualizacao v0.6.0

Endpoints de integracao clinica:

- `admin` e `medico`: podem importar, aceitar e rejeitar lotes.
- `enfermagem`: pode visualizar importacoes e executar CDS demonstrativo.
- `auditor`: pode visualizar importacoes, mas nao aceitar/rejeitar.

Aceite e rejeicao registram auditoria. Importacao exige consentimento ou base legal aplicavel no payload.
