# Modelo de ameaça

## Escopo e premissas

Modelo STRIDE simplificado para a aplicação web, API, banco, workers, integrações e providers de IA.
O ambiente demonstrativo contém somente dados fictícios. Produção real, integrações hospitalares,
mobile nativo, infraestrutura cloud e segurança física estão fora do escopo validado.

## Ativos e fronteiras de confiança

- contas, papéis, instituição, sessão e segredo MFA;
- contexto clínico, documentos, consentimentos e grants de paciente;
- catálogo, rulesets, fontes, decisões, overrides e snapshots;
- estudos, protocolos, concept sets, definições de coorte, attrition e runs;
- credenciais de IA, prompts, respostas externas e logs;
- banco PostgreSQL, backups, artefatos de CI, dependências e imagens de release.

```text
browser não confiável
  │ HTTPS / cookie HttpOnly
API ── policy + autorização por objeto ── PostgreSQL
  │                                      │
  ├── documentos/importações não confiáveis
  ├── cohort DSL allowlisted ── execução determinística aggregate-first
  └── AI Task Router ── egress HTTPS allowlisted ── provider externo não confiável
```

## Ameaças, controles e risco residual

| Ameaça | Controle atual | Risco residual/ação |
| --- | --- | --- |
| roubo ou replay de sessão | cookie HttpOnly, SameSite Lax, expiração JWT, logout | falta revogação central de JWT e CSRF token explícito para topologias cross-site |
| brute force/credential stuffing | lockout persistente por identificador hasheado, MFA TOTP opcional, auditoria | rate limit distribuído de borda ainda recomendado |
| BOLA/BFLA e tenant escape | capacidade global + instituição + relação/purpose por paciente; lista filtrada; grants/care team/episode/break-glass; testes same-tenant e cross-tenant | revisão endpoint a endpoint e política ABAC institucional continuam necessárias |
| mass assignment/adulteração de decisão | schemas `extra=forbid`, regras resolvidas no servidor, explicação por `audit_id` | novos endpoints precisam repetir o padrão |
| alteração histórica | snapshot imutável, JSON canônico, hash versionado, relatórios snapshot-only | assinatura externa/WORM e timestamp confiável não existem |
| SSRF/DNS rebinding/redirect | endpoints oficiais fixos; allowlist/porta exatas; resolução fixada no IP efetivamente conectado com Host/SNI original; redirects bloqueados; limites de timeout e tamanho | firewall/proxy de egress permanece defesa adicional do deployment |
| vazamento a IA | classificação por tarefa, provider local para sensitive/restricted, contexto minimizado, credencial criptografada, sem chave/prompt bruto no frontend ou registro | DLP independente e contrato com provider não foram validados |
| prompt injection/source poisoning | índice bloqueado por hash, chunks, marcadores rejeitados, IA não decide risco | detecção é heurística; curadoria e avaliação formal de groundedness pendem |
| SQL injection ou consulta ampla em Research | cohort DSL sem SQL livre, critérios/operadores allowlisted, limite de predicados/janelas/custo e SQLAlchemy | novos fenótipos precisam passar pela mesma revisão; testes de carga em base real pendem |
| tenant escape em estudo/fonte/run | instituição em todos os objetos, capabilities separadas e resposta sem objeto fora de escopo | ABAC e hierarquias multi-instituição reais ainda não foram modeladas |
| reidentificação por resultado pequeno | resposta aggregate-first e snapshot sem IDs de paciente | política formal de small-cell suppression ainda não existe; somente dados sintéticos são permitidos |
| adulteração de estudo revisado | versões revisadas e runs imutáveis, JSON canônico, hashes e nova versão para correção | falta assinatura externa, WORM e preservação do dataset original |
| log/CSV/XSS injection | redaction de eventos, JSON tipado, React escaping, export controlado | testes DAST e fórmula CSV em todos os campos devem continuar no roadmap |
| dependência/Action comprometida | lockfiles, Actions por SHA, Dependabot, CodeQL, SCA, gitleaks e SBOM | majors deferidos exigem nova revisão; não há exceção high/critical ativa |
| indisponibilidade/DoS | paginação, limites de payload, timeout/retry/circuit breaker compartilhado | quotas por tenant, fila e testes de carga distribuída pendem |
| segredo/default em produção | startup falha com segredo demo, SQLite, auto-seed, CORS local ou criptografia ausente | deployment precisa fornecer secret manager, TLS e observabilidade |

## Regras de privacidade

Pseudonimização não é anonimização. Novos eventos não armazenam nome/e-mail; identificadores
externos são hasheados/mascarados; dados identificáveis não entram no payload de IA por padrão.
Retenção, base legal, RIPD, atendimento a titulares e descarte seguro dependem da instituição e estão
fora da validação deste repositório.

## Verificação

Testes cobrem escopo entre instituições, acesso negativo a relatório/export/counseling, lockout,
cookie/logout, SSRF, startup inseguro, segredo em auditoria, snapshot e rollback. CI executa CodeQL,
SCA Python/npm, secret scan e CycloneDX. Isso é evidência técnica, não pentest independente.
