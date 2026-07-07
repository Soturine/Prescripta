# Cenários FHIR Fictícios

Os cenários FHIR do Prescripta são educacionais e não representam integração real.

## Cenário 1: Paciente + Medicamento

- `Patient`
- `MedicationStatement`

Objetivo: demonstrar mapeamento básico e possível match de medicação em uso.

## Cenário 2: Paciente + Condição Renal

- `Patient`
- `Condition`

Objetivo: gerar item de reconciliação para condição clínica e conflito quando o paciente existente já possui outro valor.

## Cenário 3: Alergia + Observação

- `AllergyIntolerance`
- `Observation`

Objetivo: preservar dado de fonte externa e exigir revisão humana antes de alterar histórico.

## Cenário 4: Perfil Funcional Futuro

FHIR não define de forma única todos os campos ocupacionais usados pelo Prescripta. A importação funcional permanece preparada para integração ocupacional futura quando houver fonte oficial.

## Regras

- Não usar dados reais.
- Não fazer merge automático.
- Não aceitar conflito em lote.
- Preservar payload fonte.
