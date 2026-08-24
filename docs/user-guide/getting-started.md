# Primeiro acesso

## Objetivo e acesso

Entrar no ambiente, reconhecer o escopo da conta e chegar à primeira tarefa autorizada. É necessário um usuário ativo; a página inicial depende das capacidades atribuídas ao papel profissional.

## Passos

1. Abra `/login`, informe uma conta da [tabela pública de perfis demo](../../README.md#primeiro-uso-e-perfis-demo) e selecione **Entrar**.
2. Confirme seu nome, papel e organização no cabeçalho.
3. Escolha PT-BR ou EN-US no seletor de idioma.
4. Abra o dashboard e verifique os atalhos liberados para seu perfil.
5. Em demonstrações, use somente pacientes e medicamentos sintéticos.

## Exemplo e erros comuns

Um médico pode iniciar por **Pacientes** ou **Checagem clínica**; um auditor pode receber apenas indicadores e auditoria. Credencial inválida não revela se a conta existe. **Acesso negado** indica falta de capacidade ou escopo, não falha do navegador.

## Dados, auditoria e autoridade

A preferência de idioma é local ao navegador; a sessão e as permissões são validadas pelo backend. Tentativas de login sujeitas a controle de abuso e eventos de segurança podem ser auditadas. A IA não participa da autenticação. A autorização retornada pelo backend é autoritativa.

## Limitações

As credenciais documentadas pertencem somente ao seed local e nunca devem ser reutilizadas em outro
ambiente. Não compartilhe contas de produção. Se o papel estiver incorreto, procure um administrador
em vez de contornar a restrição.
