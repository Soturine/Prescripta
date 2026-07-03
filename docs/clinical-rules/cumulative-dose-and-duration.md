# Dose Acumulada E Duração

A v0.4.0 amplia a análise além da dose máxima diária.

## Cálculos

```text
dose_diária_total = dose_mg * frequência_por_dia
dose_acumulada_estimativa = dose_diária_total * duração_em_dias
```

## Regras Demonstrativas

- Se a dose diária total ultrapassa o limite diário, a prescrição é bloqueada.
- Se a duração planejada ultrapassa o limite demonstrativo, o sistema gera alerta alto.
- Se a dose acumulada estimada ultrapassa o limite acumulado, o sistema gera alerta alto.
- Se o medicamento possui limite por condição clínica e o paciente possui essa condição, o limite específico é usado como alerta de revisão.
- Se a duração não é informada para medicamento com limite de duração, o sistema pede revisão.

Esses valores são demonstrativos e precisam de validação profissional antes de qualquer uso real.
