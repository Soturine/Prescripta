# Perfil Funcional do Paciente

`PatientFunctionalProfile` registra contexto de vida que muda orientacoes praticas sem bloquear o fluxo.

Campos:

- dirige regularmente;
- motorista profissional;
- opera maquinas;
- trabalha em altura;
- atividade com risco de queda;
- turno noturno;
- cuidador responsavel;
- atividade de alta atencao;
- alcool frequente;
- historico de quedas;
- baixa tolerancia a sedacao ou tontura.

## Regras

- O perfil nao e obrigatorio para prescrever.
- Dados ausentes geram alerta geral, nao bloqueio automatico.
- Medicamento com tontura, sedacao, hipotensao ou reflexos aciona pergunta contextual quando atividades sao desconhecidas.
- Direcao, maquinas, altura e quedas geram orientacoes personalizadas quando o perfil existir.
- Alteracoes sao auditadas.

## UI

O detalhe do paciente tem card de perfil funcional com estados `Sim`, `Nao` e `Nao informado`.
