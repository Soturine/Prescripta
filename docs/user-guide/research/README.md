# Pesquisa e RWE

## Fluxo recomendado

1. Em **Desenho**, crie o estudo e preencha protocolo, fontes, limitações e desfecho.
2. Faça revisão humana independente das versões; uma versão revisada é imutável.
3. Em **Coorte**, combine critérios no builder visual, confira custo/temporalidade, salve, revise e
   execute sobre um marcador de snapshot sintético.
4. Em **Plano de análise**, execute Qualidade dos dados, trate findings críticos e crie/revise um
   plano descritivo allowlisted.
5. Em **Resultados**, leia N, missingness, resumos numéricos/categóricos, Table 1, attrition e a
   jornada sintética quando autorizada.
6. Em **Evidências**, gere o pacote agregado, confira manifesto/hashes e use o Copiloto apenas como
   proposta para revisão.

O indicador de prontidão mostra: pergunta, protocolo, coorte, desfecho, qualidade, plano, resultados e
pacote. Um item verde confirma apenas que a etapa técnica foi concluída; não confere validade clínica,
ética, regulatória ou epidemiológica.

## v0.9.2

O workspace também oferece comparação descritiva, pessoa-tempo, PSM/IPTW experimentais, literatura,
Copilot v2 e preview NL→SQL default-off. Tudo permanece sintético, aggregate-only e sem conclusão
causal ou recomendação clínica. Células com N menor que 5 são suprimidas.

Consulte [estudos](studies.md), [coortes](cohorts.md), [concept sets](concept-sets.md),
[desfechos](outcomes.md), [qualidade](data-quality.md), [análises e resultados](analysis-results.md) e
[proveniência](provenance.md). Para o fluxo novo, veja [Signal Explorer](signal-explorer.md),
[comparações](comparisons.md), [PSM](psm.md), [IPTW](iptw.md), [pressupostos](causal-methods.md),
[literatura](literature-evidence.md), [NL→SQL](nl-to-sql.md) e [Copilot](research-copilot.md).
