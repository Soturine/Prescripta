# Reconciliacao Clinica Granular

A v0.7.0 adiciona `ClinicalReconciliationService` sobre as importacoes demonstrativas da v0.6.0.

## Comparacao

O servico compara registros importados com dados existentes:

- paciente e identificadores;
- alergias;
- condicoes;
- medicamentos em uso;
- observacoes/documentos;
- perfil funcional;
- campos de fonte e confianca.

## Badges

- `novo`
- `duplicado`
- `conflito`
- `possivel_match`
- `aceito`
- `rejeitado`
- `revisao_necessaria`
- `fonte_externa`
- `fonte_pendente`

## Decisoes

Cada item pode ser aceito ou rejeitado individualmente. O endpoint `accept-safe` aceita apenas itens sem conflito e ignora itens duplicados ou que exigem revisao manual.

Importacao nao altera dados clinicos antes de decisao humana. Ao aceitar item, o servico aplica apenas o campo correspondente e registra auditoria granular.

## Limites

A reconciliacao e demonstrativa e ainda nao cobre todos os recursos FHIR, historico temporal ou qualidade de dado de sistemas reais. Evolucao prevista para v0.8.0.
