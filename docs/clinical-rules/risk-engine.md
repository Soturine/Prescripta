# Motor de Risco

O motor de risco fica em `backend/app/services/risk_engine.py`.

## Entradas

- Paciente.
- Medicamento.
- Dose em mg.
- Frequência por dia.
- Via de administração.

## Regras

- Alergia ao medicamento, princípio ativo ou classe: alerta crítico e bloqueio.
- Dose diária acima da dose máxima: alerta crítico e bloqueio.
- Interação medicamentosa demonstrativa: alerta alto ou crítico.
- Cinco ou mais medicamentos contínuos: alerta moderado.
- Idade maior ou igual a 65 anos: aumenta risco em um nível.
- Comorbidade contraindicada: alerta alto.
- Via não permitida: alerta alto.

## Status

- `liberado`: risco baixo.
- `atencao`: risco moderado ou alto.
- `bloqueado`: risco crítico.

## Revisão Humana

Exigida quando o status não é `liberado`.

## Observação

As regras são demonstrativas e não clinicamente completas.
