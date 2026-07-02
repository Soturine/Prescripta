# Threat Model Básico

## Ativos

- Dados cadastrados de pacientes.
- Dados cadastrados de medicamentos.
- Registros de auditoria.
- Regras determinísticas de risco.
- Contas de usuário e perfis.
- Tokens JWT.

## Ameaças

- Uso indevido como sistema clínico real.
- Cadastro de dados sensíveis reais em ambiente demonstrativo.
- Alteração acidental de regras clínicas.
- Exposição de banco SQLite local.
- Divergência entre frontend e backend.
- Vazamento de token armazenado em `localStorage`.
- Uso de credenciais demonstrativas fora do ambiente local.

## Mitigações Atuais

- Aviso de uso educacional.
- `.gitignore` para banco local e `.env`.
- Testes automatizados de regras principais.
- Regra clínica concentrada no backend.
- Hash Argon2 para senhas.
- Rotas protegidas por token JWT e perfil no backend.
- Auditoria com usuário responsável.

## Mitigações Futuras

- Logs estruturados.
- Cookies seguros, rotação de segredo e revogação de sessão.
- Revisão de permissões.
- Migrações e banco gerenciado.
