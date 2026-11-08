# Riscos temporariamente aceitos

Os gates de Python, npm e imagens falham diante de vulnerabilidade HIGH/CRITICAL, exceto pela
entrada estreita, versionada e temporária abaixo.

| ID | Componente e escopo | Justificativa e compensação | Owner | Expira |
|---|---|---|---|---|
| CVE-2026-85091, CVE-2026-76844 | somente `zlib1g@1:1.3.dfsg+really1.3.1-1+b1` da base `gcr.io/distroless/cc-debian13:nonroot@sha256:08476c24…` (PURL exato em `.trivyignore.yaml`) | Debian corrigiu em `+deb13u1` (DSA-6613-1), mas o digest distroless mais recente consultado em 2026-11-08 ainda traz `+b1`. Ambos os defeitos estão na API `gz*` (`gzwrite`/`gzprintf`); CPython usa a API de stream (`deflate`/`inflate`) e `gzip` é Python puro, então o caminho não é alcançado pelo backend. Compensação: varredura semanal do Container (nova) faz a exceção expirar e falhar o gate. Remover ao trocar o digest. | mantenedor do repositório | 2026-11-22 |

### Encerrado: CVE-2026-14456 (OpenSSL QUIC listener)

Encerrado em 2026-11-08. A exceção havia **expirado em 2026-09-07** sem revisão, e o gate do Container
falhava desde então. Debian publicou a correção (`openssl 3.5.7-1~deb13u2`, DSA-6465-1); a base
runtime foi movida para o digest `sha256:08476c244888…`, que contém `libssl3t64 3.5.7-1~deb13u3`, e
a exceção foi removida. Verificação local: Trivy HIGH/CRITICAL sem a exceção → 0 achados de OpenSSL.
A base frontend foi movida de `nginx:1.30.4-alpine` (34 HIGH/CRITICAL corrigíveis, incluindo
OpenSSL, curl, expat e brotli) para `nginx:1.30.6-alpine` (0).

Histórico — reconsulta independente em 2026-08-24: o advisory oficial do OpenSSL classifica o problema como
`Low`, restrito ao listener QUIC server em OpenSSL 3.5+, e informa correção futura em 3.5.8. O
tracker oficial do Debian ainda marca `3.5.6-1~deb13u2` como vulnerável e adiado por severidade menor.
Portanto, ignorado não significa corrigido; o PURL exato e a expiração continuam obrigatórios.
Fontes: <https://openssl-library.org/news/secadv/20260813.txt> e
<https://security-tracker.debian.org/tracker/CVE-2026-14456>.

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
