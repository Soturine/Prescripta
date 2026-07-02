# Threat Model Básico

## Ativos

- Dados cadastrados de pacientes.
- Dados cadastrados de medicamentos.
- Registros de auditoria.
- Regras determinísticas de risco.
- Contas de usuário e perfis.
- Tokens JWT.
- Chave de provider de IA, quando configurada.
- Saídas explicativas geradas por IA.

## Ameaças

- Uso indevido como sistema clínico real.
- Cadastro de dados sensíveis reais em ambiente demonstrativo.
- Alteração acidental de regras clínicas.
- Exposição de banco SQLite local.
- Divergência entre frontend e backend.
- Vazamento de token armazenado em `localStorage`.
- Uso de credenciais demonstrativas fora do ambiente local.
- Uso da IA como decisão clínica.
- Vazamento de chave de IA em `.env`, logs ou commits.
- Alucinação ou interpretação incorreta em explicação gerada.
- Tentativa de usar payload de explicação para contornar regras determinísticas.

## Mitigações Atuais

- Aviso de uso educacional.
- `.gitignore` para banco local e `.env`.
- Testes automatizados de regras principais.
- Regra clínica concentrada no backend.
- Hash Argon2 para senhas.
- Rotas protegidas por token JWT e perfil no backend.
- Auditoria com usuário responsável.
- IA acionada apenas por clique, sem chamada automática em toda prescrição.
- Endpoint de explicação protegido pelos mesmos perfis da checagem.
- Fallback determinístico sem chave de API.
- Resposta de IA ecoa status, risco e alertas críticos sem alterar o motor de risco.
- `.env.example` documenta variáveis sem incluir chaves reais.
- Auditoria registra metadados da explicação, não o texto completo gerado.

## Mitigações Futuras

- Logs estruturados.
- Cookies seguros, rotação de segredo e revogação de sessão.
- Revisão de permissões.
- Migrações e banco gerenciado.
- Rate limit para endpoints autenticados.
- Observabilidade e alertas para falhas de provider externo.
- Política formal de retenção de logs e auditoria.
