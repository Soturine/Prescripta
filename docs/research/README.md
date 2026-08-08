# Research & RWE no Prescripta

A v0.8.8 introduz um vertical slice demonstrativo e aggregate-first para estudos sobre dados
sintéticos. O fluxo liga pergunta de pesquisa, protocolo versionado, concept sets revisados, coorte
declarativa, outcome, execução determinística, attrition, snapshot e Data Quality.

## Fluxo suportado

1. o pesquisador cria um `ResearchStudy` institucional;
2. uma versão de protocolo explicita população, exposição, outcome, janelas, limitações e fontes;
3. uma pessoa diferente do autor revisa o protocolo para uso demonstrativo;
4. concept sets versionados passam por revisão terminológica humana;
5. a coorte é descrita pela DSL permitida, revisada e então executada;
6. o run persiste contagens agregadas, attrition, versões, marcador do dataset e hashes;
7. o snapshot preserva definição e resultado para reprodução técnica.

As rotas e a interface aplicam capacidades de leitura, escrita, revisão, execução, IA e Data Quality
separadamente. Todos os objetos são restritos à instituição; recursos de outra instituição aparecem
como inexistentes.

## Limites desta fundação

- somente dados sintéticos/demonstrativos;
- análises descritivas, sem inferência causal, matching ou propensity score;
- sem SQL livre e sem acesso do LLM ao banco;
- sem redistribuição de vocabulários licenciados;
- nenhum resultado constitui evidência clínica, regulatória ou epidemiológica validada.

Detalhes: [modelo de estudo](study-model.md), [cohort DSL](cohort-definition.md),
[reprodutibilidade](reproducibility.md) e [Data Quality](data-quality.md).
