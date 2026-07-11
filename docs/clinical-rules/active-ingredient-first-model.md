# Modelo Princípio Ativo Primeiro

Prescripta v0.5.0 passa a tratar princípio ativo como entidade central.

## ActiveIngredient

- `dcb_name`
- `normalized_name`
- `synonyms`
- `therapeutic_classes`
- `common_brands`
- `jurisdiction`
- `source`
- `validation_status`

## DrugProduct

- `active_ingredient_id`
- `commercial_name`
- `manufacturer`
- `concentration`
- `pharmaceutical_form`
- `allowed_routes`
- `anvisa_registration_number`
- `bula_url`
- `source`
- `validation_status`

## Compatibilidade com MedicationModel

`MedicationModel` continua existindo como produto prescritivel demonstrativo, mas agora pode apontar para `active_ingredient_id`, aliases comerciais e fonte/jurisdição. Isso preserva prescricoes antigas e permite evolucao gradual.

## Exemplo

`Novalgina`, `Anador`, `Dorflex`, `Neosaldina` e `Lisador` não precisam virar cinco principios ativos. Na seed v0.5, eles sao aliases que resolvem para `dipirona`.
