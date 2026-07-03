# Compatibilidade Paciente–Medicação

Prescripta v0.4.0 calcula uma compatibilidade demonstrativa entre o perfil clínico estruturado do paciente e os metadados do medicamento.

Este cálculo não é validação clínica real. Ele organiza fatores para revisão profissional.

## Entradas

- alergias;
- comorbidades;
- reações adversas anteriores;
- medicamentos contínuos;
- condição renal, hepática, cardíaca e gastrointestinal;
- idade;
- cautelas e órgãos envolvidos no medicamento;
- alertas determinísticos já gerados.

## Níveis

- `baixa`: existe bloqueio crítico ou alerta crítico.
- `moderada`: existem alertas altos, múltiplos moderados ou perfil incompleto.
- `alta`: não há riscos relevantes e o perfil clínico está suficientemente completo.

## Saída

A resposta da checagem inclui:

- nível;
- score demonstrativo;
- fatores do paciente considerados;
- fatores do medicamento considerados;
- razões;
- necessidade de revisão;
- aviso educacional.
