# Comparative Analytics v0.9.2

O fluxo compara dois `CohortRun` imutáveis do mesmo estudo, instituição e snapshot. Outcomes
revisados, Data Quality sem finding crítico aberto e referências exatas são pré-condições. O motor
Python calcula; IA apenas explica o resultado calculado. Registros sintéticos existem somente na
requisição limitada a 5.000 linhas e não são persistidos.

## Saídas

- Table 1 contínua/categórica, missingness e standardized mean difference (SMD);
- eventos e não eventos, risco, diferença de risco, risk ratio e odds ratio, com IC log-Wald;
- pessoa-dias, pessoa-anos e incidência quando existe tempo observado positivo;
- PSM/IPTW experimentais e seus diagnósticos;
- status `not_computable`/`abstained` e motivo em vez de fabricar um resultado.

Células menores que o limiar configurado são suprimidas junto com métricas derivadas. Células zero
exigem correção de continuidade explícita; sem ela, RR/OR se abstêm. Cada run persiste apenas
agregados, configuração, versões dos métodos, hashes e provenance.

Isto é uma demonstração sintética, não uma análise epidemiológica validada e não suporta cuidado ao
paciente, recomendação terapêutica ou conclusão causal.
