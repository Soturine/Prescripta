# Threat Model Básico

## Ativos

- Dados cadastrados de pacientes.
- Dados cadastrados de medicamentos.
- Registros de auditoria.
- Regras determinísticas de risco.

## Ameaças

- Uso indevido como sistema clínico real.
- Cadastro de dados sensíveis reais em ambiente demonstrativo.
- Alteração acidental de regras clínicas.
- Exposição de banco SQLite local.
- Divergência entre frontend e backend.

## Mitigações Atuais

- Aviso de uso educacional.
- `.gitignore` para banco local e `.env`.
- Testes automatizados de regras principais.
- Regra clínica concentrada no backend.

## Mitigações Futuras

- Autenticação e perfis.
- Logs estruturados.
- Revisão de permissões.
- Migrações e banco gerenciado.
