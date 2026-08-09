# Análises determinísticas e pacote de pesquisa

## Analysis Plan

Cada versão liga uma execução de coorte concluída a objetivos, variáveis, etapas, abordagem de dados
ausentes, outputs e limitações. Apenas `population_count`, `numeric_summary`,
`categorical_distribution`, `prevalence`, `baseline_table_1` e `resource_utilization` são aceitos.
O plano precisa de revisão humana independente.

## Execução

A execução exige protocolo, coorte, outcome e plano revisados, snapshot compatível e ausência de
finding crítico aberto. Média, desvio-padrão populacional, mediana, Q1, Q3, IQR, mínimo, máximo,
missingness e distribuições são calculados deterministicamente. Prevalência sempre informa numerador,
denominador e janela. Incidência não é estimada nesta release.

O hash estável usa hashes das definições, marcador do dataset, resultados e versões de origem; horário
e executor não entram no conteúdo reprodutível.

## Research Package

O pacote contém arquivos lógicos `study.json`, `cohort.json`, `analysis-plan.json`, `results.json`,
`data-quality.json`, `provenance.json` e `README.txt`. O manifesto registra schema, hash da análise,
políticas `aggregate_only`/`synthetic_only` e hash de cada arquivo. Não existem linhas de pacientes.
