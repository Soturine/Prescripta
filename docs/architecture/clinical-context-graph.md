# Clinical Context Graph

O Clinical Context Graph é uma representação lógica em JSON. Ele não é rede neural nem grafo clínico validado.

## Objetivo

Mostrar como o Prescripta cruza:

- paciente;
- condições clínicas;
- alergias;
- reações adversas;
- medicamentos em uso;
- medicamento pretendido;
- dose diária;
- dose acumulada;
- duração;
- efeitos colaterais;
- órgãos envolvidos;
- regras determinísticas;
- evidências internas/RAG;
- explicação de IA.

## Uso

O grafo aparece na resposta da checagem de prescrição e no endpoint:

```text
GET /api/patients/{patient_id}/clinical-context
```

O frontend exibe os nós e relações em um card simples para facilitar auditoria e explicabilidade.
