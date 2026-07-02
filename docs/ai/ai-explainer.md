# IA Explicativa

Prescripta v0.3.0 adiciona uma camada de IA explicativa para apoiar a compreensao dos alertas gerados pelo motor deterministico.

Esta camada nao calcula risco, nao libera prescricao, nao recalcula dose critica e nao substitui revisao profissional. O backend continua sendo a fonte das regras clinicas demonstrativas.

## Escopo

A IA recebe o resultado ja calculado pela checagem de prescricao e gera:

- explicacao em linguagem simples;
- resumo tecnico curto;
- perguntas de revisao clinica;
- aviso educacional obrigatorio.

Alertas cobertos:

- alergia;
- dose diaria maxima;
- interacao medicamentosa;
- polifarmacia;
- idade;
- comorbidade/contraindicacao;
- via invalida.

## Endpoint

`POST /api/prescriptions/explain`

Permissao: `admin`, `medico` e `enfermagem`.

O endpoint recebe paciente, medicamento, dose, frequencia, via, perfil do usuario e o resultado da checagem de prescricao. A resposta ecoa `prescription_status`, `risk_level` e `critical_alert_codes` para deixar explicito que a IA nao alterou a decisao deterministica.

## Configuracao

Variaveis:

- `PRESCRIPTA_AI_PROVIDER`: `fallback` por padrao; `openai` habilita provider externo.
- `PRESCRIPTA_AI_API_KEY`: chave do provider, nunca versionada.
- `PRESCRIPTA_AI_MODEL`: modelo usado quando o provider externo estiver configurado.

Sem chave de API, o sistema retorna fallback deterministico baseado nos alertas. A falha do provider externo tambem cai no fallback para nao quebrar o fluxo de checagem.

## Salvaguardas

- chamada somente por clique do usuario;
- sem chamada automatica a cada prescricao;
- endpoint protegido por perfil;
- auditoria registra metadados da explicacao, nao o texto completo;
- prompt orienta o modelo a explicar, nao decidir;
- resposta preserva codigos de alertas criticos;
- testes verificam fallback, permissao, status inalterado e preservacao de bloqueios criticos.

## Uso Responsavel

O texto gerado e apoio educacional/demonstrativo. Ele deve ser revisado por profissional habilitado e confrontado com protocolos locais, historico completo do paciente e julgamento clinico.
