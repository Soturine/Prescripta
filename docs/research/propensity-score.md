# Propensity Score Matching experimental

O PSM estima propensity score com regressão logística e faz nearest-neighbor matching sem reposição.
Razão, caliper e seed são explícitos. O run registra distribuição/overlap dos scores, pares,
expostos/comparadores não pareados e SMD antes/depois.

O método se abstém quando não há covariáveis, variação de tratamento, overlap ou pares dentro do
caliper. Não há escolha automática de covariáveis por IA. Matching não prova exchangeability nem
remove confusão não medida; por isso toda superfície o rotula `experimental_non_causal`.

Validação de referência independente permanece pendente (`CAUSAL-207`).
