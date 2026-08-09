# Riscos temporariamente aceitos

Não há exceção high/critical ativa para dependências na v0.8.9. Os gates de Python, npm e imagens falham diante de vulnerabilidade HIGH/CRITICAL sem exceção estreita aprovada.

## Riscos residuais conhecidos da v0.8.9

| Área | Risco residual | Controle e condição de revisão |
| --- | --- | --- |
| containers | digest fixo não garante que uma base nunca tenha sido comprometida | imagens oficiais, Trivy e SBOM; reconstruir ao surgir advisory ou nova base revisada |
| Docker local | quem controla daemon/host controla containers | socket não montado, non-root e least privilege; produção requer hardening do host externo ao repo |
| install scripts | `esbuild` e `fsevents` permitidos executam código de pacote | policy exata por path/versão, integrity e revisão bloqueante em qualquer delta |
| localização | tradução pode gerar ambiguidade clínica | códigos/unidades/canônicos preservados e testes PT/EN; validação linguística profissional antes de uso real |
| assets | conteúdo externo pode rastrear usuário ou ter licença incompatível | somente assets locais com manifesto/atribuição e CSP fechada; revisar cada inclusão |
| assinatura Git | tag anotada pode não ser assinada se não houver chave configurada | registrar honestamente o tipo; provenance e SBOM attestations complementam, sem fingir assinatura |

Esses itens não autorizam uso clínico. Uma vulnerabilidade HIGH/CRITICAL nova, um delta no inventário de scripts ou um finding de segredo não entra automaticamente nesta lista.

## Risco encerrado: React Router RSC CSRF

- Advisory: `GHSA-qwww-vcr4-c8h2`.
- Encerramento: 8 de agosto de 2026.
- Versão instalada: `react-router` e `react-router-dom` 7.18.2.
- Resultado: a exceção temporária foi removida; autenticação, navegação, redirects, access denied, Vitest e E2E permanecem gates obrigatórios.
- Condição de reabertura: novo advisory que inclua 7.18.2 ou regressão na linha instalada.
