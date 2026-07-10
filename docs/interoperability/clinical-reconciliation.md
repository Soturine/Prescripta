# Reconciliação Clínica Granular

`ClinicalReconciliationService` compara registros importados por FHIR, JSON ou
CSV com o cadastro local antes de aplicar qualquer dado clínico.

## Comparação

O serviço compara:

- dados demográficos do paciente;
- identificadores externos;
- alergias;
- condições clínicas;
- medicamentos em uso;
- observações e documentos;
- perfil funcional;
- origem, confiança e status de validação.

## v0.8.1

- Medicamentos em uso são comparados por chave de equivalência de princípio ativo.
- Aliases como Novalgina, Anador, Dorflex, Neosaldina, Lisador e metamizol resolvem
  para dipirona quando presentes no vocabulário curado.
- Condições mapeadas podem atualizar `renal_condition`, `hepatic_condition`,
  `cardiac_condition`, `gastrointestinal_history`, `mental_health_factors` ou
  `reproductive_gynecologic_factors`.
- Identificador aceito é salvo por `PatientIdentifierService`, com hash e máscara,
  sem persistir o valor bruto.
- Aceite em lote seguro não aceita conflitos; conflitos exigem revisão item a item.

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

## Decisões

Cada item pode ser aceito ou rejeitado individualmente. Importação não altera dados
clínicos antes de decisão humana. Ao aceitar item, o serviço aplica apenas o campo
correspondente e registra auditoria granular.

## Limites

A reconciliação é demonstrativa e ainda não cobre todos os recursos FHIR,
histórico temporal ou qualidade de dado de sistemas reais.
