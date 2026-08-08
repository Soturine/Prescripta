# Cohort Definition DSL

A definição de coorte é JSON declarativo validado. SQL livre, nomes de tabela, funções,
joins e comandos não fazem parte do contrato.

```json
{
  "all": [
    {"criterion": "age", "operator": "gte", "value": 18},
    {
      "criterion": "condition",
      "operator": "exists",
      "concept_set_version_id": "uuid-revisado"
    }
  ],
  "exclude": []
}
```

Critérios iniciais: idade, sexo, exposição a medicamento, condição, existência de
medição, procedimento, data e campos demográficos permitidos. Critérios clínicos exigem
uma versão de concept set da mesma instituição e com revisão humana.

Guardrails: no máximo 30 predicados, estrutura sem recursão arbitrária, janelas de até
3.650 dias e orçamento de query 100. Campos, operadores e tipos desconhecidos são
rejeitados. A execução usa SQLAlchemy e avaliação determinística; a IA nunca conta
pacientes.

Attrition é persistido por etapa com contagem anterior, removidos, contagem final e hash
do critério. O retorno padrão contém somente agregados.
