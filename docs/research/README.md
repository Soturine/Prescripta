# Research & RWE

A v0.9.0 fecha o fluxo demonstrativo e sintético:

`Pergunta → Estudo → Protocolo → Coorte → Qualidade dos dados → Plano de análise → Análise determinística → Resultados → Evidência/Proveniência → Pacote de pesquisa`.

O Study Workspace apresenta cinco áreas profissionais: Desenho, Coorte, Plano de análise,
Resultados e Evidências. Concept sets, outcomes, runs, hashes e JSON permanecem disponíveis em
detalhes técnicos, sem dominar o fluxo principal.

## Contratos autoritativos

- protocolo, coorte, outcome e plano são versionados; revisão humana é independente do autor;
- a DSL de coorte aceita apenas critérios, operadores e temporalidade allowlisted, sem SQL livre;
- análises são determinísticas e descritivas: contagem, resumos numéricos/categóricos, prevalência,
  Table 1 e utilização de recursos;
- incidência v0.9.2 exige pessoa-tempo explícito e positivo e permanece sintética/não validada;
- resultados e pacotes são aggregate-only e aplicam supressão de células com `N < 5`;
- hashes de conteúdo excluem timestamps e outros campos voláteis;
- Patient Journey exige estudo e eventos comprovadamente sintéticos e falha fechado nos demais casos;
- o Copilot propõe estruturas e explicações; nunca calcula, executa, revisa ou publica;
- o piloto NL→SQL é default-off, validado por AST e limitado a uma view agregada com escopo injetado.

## Segurança e validade

Objetos são isolados por instituição e por capacidade. Nenhum endpoint de pesquisa entrega nomes,
identificadores ou linhas de pacientes no resultado agregado. PSM/IPTW existem somente como métodos
experimentais, com diagnósticos e abstention; não oferecem inferência causal, recomendação clínica
ou validade epidemiológica automática.

Detalhes: [modelo de estudo](study-model.md), [DSL de coorte](cohort-definition.md),
[análises e pacote](analysis-and-package.md), [reprodutibilidade](reproducibility.md),
[qualidade dos dados](data-quality.md) e [Copilot](research-copilot.md). Na v0.9.2, consulte também
[comparações](comparative-analytics.md), [métodos](statistical-methods.md),
[PSM](propensity-score.md), [IPTW](ipw.md) e [pressupostos causais](causal-assumptions.md).
