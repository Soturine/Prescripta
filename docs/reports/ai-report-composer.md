# AIReportComposer

`AIReportComposer` gera narrativa controlada para relatórios.

Ele pode gerar:

- resumo executivo;
- explicação profissional;
- orientação ao paciente;
- resumo de evidências;
- nota de dados faltantes;
- nota de contexto funcional;
- resumo de reconciliação;
- limitações e aviso de revisão humana.

Ele não pode alterar:

- risco;
- status;
- bloqueio;
- severidade;
- dose;
- duração;
- regra disparada;
- fonte;
- jurisdição;
- validação da fonte;
- decisão clínica.

Validações:

- JSON por `ReportNarrativeSchema`;
- sem HTML bruto;
- sem campos reservados;
- `cited_source_ids` precisa existir no bundle;
- fallback determinístico em erro, timeout, JSON inválido ou provider indisponível.

Prompts ficam em `backend/app/reports/prompts` e são versionados.
