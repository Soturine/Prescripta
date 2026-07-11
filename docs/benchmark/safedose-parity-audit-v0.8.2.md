# Auditoria SafeDose/RicoToro v0.8.2

Esta auditoria usa SafeDose/RicoToro apenas como benchmark conceitual. Não houve
cópia de código, textos, CSS, banco, regras ou fluxo proprietário.

## Achados Da Auditoria Inicial

- README raiz estava curto para avaliação de produto.
- Assets v0.8.1 eram úteis, mas cobriam poucas abas.
- Protocolos rápidos/emergência seguiam como lacuna principal.
- Havia textos legados sem acento em changelog/docs antigas.
- Frontend estava funcional, porém ainda denso em medicamentos e pouco expressivo
  em fluxos rápidos.
- IA já tinha health/retry/breaker, mas precisava ficar explicitamente amarrada
  aos protocolos como explicadora, não decisora.

## Fechamento v0.8.2

| Capacidade | Estado |
| --- | --- |
| Protocolos rápidos | Implementados com sete fluxos demonstrativos. |
| Execução auditada | `protocol.run` registra contexto, flags, cálculos e fonte. |
| IA em protocolos | Apenas explicação narrativa, com estrutura bloqueada. |
| Exportações | Evento de protocolo exportável em JSON/CSV e relatório/PDF. |
| README | Reestruturado como guia de produto e onboarding. |
| Frontend | Nova área de Protocolos e polish global de UI. |
| Assets | Nova pasta v0.8.2 para screenshots e GIFs reais. |

## Diferenciais Do Prescripta

- Backend FastAPI separado do frontend React.
- Regras determinísticas testadas.
- Auditoria transversal.
- IA configurável e substituível por fallback.
- Reconciliação clínica granular com hash/máscara.
- Relatórios com hash, evidência e metadados.
- Protocolos rápidos com fonte e sem decisão autônoma.

## Lacunas Restantes

- Validação clínica externa formal.
- Protocolos versionados em banco com revisão por perfil.
- Docker/PostgreSQL/migrações.
- Deploy demonstrativo.
- Observabilidade estruturada.

## Próxima Direção

O próximo passo mais coerente é `v0.9.0`: Docker, PostgreSQL, migrações e deploy
demo. Se houver revisão clínica antes disso, uma `v0.8.3` pode focar ajustes
finos de protocolos e UX.
