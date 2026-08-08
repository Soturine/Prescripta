# Riscos temporariamente aceitos

Não há exceção high/critical ativa para dependências na v0.8.8. O gate
`scripts/check_npm_audit.py` falha diante de qualquer vulnerabilidade high/critical.

## Risco encerrado: React Router RSC CSRF

- Advisory: `GHSA-qwww-vcr4-c8h2`.
- Encerramento: 8 de agosto de 2026.
- Versão instalada: `react-router` e `react-router-dom` 7.18.2.
- Evidência oficial: o GitHub Advisory Database passou a listar 7.18.2 como versão corrigida e
  restringe o impacto às APIs RSC instáveis, que o Prescripta não utiliza.
- Resultado: exceção e expiração de 15 de agosto de 2026 removidas; autenticação, navegação,
  redirects, access denied, Vitest e E2E permanecem gates obrigatórios.
- Condição de reabertura: novo advisory que inclua 7.18.2 ou regressão na linha instalada.
