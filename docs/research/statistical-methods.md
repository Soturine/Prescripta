# Métodos estatísticos

Todas as fórmulas são determinísticas e recebem numerador, denominador e janela explícitos.

| Medida | Definição implementada | Falha fechada |
| --- | --- | --- |
| Risco | eventos / N | N zero |
| Diferença de risco | risco exposto − risco comparador | grupo inválido/suprimido |
| RR | risco exposto / risco comparador | risco comparador zero sem correção |
| OR | (a/b) / (c/d) | célula zero sem correção |
| Incidência | eventos / pessoa-tempo | pessoa-tempo ausente ou zero |
| SMD contínuo | diferença de médias / DP combinada | variância degenerada |
| SMD categórico | diferença de proporções / DP combinada | proporção degenerada |

Os intervalos RR/OR usam aproximação log-Wald a 95%, identificada na provenance. Correção de
continuidade é opt-in e registrada. Estes intervalos não corrigem confusão, viés de seleção,
misclassification ou multiplicidade.

Os budgets atuais são 5.000 registros sintéticos por comparação e supressão padrão para `N < 5`.
Não existe inferência sobre dados reais nesta versão.

## Referências metodológicas

- Austin, *An Introduction to Propensity Score Methods*:
  https://pmc.ncbi.nlm.nih.gov/articles/PMC3144483/
- Austin, *Balance diagnostics*:
  https://pmc.ncbi.nlm.nih.gov/articles/PMC3472075/
- Hernán e Robins, *Causal Inference: What If*:
  https://www.hsph.harvard.edu/miguel-hernan/wp-content/uploads/sites/1268/2024/04/hernanrobins_WhatIf_26apr24.pdf
- scikit-learn, regressão logística:
  https://scikit-learn.org/stable/modules/linear_model.html#logistic-regression
