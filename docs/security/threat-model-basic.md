# Threat Model Básico

## Ativos

- Dados cadastrados de pacientes.
- Perfil clínico estruturado, triagem rápida, alergias, reações adversas e medicamentos contínuos.
- Dados cadastrados de medicamentos.
- Metadados clínicos demonstrativos de medicamentos.
- Registros de auditoria.
- Regras determinísticas de risco.
- Base interna demonstrativa de RAG.
- Contas de usuário e perfis.
- Tokens JWT.
- Chave de provider de IA, quando configurada.
- URL base de provider OpenAI-compatible/local, quando configurada.
- Saídas explicativas geradas por IA.

## Ameaças

- Uso indevido como sistema clínico real.
- Cadastro de dados sensíveis reais em ambiente demonstrativo.
- Inclusão de histórico clínico real em triagem ou perfil de paciente fictício.
- Alteração acidental de regras clínicas.
- Uso de base RAG demonstrativa como se fosse bula, protocolo ou evidência validada.
- Exposição de banco SQLite local.
- Divergência entre frontend e backend.
- Vazamento de token armazenado em `localStorage`.
- Uso de credenciais demonstrativas fora do ambiente local.
- Uso da IA como decisão clínica.
- Vazamento de chave de IA em `.env`, logs ou commits.
- Configuração de `PRESCRIPTA_AI_BASE_URL` para endpoint não confiável.
- Alucinação ou interpretação incorreta em explicação gerada.
- Tentativa de usar payload de explicação para contornar regras determinísticas.
- Perda de histórico por atualização de triagem sem auditoria.
- Duplicidade de alergias, reações ou medicamentos contínuos por variação de acento, caixa ou sinônimo.

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
- RAG textual interno usado apenas como contexto explicativo.
- Alternativas terapêuticas avaliadas pelo motor de risco antes de aparecerem.
- Normalização e deduplicação para reduzir duplicidade de termos clínicos.
- Triagem rápida registra auditoria e preserva dados anteriores.
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
- Revisão clínica da base demonstrativa por profissional habilitado.
- Validação de provedores externos e allowlist para endpoints de IA.
