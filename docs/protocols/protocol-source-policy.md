# Política de Fontes Para Protocolos

## Regra Geral

Protocolos rápidos devem priorizar fontes brasileiras oficiais ou institucionais
quando disponíveis. Fontes internacionais podem apoiar contexto, mas precisam ser
identificadas como secundárias.

## Critérios

- Preferir Ministério da Saúde, SAMU, Anvisa, linhas de cuidado do SUS e
  secretarias de saúde.
- Registrar `source_name`, `source_url`, `source_version`, `jurisdiction` e
  `validation_status`.
- Não usar scraping agressivo.
- Não copiar texto integral de protocolos externos.
- Parafrasear e estruturar apenas o necessário para navegação educacional.
- Marcar lacunas e limites quando a fonte for local, antiga ou parcial.

## Doses e Calculadoras

Calculadoras só entram quando:

- a fonte traz regra clara;
- o resultado é transparente;
- há aviso de confirmação humana;
- não há autorização automática de conduta.

Na v0.8.2, a dose demonstrativa de adrenalina na anafilaxia e a classificação de
hipoglicemia servem apenas para conferência educacional. O usuário precisa
confirmar concentração, via, idade, peso, apresentação, contraindicações e
protocolo institucional.

## IA

A IA pode explicar o racional e resumir o protocolo. Ela não pode:

- criar etapa;
- alterar ordem;
- inventar evidência;
- sugerir dose não presente;
- corrigir regra determinística;
- substituir regulação médica.

## Revisão

Toda expansão de protocolo deve atualizar:

- testes de API;
- `docs/protocols/`;
- `CHANGELOG.md`;
- release notes;
- assets quando houver mudança visual.
