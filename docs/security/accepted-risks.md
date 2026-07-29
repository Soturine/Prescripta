# Riscos temporariamente aceitos

## React Router RSC CSRF — expira em 2026-08-15

- Advisory: `GHSA-qwww-vcr4-c8h2`.
- Dependências afetadas: `react-router` e `react-router-dom` 7.18.2.
- Justificativa limitada: o Prescripta é compilado como SPA Vite e não habilita RSC Mode,
  Server Actions nem action endpoints do React Router.
- Mitigação: autenticação por cookie `SameSite=Lax`, APIs mutáveis autenticadas e ausência de
  handlers RSC. Isso não declara a biblioteca genericamente segura.
- Gate: `scripts/check_npm_audit.py` aceita somente esse advisory, somente nesses pacotes e
  falha automaticamente após a data de expiração ou diante de qualquer novo high/critical.
- Ação: atualizar imediatamente para a primeira versão estável corrigida e remover a exceção.
