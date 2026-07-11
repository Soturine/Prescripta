# Vocabulario Clínico Controlado

O objetivo da v0.5.0 e remover campos livres genericos como `renal`, `cardiaco` e `gastrointestinal`.

## Modelo

`ClinicalVocabulary`

- `category`
- `code`
- `label`
- `normalized_label`
- `severity_weight`
- `description`
- `is_active`

## Categorias

- renal
- hepatic
- cardiac
- gastrointestinal
- metabolic
- pregnancy_lactation

## Exemplos

- `funcao_renal_a_revisar` -> Funcao renal a revisar
- `risco_cardiovascular_a_revisar` -> Risco cardiovascular a revisar
- `historico_gastrointestinal_a_revisar` -> Histórico gastrointestinal a revisar
- `sangramento_gastrointestinal` -> Sangramento gastrointestinal

## Normalizacao

Entradas legadas ainda sao aceitas para compatibilidade, mas sao convertidas:

- `renal` -> `funcao_renal_a_revisar`
- `cardiaco` -> `risco_cardiovascular_a_revisar`
- `gastrointestinal` -> `historico_gastrointestinal_a_revisar`

O banco armazena codigos controlados. A interface mostra labels humanos.
