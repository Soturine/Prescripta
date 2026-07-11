# Arquitetura da Central de Protocolos Rápidos

## Contexto

A auditoria de paridade até v0.8.1 indicava uma lacuna clara: o Prescripta já
tinha prescrição, IA explicativa, reconciliação, relatórios e auditoria, mas não
tinha uma área para fluxos rápidos de urgência.

## Objetivo

A Central de Protocolos Rápidos entrega apoio estruturado para cenários
demonstrativos de emergência sem transformar o sistema em dispositivo médico ou
motor autônomo de conduta.

## Como Funciona

- Os protocolos ficam em `EmergencyProtocolService`.
- Cada protocolo tem metadados de fonte, jurisdição, status de validação e aviso.
- Os passos são imutáveis para a execução e sempre exigem julgamento humano.
- `POST /api/protocols/{id}/run` valida contexto mínimo e registra auditoria.
- `POST /api/protocols/{id}/explain` permite narrativa de IA/fallback sem alterar
  passos, doses ou fonte.
- Relatório, PDF, JSON e CSV são derivados do protocolo e do evento auditado.

## Escopo v0.8.2

- Anafilaxia.
- PCR.
- Convulsão/crise convulsiva.
- Hipoglicemia.
- Dor torácica/suspeita de SCA.
- Broncoespasmo/crise asmática.
- Intoxicação medicamentosa.

## Decisões de Segurança

- IA recebe apenas protocolo e contexto minimizado.
- IA não pode inventar etapa, dose, fonte ou evidência.
- Calculadoras são demonstrativas e retornam aviso de confirmação humana.
- A execução usa `AuditService` com `secret_logged=false`.
- Não há integração com sistema hospitalar real nem acionamento automático.

## Limitações

- Protocolos são educacionais e não clinicamente completos.
- Não há validação clínica externa formal.
- Não há versionamento de protocolo em banco.
- Não há protocolo pediátrico/adulto separado além de avisos demonstrativos.

## Próximos Passos

- Versionar protocolos em base própria.
- Adicionar revisão clínica externa.
- Criar diffs entre versões de protocolo.
- Expandir relatórios de protocolo para `GeneratedReport`.
- Adicionar filtros dedicados de protocolo na auditoria.
